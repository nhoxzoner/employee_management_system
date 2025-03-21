from app.models.database_schema import Employee, Department, db
from flask_login import current_user
import datetime

class EmployeeService:
    """Service class for employee management operations."""
    
    def get_employees_by_permission(self, user):
        """Get employees based on user's permissions."""
        # Nếu không có nhân viên liên kết với người dùng, trả về danh sách trống
        if not user.employee:
            return []
        
        current_employee = user.employee
        
        # Kiểm tra vai trò của người dùng
        is_hr = any(role.role_type.value in ['hr_employee', 'hr_manager'] for role in user.roles)
        is_hr_manager = any(role.role_type.value == 'hr_manager' for role in user.roles)
        is_manager = any(role.role_type.value == 'manager' for role in user.roles)
        is_accounting = any(role.role_type.value == 'accounting' for role in user.roles)
        is_admin = any(role.role_type.value == 'admin' for role in user.roles)
        
        # Admin có thể xem tất cả nhân viên
        if is_admin:
            employees = Employee.query.all()
            return [self._serialize_employee(emp, include_salary=True) for emp in employees]
        
        # Trưởng phòng nhân sự có thể xem tất cả nhân viên với đầy đủ thông tin
        if is_hr_manager and current_employee.department.name == 'HR':
            employees = Employee.query.all()
            return [self._serialize_employee(emp, include_salary=True) for emp in employees]
        
        # Nhân viên phòng nhân sự có thể xem tất cả nhân viên trừ nhân viên cùng phòng
        if is_hr and current_employee.department.name == 'HR':
            # Lấy tất cả nhân viên không thuộc phòng HR
            employees_other_dept = Employee.query.filter(Employee.department_id != current_employee.department_id).all()
            # Lấy nhân viên cùng phòng HR (không bao gồm lương)
            employees_same_dept = Employee.query.filter_by(department_id=current_employee.department_id).all()
            
            result = [self._serialize_employee(emp, include_salary=True) for emp in employees_other_dept]
            result.extend([self._serialize_employee(emp, include_salary=False) for emp in employees_same_dept])
            return result
        
        # Nhân viên phòng kế toán có thể xem mã số, lương và mã số thuế của tất cả nhân viên
        if is_accounting and current_employee.department.name == 'Accounting':
            employees = Employee.query.all()
            return [self._serialize_employee_for_accounting(emp) for emp in employees]
        
        # Trưởng phòng có thể xem tất cả nhân viên trong phòng mình, bao gồm lương
        if is_manager:
            managed_dept_ids = [dept.id for dept in current_employee.managed_departments]
            if managed_dept_ids:
                employees = Employee.query.filter(Employee.department_id.in_(managed_dept_ids)).all()
                return [self._serialize_employee(emp, include_salary=True) for emp in employees]
        
        # Nhân viên thông thường chỉ có thể xem nhân viên cùng phòng, không bao gồm lương
        employees = Employee.query.filter_by(department_id=current_employee.department_id).all()
        return [self._serialize_employee(emp, include_salary=False) for emp in employees]
    
    def get_employee_by_id(self, employee_id):
        """Get employee by ID."""
        employee = Employee.query.get(employee_id)
        if not employee:
            return None
        
        # Kiểm tra quyền xem lương
        include_salary = self._can_view_salary(employee)
        
        return self._serialize_employee(employee, include_salary)
    
    def get_employees_by_department(self, department_id, user):
        """Get employees by department ID."""
        employees = Employee.query.filter_by(department_id=department_id).all()
        
        # Kiểm tra quyền xem lương
        if not user.employee:
            return []
        
        current_employee = user.employee
        is_hr_manager = any(role.role_type.value == 'hr_manager' for role in user.roles)
        is_manager = any(role.role_type.value == 'manager' for role in user.roles)
        is_accounting = any(role.role_type.value == 'accounting' for role in user.roles)
        is_admin = any(role.role_type.value == 'admin' for role in user.roles)
        
        # Xác định có được xem lương không
        include_salary = False
        if is_admin:
            include_salary = True
        elif is_hr_manager and current_employee.department.name == 'HR':
            include_salary = True
        elif is_accounting and current_employee.department.name == 'Accounting':
            include_salary = True
        elif is_manager:
            # Trưởng phòng chỉ xem được lương nhân viên trong phòng mình quản lý
            managed_dept_ids = [dept.id for dept in current_employee.managed_departments]
            include_salary = department_id in managed_dept_ids
        
        return [self._serialize_employee(emp, include_salary) for emp in employees]
    
    def search_employees(self, user, query='', department_id=None):
        """Search employees by query and department."""
        # Bắt đầu với truy vấn cơ bản
        employee_query = Employee.query
        
        # Lọc theo phòng ban nếu được cung cấp
        if department_id:
            employee_query = employee_query.filter_by(department_id=department_id)
        
        # Lọc theo từ khóa tìm kiếm
        if query:
            search = f"%{query}%"
            employee_query = employee_query.filter(
                db.or_(
                    Employee.full_name.ilike(search),
                    Employee.employee_code.ilike(search),
                    Employee.email.ilike(search)
                )
            )
        
        # Lấy kết quả
        employees = employee_query.all()
        
        # Áp dụng kiểm tra quyền truy cập
        result = []
        for emp in employees:
            # Kiểm tra quyền xem nhân viên
            if self._can_view_employee(user, emp):
                # Kiểm tra quyền xem lương
                include_salary = self._can_view_salary(emp)
                result.append(self._serialize_employee(emp, include_salary))
        
        return result
    
    def create_employee(self, data):
        """Create a new employee."""
        # Kiểm tra mã nhân viên và email đã tồn tại chưa
        if Employee.query.filter_by(employee_code=data.get('employee_code')).first():
            return {'error': 'Mã nhân viên đã tồn tại'}
        
        if Employee.query.filter_by(email=data.get('email')).first():
            return {'error': 'Email đã tồn tại'}
        
        if Employee.query.filter_by(tax_code=data.get('tax_code')).first():
            return {'error': 'Mã số thuế đã tồn tại'}
        
        # Kiểm tra phòng ban có tồn tại không
        department = Department.query.get(data.get('department_id'))
        if not department:
            return {'error': 'Phòng ban không tồn tại'}
        
        # Chuyển đổi ngày sinh từ chuỗi sang đối tượng date
        try:
            birth_date = datetime.datetime.strptime(data.get('birth_date'), '%Y-%m-%d').date()
        except ValueError:
            return {'error': 'Định dạng ngày sinh không hợp lệ (YYYY-MM-DD)'}
        
        # Tạo nhân viên mới
        employee = Employee(
            employee_code=data.get('employee_code'),
            full_name=data.get('full_name'),
            birth_date=birth_date,
            email=data.get('email'),
            salary=data.get('salary'),
            tax_code=data.get('tax_code'),
            department_id=data.get('department_id')
        )
        
        db.session.add(employee)
        db.session.commit()
        
        return self._serialize_employee(employee, include_salary=True)
    
    def update_employee(self, employee_id, data):
        """Update employee information."""
        employee = Employee.query.get(employee_id)
        if not employee:
            return {'error': 'Không tìm thấy nhân viên'}
        
        # Kiểm tra mã nhân viên nếu được cập nhật
        if 'employee_code' in data and data['employee_code'] != employee.employee_code:
            if Employee.query.filter_by(employee_code=data['employee_code']).first():
                return {'error': 'Mã nhân viên đã tồn tại'}
            employee.employee_code = data['employee_code']
        
        # Kiểm tra email nếu được cập nhật
        if 'email' in data and data['email'] != employee.email:
            if Employee.query.filter_by(email=data['email']).first():
                return {'error': 'Email đã tồn tại'}
            employee.email = data['email']
        
        # Kiểm tra mã số thuế nếu được cập nhật
        if 'tax_code' in data and data['tax_code'] != employee.tax_code:
            if Employee.query.filter_by(tax_code=data['tax_code']).first():
                return {'error': 'Mã số thuế đã tồn tại'}
            employee.tax_code = data['tax_code']
        
        # Cập nhật các thông tin khác
        if 'full_name' in data:
            employee.full_name = data['full_name']
        
        if 'birth_date' in data:
            try:
                birth_date = datetime.datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
                employee.birth_date = birth_date
            except ValueError:
                return {'error': 'Định dạng ngày sinh không hợp lệ (YYYY-MM-DD)'}
        
        if 'salary' in data:
            employee.salary = data['salary']
        
        if 'department_id' in data:
            department = Department.query.get(data['department_id'])
            if not department:
                return {'error': 'Phòng ban không tồn tại'}
            employee.department_id = data['department_id']
        
        db.session.commit()
        
        return self._serialize_employee(employee, include_salary=True)
    
    def delete_employee(self, employee_id):
        """Delete an employee."""
        employee = Employee.query.get(employee_id)
        if not employee:
            return {'error': 'Không tìm thấy nhân viên'}
        
        # Lưu thông tin nhân viên để trả về
        employee_info = self._serialize_employee(employee, include_salary=True)
        
        # Kiểm tra xem nhân viên có phải là trưởng phòng của bất kỳ phòng ban nào không
        managed_departments = Department.query.filter_by(manager_id=employee_id).all()
        for dept in managed_departments:
            dept.manager_id = None
        
        # Xóa nhân viên
        db.session.delete(employee)
        db.session.commit()
        
        return employee_info
    
    def _can_view_employee(self, user, employee):
        """Kiểm tra xem người dùng có quyền xem thông tin nhân viên không."""
        if not user.is_authenticated or not user.employee:
            return False
        
        current_employee = user.employee
        
        # Admin có thể xem tất cả
        if any(role.role_type.value == 'admin' for role in user.roles):
            return True
        
        # Trưởng phòng nhân sự có thể xem tất cả
        if any(role.role_type.value == 'hr_manager' for role in user.roles) and current_employee.department.name == 'HR':
            return True
        
        # Nhân viên phòng nhân sự có thể xem tất cả nhân viên
        if any(role.role_type.value == 'hr_employee' for role in user.roles) and current_employee.department.name == 'HR':
            return True
        
        # Nhân viên phòng kế toán có thể xem tất cả nhân viên (chỉ một số thông tin)
        if any(role.role_type.value == 'accounting' for role in user.roles) and current_employee.department.name == 'Accounting':
            return True
        
        # Trưởng phòng có thể xem nhân viên trong phòng mình
        if any(role.role_type.value == 'manager' for role in user.roles):
            managed_dept_ids = [dept.id for dept in current_employee.managed_departments]
            return employee.department_id in managed_dept_ids
        
        # Nhân viên thông thường chỉ có thể xem nhân viên cùng phòng
        return employee.department_id == current_employee.department_id
    
    def _can_view_salary(self, employee):
        """Kiểm tra xem người dùng hiện tại có quyền xem lương của nhân viên không."""
        if not current_user.is_authenticated or not current_user.employee:
            return False
        
        current_employee = current_user.employee
        
        # Admin có thể xem tất cả
        if any(role.role_type.value == 'admin' for role in current_user.roles):
            return True
        
        # Trưởng phòng nhân sự có thể xem tất cả
        if any(role.role_type.value == 'hr_manager' for role in current_user.roles) and current_employee.department.name == 'HR':
            return True
        
        # Nhân viên phòng nhân sự có thể xem lương của nhân viên khác phòng
        if any(role.role_type.value == 'hr_employee' for role in current_user.roles) and current_employee.department.name == 'HR':
            return employee.department_id != current_employee.department_id
        
        # Nhân viên phòng kế toán có thể xem lương của tất cả nhân viên
        if any(role.role_type.value == 'accounting' for role in current_user.roles) and current_employee.department.name == 'Accounting':
            return True
        
        # Trưởng phòng có thể xem lương của nhân viên trong phòng mình
        if any(role.role_type.value == 'manager' for role in current_user.roles):
            managed_dept_ids = [dept.id for dept in current_employee.managed_departments]
            return employee.department_id in managed_dept_ids
        
        return False
    
    def _serialize_employee(self, employee, include_salary=False):
        """Convert employee object to dictionary."""
        result = {
            'id': employee.id,
            'employee_code': employee.employee_code,
            'full_name': employee.full_name,
            'birth_date': employee.birth_date.isoformat() if employee.birth_date else None,
            'email': employee.email,
            'department_id': employee.department_id,
            'department_name': employee.department.name if employee.department else None,
            'created_at': employee.created_at.isoformat() if employee.created_at else None,
            'updated_at': employee.updated_at.isoformat() if employee.updated_at else None
        }
        
        # Chỉ bao gồm lương nếu có quyền
        if include_salary:
            result['salary'] = employee.salary
            result['tax_code'] = employee.tax_code
        
        return result
    
    def _serialize_employee_for_accounting(self, employee):
        """Serialize employee for accounting department (only code, salary, tax)."""
        return {
            'id': employee.id,
            'employee_code': employee.employee_code,
            'full_name': employee.full_name,
            'salary': employee.salary,
            'tax_code': employee.tax_code,
            'department_id': employee.department_id,
            'department_name': employee.department.name if employee.department else None
        }
