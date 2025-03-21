from flask import request, g
from flask_login import current_user
from app.models.database_schema import AuditLog, ActionType, db
import datetime
import socket

def log_action(action, resource, resource_id=None, details=None):
    """
    Ghi nhật ký hành động của người dùng.
    
    Args:
        action: Loại hành động (LOGIN, LOGOUT, CREATE, READ, UPDATE, DELETE, FAILED_LOGIN)
        resource: Loại tài nguyên (user, employee, department, etc.)
        resource_id: ID của tài nguyên (nếu có)
        details: Chi tiết bổ sung về hành động
    """
    try:
        # Chuyển đổi action thành enum
        if isinstance(action, str):
            action_enum = ActionType[action]
        else:
            action_enum = action
        
        # Lấy thông tin người dùng
        user_id = current_user.id if current_user.is_authenticated else None
        
        # Lấy địa chỉ IP
        ip_address = request.remote_addr
        
        # Tạo bản ghi nhật ký
        audit_log = AuditLog(
            user_id=user_id,
            action=action_enum,
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            timestamp=datetime.datetime.utcnow()
        )
        
        # Lưu vào cơ sở dữ liệu
        db.session.add(audit_log)
        db.session.commit()
        
        return True
    except Exception as e:
        # Ghi lại lỗi nhưng không làm gián đoạn luồng chính
        print(f"Lỗi khi ghi nhật ký: {str(e)}")
        db.session.rollback()
        return False

def get_audit_logs(filters=None, page=1, per_page=20):
    """
    Lấy danh sách nhật ký hệ thống với bộ lọc.
    
    Args:
        filters: Dict chứa các bộ lọc (user_id, action, resource, start_date, end_date)
        page: Số trang
        per_page: Số bản ghi trên mỗi trang
        
    Returns:
        Danh sách các bản ghi nhật ký và thông tin phân trang
    """
    query = AuditLog.query
    
    # Áp dụng bộ lọc
    if filters:
        if 'user_id' in filters and filters['user_id']:
            query = query.filter(AuditLog.user_id == filters['user_id'])
            
        if 'action' in filters and filters['action']:
            try:
                if isinstance(filters['action'], str):
                    action_enum = ActionType[filters['action']]
                else:
                    action_enum = filters['action']
                query = query.filter(AuditLog.action == action_enum)
            except KeyError:
                pass
                
        if 'resource' in filters and filters['resource']:
            query = query.filter(AuditLog.resource == filters['resource'])
            
        if 'start_date' in filters and filters['start_date']:
            query = query.filter(AuditLog.timestamp >= filters['start_date'])
            
        if 'end_date' in filters and filters['end_date']:
            query = query.filter(AuditLog.timestamp <= filters['end_date'])
    
    # Sắp xếp theo thời gian giảm dần (mới nhất trước)
    query = query.order_by(AuditLog.timestamp.desc())
    
    # Phân trang
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return pagination.items, {
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    }
