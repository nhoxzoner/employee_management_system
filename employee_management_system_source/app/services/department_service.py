from app.models.database_schema import Department, Employee, db
from flask_login import current_user

class DepartmentService:
    """Service class for department management operations."""
    
    def get_all_departments(self):
        """Get all departments."""
        departments = Department.query.all()
        return [self._serialize_department(dept) for dept in departments]
    
    def get_department_by_id(self, department_id):
        """Get department by ID."""
        department = Department.query.get(department_id)
        if not department:
            return None
        return self._serialize_department(department)
    
    def create_department(self, data):
        """Create a new department."""
        # Check if department name already exists
        if Department.query.filter_by(name=data.get('name')).first():
            return {'error': 'Tên phòng ban đã tồn tại'}
        
        # Create new department
        department = Department(
            name=data.get('name'),
            description=data.get('description')
        )
        
        # Set manager if provided
        if 'manager_id' in data and data['manager_id']:
            employee = Employee.query.get(data['manager_id'])
            if not employee:
                return {'error': 'Không tìm thấy nhân viên để thiết lập làm trưởng phòng'}
            department.manager_id = data['manager_id']
        
        db.session.add(department)
        db.session.commit()
        
        return self._serialize_department(department)
    
    def update_department(self, department_id, data):
        """Update department information."""
        department = Department.query.get(department_id)
        if not department:
            return {'error': 'Không tìm thấy phòng ban'}
        
        # Update name if provided and not already taken
        if 'name' in data and data['name'] != department.name:
            if Department.query.filter_by(name=data['name']).first():
                return {'error': 'Tên phòng ban đã tồn tại'}
            department.name = data['name']
        
        # Update description if provided
        if 'description' in data:
            department.description = data['description']
        
        # Update manager if provided
        if 'manager_id' in data:
            if data['manager_id'] is None:
                department.manager_id = None
            else:
                employee = Employee.query.get(data['manager_id'])
                if not employee:
                    return {'error': 'Không tìm thấy nhân viên để thiết lập làm trưởng phòng'}
                
                # Kiểm tra nhân viên có thuộc phòng ban này không
                if employee.department_id != department_id:
                    return {'error': 'Nhân viên phải thuộc phòng ban này để có thể trở thành trưởng phòng'}
                
                department.manager_id = data['manager_id']
        
        db.session.commit()
        
        return self._serialize_department(department)
    
    def delete_department(self, department_id):
        """Delete a department."""
        department = Department.query.get(department_id)
        if not department:
            return {'error': 'Không tìm thấy phòng ban'}
        
        # Check if department has employees
        if department.employees:
            return {'error': 'Không thể xóa phòng ban có nhân viên. Vui lòng chuyển nhân viên sang phòng ban khác trước.'}
        
        # Store department info for return
        department_info = self._serialize_department(department)
        
        db.session.delete(department)
        db.session.commit()
        
        return department_info
    
    def set_department_manager(self, department_id, employee_id):
        """Set department manager."""
        department = Department.query.get(department_id)
        if not department:
            return {'error': 'Không tìm thấy phòng ban'}
        
        if employee_id is None:
            # Xóa trưởng phòng
            department.manager_id = None
            db.session.commit()
            return self._serialize_department(department)
        
        employee = Employee.query.get(employee_id)
        if not employee:
            return {'error': 'Không tìm thấy nhân viên'}
        
        # Check if employee belongs to the department
        if employee.department_id != department_id:
            return {'error': 'Nhân viên phải thuộc phòng ban để có thể trở thành trưởng phòng'}
        
        department.manager_id = employee_id
        db.session.commit()
        
        return self._serialize_department(department)
    
    def get_department_employees(self, department_id, current_user):
        """Get employees of a department."""
        from app.services.employee_service import EmployeeService
        employee_service = EmployeeService()
        
        return employee_service.get_employees_by_department(department_id, current_user)
    
    def get_department_statistics(self):
        """Get statistics about departments."""
        departments = Department.query.all()
        
        statistics = []
        for dept in departments:
            # Tính số lượng nhân viên
            employee_count = len(dept.employees)
            
            # Tính tổng lương
            total_salary = sum(emp.salary for emp in dept.employees) if dept.employees else 0
            
            # Tính lương trung bình
            avg_salary = total_salary / employee_count if employee_count > 0 else 0
            
            statistics.append({
                'id': dept.id,
                'name': dept.name,
                'manager_name': dept.manager.full_name if dept.manager else None,
                'employee_count': employee_count,
                'total_salary': total_salary,
                'average_salary': avg_salary
            })
        
        return statistics
    
    def _serialize_department(self, department):
        """Convert department object to dictionary."""
        return {
            'id': department.id,
            'name': department.name,
            'description': department.description,
            'manager_id': department.manager_id,
            'manager_name': department.manager.full_name if department.manager else None,
            'employee_count': len(department.employees),
            'created_at': department.created_at.isoformat() if department.created_at else None,
            'updated_at': department.updated_at.isoformat() if department.updated_at else None
        }
