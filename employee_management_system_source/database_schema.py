from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import enum

db = SQLAlchemy()

# Enum cho các loại vai trò
class RoleType(enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    HR_EMPLOYEE = "hr_employee"
    HR_MANAGER = "hr_manager"
    ACCOUNTING = "accounting"

# Enum cho các loại hành động trong nhật ký
class ActionType(enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    FAILED_LOGIN = "failed_login"

# Bảng liên kết nhiều-nhiều giữa User và Role
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

# Bảng liên kết nhiều-nhiều giữa Role và Permission
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
)

# Bảng User
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Quan hệ với Employee (1-1)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    employee = db.relationship('Employee', backref=db.backref('user', uselist=False))
    
    # Quan hệ với Role (nhiều-nhiều)
    roles = db.relationship('Role', secondary=user_roles, lazy='subquery',
                           backref=db.backref('users', lazy=True))
    
    # Quan hệ với AuditLog (1-nhiều)
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

# Bảng Role
class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255))
    role_type = db.Column(db.Enum(RoleType), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Quan hệ với Permission (nhiều-nhiều)
    permissions = db.relationship('Permission', secondary=role_permissions, lazy='subquery',
                                 backref=db.backref('roles', lazy=True))
    
    def __repr__(self):
        return f'<Role {self.name}>'

# Bảng Permission
class Permission(db.Model):
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255))
    resource = db.Column(db.String(64), nullable=False)  # employee, department, etc.
    action = db.Column(db.String(64), nullable=False)    # create, read, update, delete
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Permission {self.name}>'

# Bảng Department
class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Quan hệ với Employee (1-nhiều)
    employees = db.relationship('Employee', backref='department', lazy=True)
    
    # Quan hệ với Manager (1-1)
    manager_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=True)
    manager = db.relationship('Employee', foreign_keys=[manager_id], post_update=True)
    
    def __repr__(self):
        return f'<Department {self.name}>'

# Bảng Employee
class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_code = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    salary = db.Column(db.Float, nullable=False)
    tax_code = db.Column(db.String(20), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Quan hệ với Department (nhiều-1)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    
    # Quan hệ với các phòng ban mà nhân viên là trưởng phòng (1-nhiều)
    managed_departments = db.relationship('Department', 
                                         foreign_keys=[Department.manager_id],
                                         backref='department_manager',
                                         lazy=True)
    
    def __repr__(self):
        return f'<Employee {self.employee_code}>'

# Bảng AuditLog
class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.Enum(ActionType), nullable=False)
    resource = db.Column(db.String(64), nullable=False)  # employee, department, etc.
    resource_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AuditLog {self.id}>'
