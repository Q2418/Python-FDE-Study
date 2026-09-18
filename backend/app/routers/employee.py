from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, load_only

from ..core.deps import get_current_user, require_admin
from ..core.response import success
from ..database import get_db
from ..models.employee import Employee
from ..models.user import User
from ..schemas.employee import EmployeeCreate, EmployeeListOut, EmployeeOut, EmployeeUpdate

router = APIRouter(
    prefix="/api/employee",
    tags=["员工管理"],
    dependencies=[Depends(get_current_user)],
)

LIST_FIELDS = (
    Employee.id,
    Employee.emp_no,
    Employee.name,
    Employee.gender,
    Employee.department,
    Employee.position,
    Employee.phone,
    Employee.email,
    Employee.hire_date,
    Employee.status,
)


@router.get("/list", summary="分页查询员工列表")
def list_employees(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页条数"),
    name: str = Query("", description="姓名（模糊查询）"),
    department: str = Query("", description="部门（精准查询）"),
    db: Session = Depends(get_db),
):
    query = db.query(Employee).options(load_only(*LIST_FIELDS))
    if name:
        query = query.filter(Employee.name.like(f"%{name}%"))
    if department:
        query = query.filter(Employee.department == department)
    total = query.count()
    items = query.order_by(Employee.id.desc()).offset((page - 1) * size).limit(size).all()
    return success({"total": total, "items": [EmployeeListOut.model_validate(item) for item in items]})


@router.get("/{emp_id}", summary="查询单个员工")
def get_employee(emp_id: int, db: Session = Depends(get_db)):
    emp = db.get(Employee, emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="员工不存在")
    return success(EmployeeOut.model_validate(emp))


@router.post("", summary="新增员工")
def create_employee(
    data: EmployeeCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    if db.query(Employee.id).filter(Employee.emp_no == data.emp_no).first():
        raise HTTPException(status_code=400, detail="工号已存在，请更换后重试")
    emp = Employee(**data.model_dump())
    db.add(emp)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="工号已存在，请更换后重试")
    db.refresh(emp)
    return success(EmployeeOut.model_validate(emp), msg="新增成功")


@router.put("/{emp_id}", summary="修改员工")
def update_employee(
    emp_id: int,
    data: EmployeeUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    emp = db.get(Employee, emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="员工不存在")
    update_data = data.model_dump(exclude_unset=True)
    new_emp_no = update_data.get("emp_no")
    if new_emp_no and new_emp_no != emp.emp_no:
        if db.query(Employee.id).filter(Employee.emp_no == new_emp_no, Employee.id != emp_id).first():
            raise HTTPException(status_code=400, detail="工号已存在，请更换后重试")
    for key, value in update_data.items():
        setattr(emp, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="工号已存在，请更换后重试")
    db.refresh(emp)
    return success(EmployeeOut.model_validate(emp), msg="修改成功")


@router.delete("/{emp_id}", summary="删除员工")
def delete_employee(
    emp_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    emp = db.get(Employee, emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="员工不存在")
    db.delete(emp)
    db.commit()
    return success(msg="删除成功")
