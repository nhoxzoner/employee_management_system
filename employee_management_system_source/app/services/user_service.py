from app.models.database_schema import User, db

class UserService:
    """Service class for user management operations."""
    
    def get_all_users(self):
        """Get all users."""
        users = User.query.all()
        return [self._serialize_user(user) for user in users]
    
    def get_user_by_id(self, user_id):
        """Get user by ID."""
        user = User.query.get(user_id)
        if not user:
            return None
        return self._serialize_user(user)
    
    def get_user_by_username(self, username):
        """Get user by username."""
        user = User.query.filter_by(username=username).first()
        if not user:
            return None
        return self._serialize_user(user)
    
    def create_user(self, data):
        """Create a new user."""
        # Check if username or email already exists
        if User.query.filter_by(username=data.get('username')).first():
            return {'error': 'Tên đăng nhập đã tồn tại'}
        
        if User.query.filter_by(email=data.get('email')).first():
            return {'error': 'Email đã tồn tại'}
        
        # Create new user
        from werkzeug.security import generate_password_hash
        
        user = User(
            username=data.get('username'),
            email=data.get('email'),
            password_hash=generate_password_hash(data.get('password')),
            is_active=data.get('is_active', True)
        )
        
        # Add employee association if provided
        if 'employee_id' in data and data['employee_id']:
            from app.models.database_schema import Employee
            employee = Employee.query.get(data['employee_id'])
            if employee:
                user.employee = employee
        
        db.session.add(user)
        db.session.commit()
        
        return self._serialize_user(user)
    
    def update_user(self, user_id, data):
        """Update user information."""
        user = User.query.get(user_id)
        if not user:
            return {'error': 'Không tìm thấy người dùng'}
        
        # Update username if provided and not already taken
        if 'username' in data and data['username'] != user.username:
            if User.query.filter_by(username=data['username']).first():
                return {'error': 'Tên đăng nhập đã tồn tại'}
            user.username = data['username']
        
        # Update email if provided and not already taken
        if 'email' in data and data['email'] != user.email:
            if User.query.filter_by(email=data['email']).first():
                return {'error': 'Email đã tồn tại'}
            user.email = data['email']
        
        # Update password if provided
        if 'password' in data and data['password']:
            from werkzeug.security import generate_password_hash
            user.password_hash = generate_password_hash(data['password'])
        
        # Update active status if provided
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        # Update employee association if provided
        if 'employee_id' in data:
            from app.models.database_schema import Employee
            employee = Employee.query.get(data['employee_id'])
            if employee:
                user.employee = employee
            elif data['employee_id'] is None:
                user.employee = None
        
        db.session.commit()
        
        return self._serialize_user(user)
    
    def delete_user(self, user_id):
        """Delete a user."""
        user = User.query.get(user_id)
        if not user:
            return {'error': 'Không tìm thấy người dùng'}
        
        # Store user info for return
        user_info = self._serialize_user(user)
        
        db.session.delete(user)
        db.session.commit()
        
        return user_info
    
    def get_user_roles(self, user_id):
        """Get roles assigned to a user."""
        user = User.query.get(user_id)
        if not user:
            return {'error': 'Không tìm thấy người dùng'}
        
        return [{'id': role.id, 'name': role.name, 'role_type': role.role_type.value} for role in user.roles]
    
    def assign_role(self, user_id, role_id):
        """Assign a role to a user."""
        from app.models.database_schema import Role
        
        user = User.query.get(user_id)
        if not user:
            return {'error': 'Không tìm thấy người dùng'}
        
        role = Role.query.get(role_id)
        if not role:
            return {'error': 'Không tìm thấy vai trò'}
        
        # Check if role is already assigned
        if role in user.roles:
            return {'error': 'Vai trò đã được gán cho người dùng này'}
        
        user.roles.append(role)
        db.session.commit()
        
        return {'message': f'Đã gán vai trò {role.name} cho người dùng {user.username}'}
    
    def revoke_role(self, user_id, role_id):
        """Revoke a role from a user."""
        from app.models.database_schema import Role
        
        user = User.query.get(user_id)
        if not user:
            return {'error': 'Không tìm thấy người dùng'}
        
        role = Role.query.get(role_id)
        if not role:
            return {'error': 'Không tìm thấy vai trò'}
        
        # Check if role is assigned
        if role not in user.roles:
            return {'error': 'Người dùng không có vai trò này'}
        
        user.roles.remove(role)
        db.session.commit()
        
        return {'message': f'Đã thu hồi vai trò {role.name} từ người dùng {user.username}'}
    
    def _serialize_user(self, user):
        """Convert user object to dictionary."""
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_active': user.is_active,
            'employee_id': user.employee_id,
            'roles': [{'id': role.id, 'name': role.name, 'role_type': role.role_type.value} for role in user.roles],
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None
        }
