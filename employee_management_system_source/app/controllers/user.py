from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.models.database_schema import User, Role, db
from app.services.user_service import UserService
from app.utils.audit_logger import log_action
from app.utils.rbac import admin_required

user_routes = Blueprint('user', __name__)
user_service = UserService()

@user_routes.route('/', methods=['GET'])
@login_required
@admin_required
def get_users():
    """Lấy danh sách tất cả người dùng."""
    users = user_service.get_all_users()
    return jsonify(users)

@user_routes.route('/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def get_user(user_id):
    """Lấy thông tin của một người dùng cụ thể."""
    user = user_service.get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'Không tìm thấy người dùng'}), 404
    return jsonify(user)

@user_routes.route('/', methods=['POST'])
@login_required
@admin_required
def create_user():
    """Tạo người dùng mới."""
    data = request.get_json()
    result = user_service.create_user(data)
    if 'error' in result:
        return jsonify(result), 400
    log_action('CREATE', 'user', result['id'], f"Tạo người dùng {result['username']}")
    return jsonify(result), 201

@user_routes.route('/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user_id):
    """Cập nhật thông tin người dùng."""
    data = request.get_json()
    result = user_service.update_user(user_id, data)
    if 'error' in result:
        return jsonify(result), 400
    log_action('UPDATE', 'user', user_id, f"Cập nhật người dùng {result['username']}")
    return jsonify(result)

@user_routes.route('/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """Xóa người dùng."""
    result = user_service.delete_user(user_id)
    if 'error' in result:
        return jsonify(result), 400
    log_action('DELETE', 'user', user_id, f"Xóa người dùng {result['username']}")
    return jsonify({'message': 'Xóa người dùng thành công'})

@user_routes.route('/<int:user_id>/roles', methods=['GET'])
@login_required
@admin_required
def get_user_roles(user_id):
    """Lấy danh sách vai trò của người dùng."""
    roles = user_service.get_user_roles(user_id)
    return jsonify(roles)

@user_routes.route('/<int:user_id>/roles', methods=['POST'])
@login_required
@admin_required
def assign_role(user_id):
    """Gán vai trò cho người dùng."""
    data = request.get_json()
    result = user_service.assign_role(user_id, data['role_id'])
    if 'error' in result:
        return jsonify(result), 400
    log_action('UPDATE', 'user_role', user_id, f"Gán vai trò {data['role_id']} cho người dùng {user_id}")
    return jsonify(result)

@user_routes.route('/<int:user_id>/roles/<int:role_id>', methods=['DELETE'])
@login_required
@admin_required
def revoke_role(user_id, role_id):
    """Thu hồi vai trò từ người dùng."""
    result = user_service.revoke_role(user_id, role_id)
    if 'error' in result:
        return jsonify(result), 400
    log_action('UPDATE', 'user_role', user_id, f"Thu hồi vai trò {role_id} từ người dùng {user_id}")
    return jsonify({'message': 'Thu hồi vai trò thành công'})
