from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.models.database_schema import Role, Permission, db
from app.utils.audit_logger import log_action
from app.utils.rbac import admin_required

role_routes = Blueprint('role', __name__)

@role_routes.route('/', methods=['GET'])
@login_required
@admin_required
def get_roles():
    """Lấy danh sách tất cả vai trò."""
    roles = Role.query.all()
    return jsonify([{
        'id': role.id,
        'name': role.name,
        'description': role.description,
        'role_type': role.role_type.value,
        'permissions': [{
            'id': permission.id,
            'name': permission.name,
            'resource': permission.resource,
            'action': permission.action
        } for permission in role.permissions]
    } for role in roles])

@role_routes.route('/<int:role_id>', methods=['GET'])
@login_required
@admin_required
def get_role(role_id):
    """Lấy thông tin của một vai trò cụ thể."""
    role = Role.query.get(role_id)
    if not role:
        return jsonify({'error': 'Không tìm thấy vai trò'}), 404
    
    return jsonify({
        'id': role.id,
        'name': role.name,
        'description': role.description,
        'role_type': role.role_type.value,
        'permissions': [{
            'id': permission.id,
            'name': permission.name,
            'resource': permission.resource,
            'action': permission.action
        } for permission in role.permissions]
    })

@role_routes.route('/', methods=['POST'])
@login_required
@admin_required
def create_role():
    """Tạo vai trò mới."""
    data = request.get_json()
    
    # Kiểm tra tên vai trò đã tồn tại chưa
    if Role.query.filter_by(name=data.get('name')).first():
        return jsonify({'error': 'Tên vai trò đã tồn tại'}), 400
    
    # Kiểm tra role_type hợp lệ
    try:
        from app.models.database_schema import RoleType
        role_type = RoleType[data.get('role_type', 'EMPLOYEE').upper()]
    except KeyError:
        return jsonify({'error': 'Loại vai trò không hợp lệ'}), 400
    
    # Tạo vai trò mới
    role = Role(
        name=data.get('name'),
        description=data.get('description'),
        role_type=role_type
    )
    
    # Thêm quyền nếu được cung cấp
    if 'permission_ids' in data and data['permission_ids']:
        for permission_id in data['permission_ids']:
            permission = Permission.query.get(permission_id)
            if permission:
                role.permissions.append(permission)
    
    db.session.add(role)
    db.session.commit()
    
    log_action('CREATE', 'role', role.id, f"Tạo vai trò {role.name}")
    
    return jsonify({
        'id': role.id,
        'name': role.name,
        'description': role.description,
        'role_type': role.role_type.value,
        'permissions': [{
            'id': permission.id,
            'name': permission.name,
            'resource': permission.resource,
            'action': permission.action
        } for permission in role.permissions]
    }), 201

@role_routes.route('/<int:role_id>', methods=['PUT'])
@login_required
@admin_required
def update_role(role_id):
    """Cập nhật thông tin vai trò."""
    data = request.get_json()
    role = Role.query.get(role_id)
    
    if not role:
        return jsonify({'error': 'Không tìm thấy vai trò'}), 404
    
    # Kiểm tra tên vai trò nếu được cập nhật
    if 'name' in data and data['name'] != role.name:
        if Role.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Tên vai trò đã tồn tại'}), 400
        role.name = data['name']
    
    # Cập nhật mô tả nếu được cung cấp
    if 'description' in data:
        role.description = data['description']
    
    # Cập nhật role_type nếu được cung cấp
    if 'role_type' in data:
        try:
            from app.models.database_schema import RoleType
            role.role_type = RoleType[data['role_type'].upper()]
        except KeyError:
            return jsonify({'error': 'Loại vai trò không hợp lệ'}), 400
    
    # Cập nhật quyền nếu được cung cấp
    if 'permission_ids' in data:
        # Xóa tất cả quyền hiện tại
        role.permissions = []
        
        # Thêm quyền mới
        for permission_id in data['permission_ids']:
            permission = Permission.query.get(permission_id)
            if permission:
                role.permissions.append(permission)
    
    db.session.commit()
    
    log_action('UPDATE', 'role', role.id, f"Cập nhật vai trò {role.name}")
    
    return jsonify({
        'id': role.id,
        'name': role.name,
        'description': role.description,
        'role_type': role.role_type.value,
        'permissions': [{
            'id': permission.id,
            'name': permission.name,
            'resource': permission.resource,
            'action': permission.action
        } for permission in role.permissions]
    })

@role_routes.route('/<int:role_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_role(role_id):
    """Xóa vai trò."""
    role = Role.query.get(role_id)
    
    if not role:
        return jsonify({'error': 'Không tìm thấy vai trò'}), 404
    
    # Kiểm tra xem vai trò có đang được sử dụng không
    if role.users:
        return jsonify({'error': 'Không thể xóa vai trò đang được sử dụng bởi người dùng'}), 400
    
    role_name = role.name
    db.session.delete(role)
    db.session.commit()
    
    log_action('DELETE', 'role', role_id, f"Xóa vai trò {role_name}")
    
    return jsonify({'message': 'Xóa vai trò thành công'})

@role_routes.route('/<int:role_id>/permissions', methods=['GET'])
@login_required
@admin_required
def get_role_permissions(role_id):
    """Lấy danh sách quyền của vai trò."""
    role = Role.query.get(role_id)
    
    if not role:
        return jsonify({'error': 'Không tìm thấy vai trò'}), 404
    
    return jsonify([{
        'id': permission.id,
        'name': permission.name,
        'resource': permission.resource,
        'action': permission.action
    } for permission in role.permissions])

@role_routes.route('/permissions', methods=['GET'])
@login_required
@admin_required
def get_all_permissions():
    """Lấy danh sách tất cả quyền."""
    permissions = Permission.query.all()
    
    return jsonify([{
        'id': permission.id,
        'name': permission.name,
        'description': permission.description,
        'resource': permission.resource,
        'action': permission.action
    } for permission in permissions])
