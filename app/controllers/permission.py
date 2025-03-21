from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.models.database_schema import User, Role, Permission, db
from app.utils.audit_logger import log_action
from app.utils.rbac import admin_required

permission_routes = Blueprint('permission', __name__)

@permission_routes.route('/', methods=['GET'])
@login_required
@admin_required
def get_permissions():
    """Lấy danh sách tất cả quyền."""
    permissions = Permission.query.all()
    return jsonify([{
        'id': permission.id,
        'name': permission.name,
        'description': permission.description,
        'resource': permission.resource,
        'action': permission.action
    } for permission in permissions])

@permission_routes.route('/<int:permission_id>', methods=['GET'])
@login_required
@admin_required
def get_permission(permission_id):
    """Lấy thông tin của một quyền cụ thể."""
    permission = Permission.query.get(permission_id)
    if not permission:
        return jsonify({'error': 'Không tìm thấy quyền'}), 404
    
    return jsonify({
        'id': permission.id,
        'name': permission.name,
        'description': permission.description,
        'resource': permission.resource,
        'action': permission.action
    })

@permission_routes.route('/', methods=['POST'])
@login_required
@admin_required
def create_permission():
    """Tạo quyền mới."""
    data = request.get_json()
    
    # Kiểm tra tên quyền đã tồn tại chưa
    if Permission.query.filter_by(name=data.get('name')).first():
        return jsonify({'error': 'Tên quyền đã tồn tại'}), 400
    
    # Tạo quyền mới
    permission = Permission(
        name=data.get('name'),
        description=data.get('description'),
        resource=data.get('resource'),
        action=data.get('action')
    )
    
    db.session.add(permission)
    db.session.commit()
    
    log_action('CREATE', 'permission', permission.id, f"Tạo quyền {permission.name}")
    
    return jsonify({
        'id': permission.id,
        'name': permission.name,
        'description': permission.description,
        'resource': permission.resource,
        'action': permission.action
    }), 201

@permission_routes.route('/<int:permission_id>', methods=['PUT'])
@login_required
@admin_required
def update_permission(permission_id):
    """Cập nhật thông tin quyền."""
    data = request.get_json()
    permission = Permission.query.get(permission_id)
    
    if not permission:
        return jsonify({'error': 'Không tìm thấy quyền'}), 404
    
    # Kiểm tra tên quyền nếu được cập nhật
    if 'name' in data and data['name'] != permission.name:
        if Permission.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Tên quyền đã tồn tại'}), 400
        permission.name = data['name']
    
    # Cập nhật các thông tin khác
    if 'description' in data:
        permission.description = data['description']
    
    if 'resource' in data:
        permission.resource = data['resource']
    
    if 'action' in data:
        permission.action = data['action']
    
    db.session.commit()
    
    log_action('UPDATE', 'permission', permission.id, f"Cập nhật quyền {permission.name}")
    
    return jsonify({
        'id': permission.id,
        'name': permission.name,
        'description': permission.description,
        'resource': permission.resource,
        'action': permission.action
    })

@permission_routes.route('/<int:permission_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_permission(permission_id):
    """Xóa quyền."""
    permission = Permission.query.get(permission_id)
    
    if not permission:
        return jsonify({'error': 'Không tìm thấy quyền'}), 404
    
    # Kiểm tra xem quyền có đang được sử dụng không
    if permission.roles:
        return jsonify({'error': 'Không thể xóa quyền đang được sử dụng bởi vai trò'}), 400
    
    permission_name = permission.name
    db.session.delete(permission)
    db.session.commit()
    
    log_action('DELETE', 'permission', permission_id, f"Xóa quyền {permission_name}")
    
    return jsonify({'message': 'Xóa quyền thành công'})

@permission_routes.route('/<int:permission_id>/roles', methods=['GET'])
@login_required
@admin_required
def get_permission_roles(permission_id):
    """Lấy danh sách vai trò có quyền này."""
    permission = Permission.query.get(permission_id)
    
    if not permission:
        return jsonify({'error': 'Không tìm thấy quyền'}), 404
    
    return jsonify([{
        'id': role.id,
        'name': role.name,
        'description': role.description,
        'role_type': role.role_type.value
    } for role in permission.roles])
