from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.employee import Employee
from ..schemas.employee import EmployeeCreate, EmployeeOut, EmployeeUpdate

router = APIRouter(prefix="/api/employee", tags=["员工管理"])


@router.get("/list", summary="分页查询员工列表")
def list_employees(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页条数"),
    name: str = Query("", description="姓名（模糊查询）"),
    department: str = Query("", description="部门（精准查询）"),
    db: Session = Depends(get_db),
):
    query = db.query(Employee)
    if name:
        query = query.filter(Employee.name.like(f"%{name}%"))
    if department:
        query = query.filter(Employee.department == department)
    total = query.count()
    items = query.order_by(Employee.id.desc()).offset((page - 1) * size).limit(size).all()
    return {"total": total, "items": [EmployeeOut.model_validate(item) for item in items]}


@router.get("/{emp_id}", summary="查询单个员工")
def get_employee(emp_id: int, db: Session = Depends(get_db)):
    emp = db.get(Employee, emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="员工不存在")
    return EmployeeOut.model_validate(emp)


@router.post("", summary="新增员工")
def create_employee(data: EmployeeCreate, db: Session = Depends(get_db)):
    emp = Employee(**data.model_dump())
    db.add(emp)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="工号已存在，请更换后重试")
    db.refresh(emp)
    return EmployeeOut.model_validate(emp)


@router.put("/{emp_id}", summary="修改员工")
def update_employee(emp_id: int, data: EmployeeUpdate, db: Session = Depends(get_db)):
    emp = db.get(Employee, emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="员工不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(emp, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="工号已存在，请更换后重试")
    db.refresh(emp)
    return EmployeeOut.model_validate(emp)


@router.delete("/{emp_id}", summary="删除员工")
def delete_employee(emp_id: int, db: Session = Depends(get_db)):
    emp = db.get(Employee, emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="员工不存在")
    db.delete(emp)
    db.commit()
    return {"message": "删除成功"}
