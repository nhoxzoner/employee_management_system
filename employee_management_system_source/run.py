from app import create_app
import os

app = create_app(os.getenv('FLASK_ENV', 'development'))

@app.shell_context_processor
def make_shell_context():
    """Cung cấp context cho shell."""
    from app.models.database_schema import db, User, Role, Permission, Employee, Department, AuditLog
    return {
        'db': db,
        'User': User,
        'Role': Role,
        'Permission': Permission,
        'Employee': Employee,
        'Department': Department,
        'AuditLog': AuditLog
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
