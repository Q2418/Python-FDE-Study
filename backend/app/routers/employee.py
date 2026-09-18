import io
import logging
import uuid
from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from openpyxl import Workbook
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, load_only

from ..config import ALLOWED_UPLOAD_EXTENSIONS, MAX_UPLOAD_SIZE, UPLOAD_DIR
from ..core.deps import get_current_user, require_admin
from ..core.logger import log_operation
from ..core.response import success
from ..database import get_db
from ..models.employee import Employee
from ..models.user import User
from ..schemas.employee import EmployeeCreate, EmployeeListOut, EmployeeOut, EmployeeUpdate

logger = logging.getLogger("asset_admin")

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
    Employee.attachment_name,
)

SORT_FIELDS = {
    "id": Employee.id,
    "emp_no": Employee.emp_no,
    "name": Employee.name,
    "hire_date": Employee.hire_date,
    "create_time": Employee.create_time,
}

EXPORT_HEADERS = ["工号", "姓名", "性别", "部门", "职位", "手机号", "邮箱", "入职日期", "状态", "附件"]


def build_employee_query(
    db: Session,
    name: str = "",
    department: str = "",
    status: str = "",
    hire_date_start: date = None,
    hire_date_end: date = None,
):
    query = db.query(Employee)
    if name:
        query = query.filter(Employee.name.like(f"%{name}%"))
    if department:
        query = query.filter(Employee.department == department)
    if status:
        query = query.filter(Employee.status == status)
    if hire_date_start:
        query = query.filter(Employee.hire_date >= hire_date_start)
    if hire_date_end:
        query = query.filter(Employee.hire_date <= hire_date_end)
    return query


@router.get("/list", summary="分页查询员工列表（多条件 + 排序）")
def list_employees(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页条数"),
    name: str = Query("", description="姓名（模糊查询）"),
    department: str = Query("", description="部门（精准查询）"),
    status: str = Query("", description="状态：在职/离职"),
    hire_date_start: date = Query(None, description="入职日期起"),
    hire_date_end: date = Query(None, description="入职日期止"),
    sort_by: str = Query("id", description="排序字段：id/emp_no/name/hire_date/create_time"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="排序方式：asc/desc"),
    db: Session = Depends(get_db),
):
    query = build_employee_query(db, name, department, status, hire_date_start, hire_date_end).options(
        load_only(*LIST_FIELDS)
    )
    sort_column = SORT_FIELDS.get(sort_by, Employee.id)
    order_clause = sort_column.asc() if sort_order == "asc" else sort_column.desc()
    total = query.count()
    items = query.order_by(order_clause).offset((page - 1) * size).limit(size).all()
    return success({"total": total, "items": [EmployeeListOut.model_validate(item) for item in items]})


@router.get("/export", summary="导出员工 Excel（沿用当前筛选条件）")
def export_employees(
    name: str = Query("", description="姓名（模糊查询）"),
    department: str = Query("", description="部门（精准查询）"),
    status: str = Query("", description="状态：在职/离职"),
    hire_date_start: date = Query(None, description="入职日期起"),
    hire_date_end: date = Query(None, description="入职日期止"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = (
        build_employee_query(db, name, department, status, hire_date_start, hire_date_end)
        .order_by(Employee.id.desc())
        .all()
    )
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "员工数据"
    sheet.append(EXPORT_HEADERS)
    for row in rows:
        sheet.append(
            [
                row.emp_no,
                row.name,
                row.gender,
                row.department,
                row.position,
                row.phone,
                row.email,
                row.hire_date.isoformat() if row.hire_date else "",
                row.status,
                row.attachment_name or "",
            ]
        )
    widths = [10, 12, 8, 12, 16, 15, 26, 13, 10, 22]
    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[sheet.cell(row=1, column=index).column_letter].width = width
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    filename = f"员工数据_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    log_operation(user, "导出员工Excel", f"共 {len(rows)} 条")
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


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
    admin: User = Depends(require_admin),
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
    log_operation(admin, "新增员工", f"{emp.emp_no} {emp.name}")
    return success(EmployeeOut.model_validate(emp), msg="新增成功")


@router.put("/{emp_id}", summary="修改员工")
def update_employee(
    emp_id: int,
    data: EmployeeUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
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
    log_operation(admin, "修改员工", f"{emp.emp_no} {emp.name} 字段：{'、'.join(update_data.keys())}")
    return success(EmployeeOut.model_validate(emp), msg="修改成功")


@router.delete("/{emp_id}", summary="删除员工")
def delete_employee(
    emp_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    emp = db.get(Employee, emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="员工不存在")
    if emp.attachment_path:
        try:
            Path(emp.attachment_path).unlink(missing_ok=True)
        except OSError:
            logger.warning("删除员工附件文件失败: %s", emp.attachment_path)
    db.delete(emp)
    db.commit()
    log_operation(admin, "删除员工", f"{emp.emp_no} {emp.name}")
    return success(msg="删除成功")


@router.post("/{emp_id}/attachment", summary="上传员工附件")
async def upload_attachment(
    emp_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    emp = db.get(Employee, emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="员工不存在")
    filename = file.filename or "未命名文件"
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        allowed = "、".join(sorted(ALLOWED_UPLOAD_EXTENSIONS))
        raise HTTPException(status_code=400, detail=f"不支持的文件类型 {extension or '（无扩展名）'}，仅支持：{allowed}")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="文件内容为空")
    if len(data) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过 5MB")
    target_dir = UPLOAD_DIR / "employee"
    target_dir.mkdir(parents=True, exist_ok=True)
    if emp.attachment_path:
        try:
            Path(emp.attachment_path).unlink(missing_ok=True)
        except OSError:
            logger.warning("替换附件时删除旧文件失败: %s", emp.attachment_path)
    stored_path = target_dir / f"{uuid.uuid4().hex}{extension}"
    stored_path.write_bytes(data)
    emp.attachment_path = str(stored_path)
    emp.attachment_name = filename
    db.commit()
    db.refresh(emp)
    log_operation(admin, "上传员工附件", f"{emp.name} - {filename}（{len(data)} 字节）")
    return success(EmployeeOut.model_validate(emp), msg="附件上传成功")


@router.get("/{emp_id}/attachment", summary="下载员工附件")
def download_attachment(emp_id: int, db: Session = Depends(get_db)):
    emp = db.get(Employee, emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="员工不存在")
    if not emp.attachment_path or not Path(emp.attachment_path).exists():
        raise HTTPException(status_code=404, detail="该员工没有附件")
    filename = emp.attachment_name or Path(emp.attachment_path).name
    return FileResponse(
        emp.attachment_path,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.delete("/{emp_id}/attachment", summary="删除员工附件")
def delete_attachment(
    emp_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    emp = db.get(Employee, emp_id)
    if not emp:
        raise HTTPException(status_code=404, detail="员工不存在")
    if not emp.attachment_path:
        raise HTTPException(status_code=400, detail="该员工没有附件")
    try:
        Path(emp.attachment_path).unlink(missing_ok=True)
    except OSError:
        logger.warning("删除附件文件失败: %s", emp.attachment_path)
    old_name = emp.attachment_name
    emp.attachment_path = None
    emp.attachment_name = None
    db.commit()
    log_operation(admin, "删除员工附件", f"{emp.name} - {old_name}")
    return success(msg="附件已删除")
