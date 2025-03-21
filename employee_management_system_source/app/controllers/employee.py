from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models.database_schema import Employee, Department, db
from app.services.employee_service import EmployeeService
from app.utils.audit_logger import log_action
from app.utils.rbac import has_permission

employee_routes = Blueprint('employee', __name__)
employee_service = EmployeeService()

@employee_routes.route('/', methods=['GET'])
@login_required
def get_employees():
    """Lấy danh sách nhân viên dựa trên quyền của người dùng."""
    employees = employee_service.get_employees_by_permission(current_user)
    return jsonify(employees)

@employee_routes.route('/<int:employee_id>', methods=['GET'])
@login_required
def get_employee(employee_id):
    """Lấy thông tin của một nhân viên cụ thể."""
    if not has_permission(current_user, 'employee', 'read', employee_id):
        return jsonify({'error': 'Không có quyền truy cập'}), 403
        
    employee = employee_service.get_employee_by_id(employee_id)
    if not employee:
        return jsonify({'error': 'Không tìm thấy nhân viên'}), 404
    
    return jsonify(employee)

@employee_routes.route('/', methods=['POST'])
@login_required
def create_employee():
    """Tạo nhân viên mới."""
    if not has_permission(current_user, 'employee', 'create'):
        return jsonify({'error': 'Không có quyền tạo nhân viên'}), 403
        
    data = request.get_json()
    result = employee_service.create_employee(data)
    if 'error' in result:
        return jsonify(result), 400
    
    log_action('CREATE', 'employee', result['id'], f"Tạo nhân viên {result['full_name']}")
    return jsonify(result), 201

@employee_routes.route('/<int:employee_id>', methods=['PUT'])
@login_required
def update_employee(employee_id):
    """Cập nhật thông tin nhân viên."""
    if not has_permission(current_user, 'employee', 'update', employee_id):
        return jsonify({'error': 'Không có quyền cập nhật nhân viên'}), 403
        
    data = request.get_json()
    result = employee_service.update_employee(employee_id, data)
    if 'error' in result:
        return jsonify(result), 400
    
    log_action('UPDATE', 'employee', employee_id, f"Cập nhật nhân viên {result['full_name']}")
    return jsonify(result)

@employee_routes.route('/<int:employee_id>', methods=['DELETE'])
@login_required
def delete_employee(employee_id):
    """Xóa nhân viên."""
    if not has_permission(current_user, 'employee', 'delete', employee_id):
        return jsonify({'error': 'Không có quyền xóa nhân viên'}), 403
        
    result = employee_service.delete_employee(employee_id)
    if 'error' in result:
        return jsonify(result), 400
    
    log_action('DELETE', 'employee', employee_id, f"Xóa nhân viên {result['full_name']}")
    return jsonify({'message': 'Xóa nhân viên thành công'})

@employee_routes.route('/department/<int:department_id>', methods=['GET'])
@login_required
def get_employees_by_department(department_id):
    """Lấy danh sách nhân viên theo phòng ban."""
    if not has_permission(current_user, 'department', 'read', department_id):
        return jsonify({'error': 'Không có quyền truy cập'}), 403
        
    employees = employee_service.get_employees_by_department(department_id, current_user)
    return jsonify(employees)

@employee_routes.route('/search', methods=['GET'])
@login_required
def search_employees():
    """Tìm kiếm nhân viên theo các tiêu chí."""
    query = request.args.get('query', '')
    department_id = request.args.get('department_id')
    
    if department_id and department_id.isdigit():
        department_id = int(department_id)
        if not has_permission(current_user, 'department', 'read', department_id):
            return jsonify({'error': 'Không có quyền truy cập phòng ban này'}), 403
    
    # Gọi service để tìm kiếm nhân viên
    employees = employee_service.search_employees(current_user, query, department_id)
    return jsonify(employees)
