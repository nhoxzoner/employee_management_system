from app.models.database_schema import db, User, Role, Permission, Employee, Department, AuditLog, RoleType, ActionType
from werkzeug.security import generate_password_hash
from datetime import datetime, date
import os

def init_db():
    """Khởi tạo cơ sở dữ liệu và tạo các bảng."""
    db.create_all()
    
    # Kiểm tra xem đã có dữ liệu trong cơ sở dữ liệu chưa
    if User.query.first() is None:
        create_initial_data()

def create_initial_data():
    """Tạo dữ liệu ban đầu cho cơ sở dữ liệu."""
    # Tạo các quyền
    permissions = create_permissions()
    
    # Tạo các vai trò
    roles = create_roles(permissions)
    
    # Tạo các phòng ban
    departments = create_departments()
    
    # Tạo nhân viên
    employees = create_employees(departments)
    
    # Tạo người dùng
    create_users(employees, roles)
    
    # Thiết lập trưởng phòng cho các phòng ban
    set_department_managers(departments, employees)
    
    db.session.commit()

def create_permissions():
    """Tạo các quyền cơ bản."""
    permissions = {}
    
    # Quyền đối với người dùng
    permissions['user_create'] = Permission(name='user_create', description='Tạo người dùng', resource='user', action='create')
    permissions['user_read'] = Permission(name='user_read', description='Xem người dùng', resource='user', action='read')
    permissions['user_update'] = Permission(name='user_update', description='Cập nhật người dùng', resource='user', action='update')
    permissions['user_delete'] = Permission(name='user_delete', description='Xóa người dùng', resource='user', action='delete')
    
    # Quyền đối với vai trò
    permissions['role_create'] = Permission(name='role_create', description='Tạo vai trò', resource='role', action='create')
    permissions['role_read'] = Permission(name='role_read', description='Xem vai trò', resource='role', action='read')
    permissions['role_update'] = Permission(name='role_update', description='Cập nhật vai trò', resource='role', action='update')
    permissions['role_delete'] = Permission(name='role_delete', description='Xóa vai trò', resource='role', action='delete')
    
    # Quyền đối với nhân viên
    permissions['employee_create'] = Permission(name='employee_create', description='Tạo nhân viên', resource='employee', action='create')
    permissions['employee_read'] = Permission(name='employee_read', description='Xem nhân viên', resource='employee', action='read')
    permissions['employee_update'] = Permission(name='employee_update', description='Cập nhật nhân viên', resource='employee', action='update')
    permissions['employee_delete'] = Permission(name='employee_delete', description='Xóa nhân viên', resource='employee', action='delete')
    
    # Quyền đối với lương nhân viên
    permissions['employee_salary_read'] = Permission(name='employee_salary_read', description='Xem lương nhân viên', resource='employee_salary', action='read')
    
    # Quyền đối với phòng ban
    permissions['department_create'] = Permission(name='department_create', description='Tạo phòng ban', resource='department', action='create')
    permissions['department_read'] = Permission(name='department_read', description='Xem phòng ban', resource='department', action='read')
    permissions['department_update'] = Permission(name='department_update', description='Cập nhật phòng ban', resource='department', action='update')
    permissions['department_delete'] = Permission(name='department_delete', description='Xóa phòng ban', resource='department', action='delete')
    
    # Thêm tất cả quyền vào cơ sở dữ liệu
    for permission in permissions.values():
        db.session.add(permission)
    
    db.session.commit()
    return permissions

def create_roles(permissions):
    """Tạo các vai trò với quyền tương ứng."""
    roles = {}
    
    # Vai trò Admin - có tất cả quyền
    roles['admin'] = Role(name='Admin', description='Quản trị viên hệ thống', role_type=RoleType.ADMIN)
    roles['admin'].permissions = list(permissions.values())
    
    # Vai trò nhân viên thông thường
    roles['employee'] = Role(name='Employee', description='Nhân viên thông thường', role_type=RoleType.EMPLOYEE)
    roles['employee'].permissions = [
        permissions['employee_read'],
        permissions['department_read']
    ]
    
    # Vai trò trưởng phòng
    roles['manager'] = Role(name='Manager', description='Trưởng phòng', role_type=RoleType.MANAGER)
    roles['manager'].permissions = [
        permissions['employee_read'],
        permissions['employee_salary_read'],
        permissions['department_read']
    ]
    
    # Vai trò nhân viên phòng nhân sự
    roles['hr_employee'] = Role(name='HR Employee', description='Nhân viên phòng nhân sự', role_type=RoleType.HR_EMPLOYEE)
    roles['hr_employee'].permissions = [
        permissions['employee_read'],
        permissions['employee_update'],
        permissions['employee_create'],
        permissions['employee_delete'],
        permissions['department_read']
    ]
    
    # Vai trò trưởng phòng nhân sự
    roles['hr_manager'] = Role(name='HR Manager', description='Trưởng phòng nhân sự', role_type=RoleType.HR_MANAGER)
    roles['hr_manager'].permissions = [
        permissions['employee_read'],
        permissions['employee_update'],
        permissions['employee_create'],
        permissions['employee_delete'],
        permissions['employee_salary_read'],
        permissions['department_read'],
        permissions['user_read'],
        permissions['user_update']
    ]
    
    # Vai trò nhân viên phòng kế toán
    roles['accounting'] = Role(name='Accounting', description='Nhân viên phòng kế toán', role_type=RoleType.ACCOUNTING)
    roles['accounting'].permissions = [
        permissions['employee_read'],
        permissions['employee_salary_read'],
        permissions['department_read']
    ]
    
    # Thêm tất cả vai trò vào cơ sở dữ liệu
    for role in roles.values():
        db.session.add(role)
    
    db.session.commit()
    return roles

def create_departments():
    """Tạo các phòng ban cơ bản."""
    departments = {}
    
    departments['hr'] = Department(name='HR', description='Phòng Nhân sự')
    departments['accounting'] = Department(name='Accounting', description='Phòng Kế toán')
    departments['it'] = Department(name='IT', description='Phòng Công nghệ thông tin')
    departments['sales'] = Department(name='Sales', description='Phòng Kinh doanh')
    departments['marketing'] = Department(name='Marketing', description='Phòng Marketing')
    
    # Thêm tất cả phòng ban vào cơ sở dữ liệu
    for department in departments.values():
        db.session.add(department)
    
    db.session.commit()
    return departments

def create_employees(departments):
    """Tạo nhân viên cho các phòng ban."""
    employees = {}
    
    # Nhân viên phòng HR
    employees['hr_manager'] = Employee(
        employee_code='HR001',
        full_name='Nguyễn Văn Quản Lý HR',
        birth_date=date(1980, 1, 15),
        email='hr_manager@company.com',
        salary=25000000,
        tax_code='TAX001',
        department=departments['hr']
    )
    
    employees['hr_employee1'] = Employee(
        employee_code='HR002',
        full_name='Trần Thị Nhân Sự 1',
        birth_date=date(1985, 5, 20),
        email='hr_employee1@company.com',
        salary=15000000,
        tax_code='TAX002',
        department=departments['hr']
    )
    
    employees['hr_employee2'] = Employee(
        employee_code='HR003',
        full_name='Lê Văn Nhân Sự 2',
        birth_date=date(1988, 8, 10),
        email='hr_employee2@company.com',
        salary=14000000,
        tax_code='TAX003',
        department=departments['hr']
    )
    
    # Nhân viên phòng Kế toán
    employees['accounting_manager'] = Employee(
        employee_code='ACC001',
        full_name='Phạm Thị Quản Lý Kế Toán',
        birth_date=date(1982, 3, 25),
        email='accounting_manager@company.com',
        salary=23000000,
        tax_code='TAX004',
        department=departments['accounting']
    )
    
    employees['accounting_employee1'] = Employee(
        employee_code='ACC002',
        full_name='Hoàng Văn Kế Toán 1',
        birth_date=date(1987, 7, 12),
        email='accounting_employee1@company.com',
        salary=16000000,
        tax_code='TAX005',
        department=departments['accounting']
    )
    
    # Nhân viên phòng IT
    employees['it_manager'] = Employee(
        employee_code='IT001',
        full_name='Đỗ Văn Quản Lý IT',
        birth_date=date(1983, 9, 5),
        email='it_manager@company.com',
        salary=28000000,
        tax_code='TAX006',
        department=departments['it']
    )
    
    employees['it_employee1'] = Employee(
        employee_code='IT002',
        full_name='Ngô Thị IT 1',
        birth_date=date(1990, 11, 18),
        email='it_employee1@company.com',
        salary=20000000,
        tax_code='TAX007',
        department=departments['it']
    )
    
    employees['it_employee2'] = Employee(
        employee_code='IT003',
        full_name='Vũ Văn IT 2',
        birth_date=date(1992, 2, 28),
        email='it_employee2@company.com',
        salary=18000000,
        tax_code='TAX008',
        department=departments['it']
    )
    
    # Nhân viên phòng Sales
    employees['sales_manager'] = Employee(
        employee_code='SL001',
        full_name='Lý Thị Quản Lý Sales',
        birth_date=date(1984, 4, 15),
        email='sales_manager@company.com',
        salary=26000000,
        tax_code='TAX009',
        department=departments['sales']
    )
    
    employees['sales_employee1'] = Employee(
        employee_code='SL002',
        full_name='Đinh Văn Sales 1',
        birth_date=date(1989, 6, 22),
        email='sales_employee1@company.com',
        salary=17000000,
        tax_code='TAX010',
        department=departments['sales']
    )
    
    # Nhân viên phòng Marketing
    employees['marketing_manager'] = Employee(
        employee_code='MK001',
        full_name='Trịnh Văn Quản Lý Marketing',
        birth_date=date(1985, 10, 8),
        email='marketing_manager@company.com',
        salary=24000000,
        tax_code='TAX011',
        department=departments['marketing']
    )
    
    employees['marketing_employee1'] = Employee(
        employee_code='MK002',
        full_name='Mai Thị Marketing 1',
        birth_date=date(1991, 12, 30),
        email='marketing_employee1@company.com',
        salary=16500000,
        tax_code='TAX012',
        department=departments['marketing']
    )
    
    # Thêm tất cả nhân viên vào cơ sở dữ liệu
    for employee in employees.values():
        db.session.add(employee)
    
    db.session.commit()
    return employees

def create_users(employees, roles):
    """Tạo người dùng cho nhân viên."""
    # Admin user (không gắn với nhân viên cụ thể)
    admin_user = User(
        username='admin',
        email='admin@company.com',
        password_hash=generate_password_hash('admin123'),
        is_active=True
    )
    admin_user.roles.append(roles['admin'])
    db.session.add(admin_user)
    
    # Người dùng cho nhân viên HR
    hr_manager_user = User(
        username='hr_manager',
        email=employees['hr_manager'].email,
        password_hash=generate_password_hash('password'),
        is_active=True,
        employee=employees['hr_manager']
    )
    hr_manager_user.roles.append(roles['hr_manager'])
    db.session.add(hr_manager_user)
    
    hr_employee1_user = User(
        username='hr_employee1',
        email=employees['hr_employee1'].email,
        password_hash=generate_password_hash('password'),
        is_active=True,
        employee=employees['hr_employee1']
    )
    hr_employee1_user.roles.append(roles['hr_employee'])
    db.session.add(hr_employee1_user)
    
    hr_employee2_user = User(
        username='hr_employee2',
        email=employees['hr_employee2'].email,
        password_hash=generate_password_hash('password'),
        is_active=True,
        employee=employees['hr_employee2']
    )
    hr_employee2_user.roles.append(roles['hr_employee'])
    db.session.add(hr_employee2_user)
    
    # Người dùng cho nhân viên Kế toán
    accounting_manager_user = User(
        username='accounting_manager',
        email=employees['accounting_manager'].email,
        password_hash=generate_password_hash('password'),
        is_active=True,
        employee=employees['accounting_manager']
    )
    accounting_manager_user.roles.append(roles['manager'])
    accounting_manager_user.roles.append(roles['accounting'])
    db.session.add(accounting_manager_user)
    
    accounting_employee1_user = User(
        username='accounting_employee1',
        email=employees['accounting_employee1'].email,
        password_hash=generate_password_hash('password'),
        is_active=True,
        employee=employees['accounting_employee1']
    )
    accounting_employee1_user.roles.append(roles['accounting'])
    db.session.add(accounting_employee1_user)
    
    # Người dùng cho nhân viên IT
    it_manager_user = User(
        username='it_manager',
        email=employees['it_manager'].email,
        password_hash=generate_password_hash('password'),
        is_active=True,
        employee=employees['it_manager']
    )
    it_manager_user.roles.append(roles['manager'])
    db.session.add(it_manager_user)
    
    it_employee1_user = User(
        username='it_employee1',
        email=employees['it_employee1'].email,
        password_hash=generate_password_hash('password'),
        is_active=True,
        employee=employees['it_employee1']
    )
    it_employee1_user.roles.append(roles['employee'])
    db.session.add(it_employee1_user)
    
    it_employee2_user = User(
        username='it_employee2',
        email=employees['it_employee2'].email,
        password_hash=generate_password_hash('password'),
        is_active=True,
        employee=employees['it_employee2']
    )
    it_employee2_user.roles.append(roles['employee'])
    db.session.add(it_employee2_user)
    
    # Người dùng cho nhân viên Sales
    sales_manager_user = User(
        username='sales_manager',
        email=employees['sales_manager'].email,
        password_hash=generate_password_hash('password'),
        is_active=True,
        employee=employees['sales_manager']
    )
    sales_manager_user.roles.append(roles['manager'])
    db.session.add(sales_manager_user)
    
    sales_employee1_user = User(
        username='sales_employee1',
        email=employees['sales_employee1'].email,
        password_hash=generate_password_hash('password'),
        is_active=True,
        employee=employees['sales_employee1']
    )
    sales_employee1_user.roles.append(roles['employee'])
    db.session.add(sales_employee1_user)
    
    # Người dùng cho nhân viên Marketing
    marketing_manager_user = User(
        username='marketing_manager',
        email=employees['marketing_manager'].email,
        password_hash=generate_password_hash('password'),
        is_active=True,
        employee=employees['marketing_manager']
    )
    marketing_manager_user.roles.append(roles['manager'])
    db.session.add(marketing_manager_user)
    
    marketing_employee1_user = User(
        username='marketing_employee1',
        email=employees['marketing_employee1'].email,
        password_hash=generate_password_hash('password'),
        is_active=True,
        employee=employees['marketing_employee1']
    )
    marketing_employee1_user.roles.append(roles['employee'])
    db.session.add(marketing_employee1_user)
    
    db.session.commit()

def set_department_managers(departments, employees):
    """Thiết lập trưởng phòng cho các phòng ban."""
    departments['hr'].manager = employees['hr_manager']
    departments['accounting'].manager = employees['accounting_manager']
    departments['it'].manager = employees['it_manager']
    departments['sales'].manager = employees['sales_manager']
    departments['marketing'].manager = employees['marketing_manager']
    
    db.session.commit()
