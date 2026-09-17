from datetime import date

from .database import SessionLocal
from .models import Asset, Employee

DEMO_EMPLOYEES = [
    dict(emp_no="E001", name="张伟", gender="男", department="技术部", position="后端工程师",
         phone="13800000001", email="zhangwei@example.com", hire_date=date(2022, 3, 1), status="在职"),
    dict(emp_no="E002", name="李娜", gender="女", department="人事部", position="HR主管",
         phone="13800000002", email="lina@example.com", hire_date=date(2021, 7, 15), status="在职"),
    dict(emp_no="E003", name="王强", gender="男", department="技术部", position="前端工程师",
         phone="13800000003", email="wangqiang@example.com", hire_date=date(2023, 2, 20), status="在职"),
    dict(emp_no="E004", name="刘洋", gender="男", department="财务部", position="会计",
         phone="13800000004", email="liuyang@example.com", hire_date=date(2020, 11, 5), status="在职"),
    dict(emp_no="E005", name="陈静", gender="女", department="市场部", position="市场专员",
         phone="13800000005", email="chenjing@example.com", hire_date=date(2024, 6, 1), status="在职"),
]

DEMO_ASSETS = [
    dict(asset_no="ZC20260001", name="联想笔记本", category="电脑设备", brand="Lenovo", model="ThinkPad X1",
         price=8999.00, purchase_date=date(2023, 5, 10), status="空闲", user_id=None, remark="技术部备用机"),
    dict(asset_no="ZC20260002", name="戴尔显示器", category="电脑设备", brand="Dell", model="U2723QE",
         price=3299.00, purchase_date=date(2023, 6, 18), status="已领用", user_id=1, remark="张伟领用"),
    dict(asset_no="ZC20260003", name="惠普打印机", category="办公用品", brand="HP", model="M479fdw",
         price=4599.00, purchase_date=date(2022, 9, 1), status="维修", user_id=None, remark="进纸器故障送修"),
    dict(asset_no="ZC20260004", name="群晖NAS服务器", category="网络设备", brand="Synology", model="DS1823xs+",
         price=12999.00, purchase_date=date(2023, 1, 12), status="空闲", user_id=None, remark="存放项目资料"),
    dict(asset_no="ZC20260005", name="人体工学办公椅", category="办公用品", brand="ErgoPro", model="EP-2023",
         price=1299.00, purchase_date=date(2023, 3, 25), status="已领用", user_id=4, remark="刘洋领用"),
    dict(asset_no="ZC20260006", name="爱普生投影仪", category="办公用品", brand="Epson", model="CB-L630U",
         price=18999.00, purchase_date=date(2020, 4, 8), status="报废", user_id=None, remark="已到报废年限"),
]


def init_demo_data():
    """首次启动时写入演示数据，已有数据则跳过"""
    db = SessionLocal()
    try:
        if db.query(Employee).count() == 0:
            db.add_all([Employee(**item) for item in DEMO_EMPLOYEES])
        if db.query(Asset).count() == 0:
            db.add_all([Asset(**item) for item in DEMO_ASSETS])
        db.commit()
    finally:
        db.close()
