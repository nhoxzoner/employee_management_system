from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models.database_schema import AuditLog, ActionType, User, db
from app.utils.audit_logger import get_audit_logs
from app.utils.rbac import admin_required

audit_routes = Blueprint('audit', __name__)

@audit_routes.route('/', methods=['GET'])
@login_required
@admin_required
def get_audit_log_entries():
    """Lấy danh sách nhật ký hệ thống."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Xây dựng bộ lọc từ tham số truy vấn
    filters = {}
    
    if 'user_id' in request.args and request.args['user_id']:
        filters['user_id'] = int(request.args['user_id'])
    
    if 'action' in request.args and request.args['action']:
        filters['action'] = request.args['action']
    
    if 'resource' in request.args and request.args['resource']:
        filters['resource'] = request.args['resource']
    
    if 'start_date' in request.args and request.args['start_date']:
        from datetime import datetime
        try:
            filters['start_date'] = datetime.strptime(request.args['start_date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Định dạng ngày bắt đầu không hợp lệ (YYYY-MM-DD)'}), 400
    
    if 'end_date' in request.args and request.args['end_date']:
        from datetime import datetime
        try:
            filters['end_date'] = datetime.strptime(request.args['end_date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Định dạng ngày kết thúc không hợp lệ (YYYY-MM-DD)'}), 400
    
    # Lấy danh sách nhật ký
    logs, pagination = get_audit_logs(filters, page, per_page)
    
    # Chuyển đổi kết quả thành JSON
    result = {
        'logs': [{
            'id': log.id,
            'user_id': log.user_id,
            'username': User.query.get(log.user_id).username if log.user_id else None,
            'action': log.action.value,
            'resource': log.resource,
            'resource_id': log.resource_id,
            'details': log.details,
            'ip_address': log.ip_address,
            'timestamp': log.timestamp.isoformat()
        } for log in logs],
        'pagination': pagination
    }
    
    return jsonify(result)

@audit_routes.route('/actions', methods=['GET'])
@login_required
@admin_required
def get_audit_actions():
    """Lấy danh sách các loại hành động."""
    actions = [action.value for action in ActionType]
    return jsonify(actions)

@audit_routes.route('/resources', methods=['GET'])
@login_required
@admin_required
def get_audit_resources():
    """Lấy danh sách các loại tài nguyên."""
    # Lấy danh sách các loại tài nguyên duy nhất từ cơ sở dữ liệu
    resources = db.session.query(AuditLog.resource).distinct().all()
    return jsonify([resource[0] for resource in resources])

@audit_routes.route('/users', methods=['GET'])
@login_required
@admin_required
def get_audit_users():
    """Lấy danh sách người dùng có nhật ký."""
    # Lấy danh sách user_id duy nhất từ cơ sở dữ liệu
    user_ids = db.session.query(AuditLog.user_id).filter(AuditLog.user_id != None).distinct().all()
    user_ids = [user_id[0] for user_id in user_ids]
    
    # Lấy thông tin người dùng
    users = User.query.filter(User.id.in_(user_ids)).all()
    
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email
    } for user in users])

@audit_routes.route('/statistics', methods=['GET'])
@login_required
@admin_required
def get_audit_statistics():
    """Lấy thống kê về nhật ký hệ thống."""
    # Tổng số bản ghi
    total_logs = AuditLog.query.count()
    
    # Số lượng bản ghi theo loại hành động
    action_stats = db.session.query(
        AuditLog.action, 
        db.func.count(AuditLog.id)
    ).group_by(AuditLog.action).all()
    
    # Số lượng bản ghi theo loại tài nguyên
    resource_stats = db.session.query(
        AuditLog.resource, 
        db.func.count(AuditLog.id)
    ).group_by(AuditLog.resource).all()
    
    # Số lượng bản ghi theo người dùng (top 10)
    user_stats = db.session.query(
        AuditLog.user_id, 
        db.func.count(AuditLog.id)
    ).filter(AuditLog.user_id != None).group_by(AuditLog.user_id).order_by(
        db.func.count(AuditLog.id).desc()
    ).limit(10).all()
    
    # Lấy thông tin người dùng
    user_ids = [user_id for user_id, _ in user_stats]
    users = {user.id: user.username for user in User.query.filter(User.id.in_(user_ids)).all()}
    
    return jsonify({
        'total_logs': total_logs,
        'action_stats': [{
            'action': action.value,
            'count': count
        } for action, count in action_stats],
        'resource_stats': [{
            'resource': resource,
            'count': count
        } for resource, count in resource_stats],
        'user_stats': [{
            'user_id': user_id,
            'username': users.get(user_id, 'Unknown'),
            'count': count
        } for user_id, count in user_stats]
    })
