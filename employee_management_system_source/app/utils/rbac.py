from flask import request, session
from flask_login import current_user
from functools import wraps
from app.models.database_schema import User, Role, Permission, Employee, Department, RoleType

def admin_required(f):
    """Decorator để kiểm tra quyền quản trị viên."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Kiểm tra xem người dùng hiện tại có vai trò admin không
        if not any(role.role_type == RoleType.ADMIN for role in current_user.roles):
            return {'error': 'Yêu cầu quyền quản trị viên'}, 403
        return f(*args, **kwargs)
    return decorated_function

def has_permission(user, resource, action, resource_id=None):
    """
    Kiểm tra xem người dùng có quyền thực hiện hành động trên tài nguyên không.
    
    Args:
        user: Đối tượng User hiện tại
        resource: Loại tài nguyên (employee, department, etc.)
        action: Hành động (create, read, update, delete)
        resource_id: ID của tài nguyên cụ thể (nếu có)
        
    Returns:
        bool: True nếu có quyền, False nếu không
    """
    # Quản trị viên có tất cả quyền
    if any(role.role_type == RoleType.ADMIN for role in user.roles):
        return True
    
    # Kiểm tra quyền dựa trên vai trò
    for role in user.roles:
        for permission in role.permissions:
            if permission.resource == resource and permission.action == action:
                # Nếu không có resource_id, hoặc permission áp dụng cho tất cả tài nguyên
                if resource_id is None:
                    return True
                
                # Xử lý các trường hợp đặc biệt dựa trên chính sách
                if resource == 'employee':
                    return check_employee_permission(user, action, resource_id, role)
                elif resource == 'employee_salary':
                    return check_salary_permission(user, resource_id, role)
                elif resource == 'department':
                    return check_department_permission(user, action, resource_id, role)
    
    return False

def check_employee_permission(user, action, employee_id, role):
    """Kiểm tra quyền đối với nhân viên dựa trên chính sách."""
    # Lấy thông tin nhân viên cần kiểm tra
    target_employee = Employee.query.get(employee_id)
    if not target_employee:
        return False
    
    # Lấy thông tin nhân viên của người dùng hiện tại
    if not user.employee:
        return False
    
    current_employee = user.employee
    
    # Trường hợp 1: Nhân viên phòng nhân sự
    if role.role_type == RoleType.HR_EMPLOYEE:
        # Nhân viên HR có thể xem/sửa thông tin của tất cả nhân viên trừ nhân viên cùng phòng
        if current_employee.department.name == 'HR':
            # Không được phép nếu nhân viên đích cũng thuộc phòng HR
            if target_employee.department_id == current_employee.department_id:
                # Nhân viên HR chỉ được xem (không sửa) thông tin nhân viên cùng phòng
                return action == 'read'
            # Được phép với nhân viên khác phòng
            return True
    
    # Trường hợp 2: Trưởng phòng nhân sự
    elif role.role_type == RoleType.HR_MANAGER:
        # Trưởng phòng HR có thể xem/sửa thông tin của tất cả nhân viên
        if current_employee.department.name == 'HR':
            return True
    
    # Trường hợp 3: Nhân viên phòng kế toán
    elif role.role_type == RoleType.ACCOUNTING:
        # Nhân viên kế toán có thể xem mã số, lương và mã số thuế của tất cả nhân viên
        if current_employee.department.name == 'Accounting':
            # Chỉ cho phép xem, không cho phép sửa
            if action == 'read':
                return True
            return False
    
    # Trường hợp 4: Trưởng phòng (không phải HR)
    elif role.role_type == RoleType.MANAGER:
        # Trưởng phòng có thể xem thông tin của nhân viên trong phòng mình
        if current_employee.managed_departments:
            for dept in current_employee.managed_departments:
                if target_employee.department_id == dept.id:
                    # Chỉ cho phép xem, không cho phép sửa
                    return action == 'read'
    
    # Trường hợp 5: Nhân viên thông thường
    elif role.role_type == RoleType.EMPLOYEE:
        # Nhân viên chỉ được xem thông tin của nhân viên cùng phòng
        if current_employee.department_id == target_employee.department_id:
            # Chỉ cho phép xem, không cho phép sửa
            return action == 'read'
    
    return False

def check_salary_permission(user, employee_id, role):
    """Kiểm tra quyền xem thông tin lương."""
    # Lấy thông tin nhân viên cần kiểm tra
    target_employee = Employee.query.get(employee_id)
    if not target_employee:
        return False
    
    # Lấy thông tin nhân viên của người dùng hiện tại
    if not user.employee:
        return False
    
    current_employee = user.employee
    
    # Trường hợp 1: Quản trị viên có thể xem tất cả
    if role.role_type == RoleType.ADMIN:
        return True
    
    # Trường hợp 2: Trưởng phòng nhân sự có thể xem tất cả
    if role.role_type == RoleType.HR_MANAGER and current_employee.department.name == 'HR':
        return True
    
    # Trường hợp 3: Nhân viên phòng nhân sự có thể xem lương của nhân viên khác phòng
    if role.role_type == RoleType.HR_EMPLOYEE and current_employee.department.name == 'HR':
        # Không được xem lương của nhân viên cùng phòng
        if target_employee.department_id != current_employee.department_id:
            return True
    
    # Trường hợp 4: Nhân viên phòng kế toán có thể xem lương của tất cả nhân viên
    if role.role_type == RoleType.ACCOUNTING and current_employee.department.name == 'Accounting':
        return True
    
    # Trường hợp 5: Trưởng phòng có thể xem lương của nhân viên trong phòng mình
    if role.role_type == RoleType.MANAGER:
        if current_employee.managed_departments:
            for dept in current_employee.managed_departments:
                if target_employee.department_id == dept.id:
                    return True
    
    return False

def check_department_permission(user, action, department_id, role):
    """Kiểm tra quyền đối với phòng ban."""
    # Lấy thông tin phòng ban
    department = Department.query.get(department_id)
    if not department:
        return False
    
    # Lấy thông tin nhân viên của người dùng hiện tại
    if not user.employee:
        return False
    
    current_employee = user.employee
    
    # Quản trị viên có tất cả quyền
    if role.role_type == RoleType.ADMIN:
        return True
    
    # Trưởng phòng có quyền xem thông tin phòng ban của mình
    if role.role_type == RoleType.MANAGER:
        if current_employee.managed_departments:
            for dept in current_employee.managed_departments:
                if department_id == dept.id:
                    return action == 'read'
    
    # Nhân viên có quyền xem thông tin phòng ban của mình
    if current_employee.department_id == department_id:
        return action == 'read'
    
    # Nhân viên HR có quyền xem thông tin tất cả phòng ban
    if (role.role_type == RoleType.HR_EMPLOYEE or role.role_type == RoleType.HR_MANAGER) and current_employee.department.name == 'HR':
        return action == 'read'
    
    return False
