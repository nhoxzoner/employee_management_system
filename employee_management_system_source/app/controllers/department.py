from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models.database_schema import Department, Employee, db
from app.services.department_service import DepartmentService
from app.utils.audit_logger import log_action
from app.utils.rbac import has_permission, admin_required

department_routes = Blueprint('department', __name__)
department_service = DepartmentService()

@department_routes.route('/', methods=['GET'])
@login_required
def get_departments():
    """Lấy danh sách tất cả phòng ban."""
    departments = department_service.get_all_departments()
    return jsonify(departments)

@department_routes.route('/<int:department_id>', methods=['GET'])
@login_required
def get_department(department_id):
    """Lấy thông tin của một phòng ban cụ thể."""
    if not has_permission(current_user, 'department', 'read', department_id):
        return jsonify({'error': 'Không có quyền truy cập'}), 403
        
    department = department_service.get_department_by_id(department_id)
    if not department:
        return jsonify({'error': 'Không tìm thấy phòng ban'}), 404
    return jsonify(department)

@department_routes.route('/', methods=['POST'])
@login_required
@admin_required
def create_department():
    """Tạo phòng ban mới."""
    data = request.get_json()
    result = department_service.create_department(data)
    if 'error' in result:
        return jsonify(result), 400
    
    log_action('CREATE', 'department', result['id'], f"Tạo phòng ban {result['name']}")
    return jsonify(result), 201

@department_routes.route('/<int:department_id>', methods=['PUT'])
@login_required
@admin_required
def update_department(department_id):
    """Cập nhật thông tin phòng ban."""
    data = request.get_json()
    result = department_service.update_department(department_id, data)
    if 'error' in result:
        return jsonify(result), 400
    
    log_action('UPDATE', 'department', department_id, f"Cập nhật phòng ban {result['name']}")
    return jsonify(result)

@department_routes.route('/<int:department_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_department(department_id):
    """Xóa phòng ban."""
    result = department_service.delete_department(department_id)
    if 'error' in result:
        return jsonify(result), 400
    
    log_action('DELETE', 'department', department_id, f"Xóa phòng ban {result['name']}")
    return jsonify({'message': 'Xóa phòng ban thành công'})

@department_routes.route('/<int:department_id>/manager', methods=['PUT'])
@login_required
@admin_required
def set_department_manager(department_id):
    """Thiết lập trưởng phòng cho phòng ban."""
    data = request.get_json()
    result = department_service.set_department_manager(department_id, data['employee_id'])
    if 'error' in result:
        return jsonify(result), 400
    
    log_action('UPDATE', 'department', department_id, f"Thiết lập trưởng phòng {data['employee_id']} cho phòng ban {department_id}")
    return jsonify(result)

@department_routes.route('/<int:department_id>/employees', methods=['GET'])
@login_required
def get_department_employees(department_id):
    """Lấy danh sách nhân viên của phòng ban."""
    # Kiểm tra quyền truy cập
    if not has_permission(current_user, 'department', 'read', department_id):
        return jsonify({'error': 'Không có quyền truy cập'}), 403
        
    employees = department_service.get_department_employees(department_id, current_user)
    return jsonify(employees)

@department_routes.route('/statistics', methods=['GET'])
@login_required
@admin_required
def get_department_statistics():
    """Lấy thống kê về các phòng ban."""
    statistics = department_service.get_department_statistics()
    return jsonify(statistics)
