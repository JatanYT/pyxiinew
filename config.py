"""
MySQL Database Configuration for Windows
========================================
Default Windows MySQL installation settings:
- User: root
- Password: (empty by default, or set during installation)
- Port: 3306
- Host: localhost
"""

# CHANGE THESE VALUES TO MATCH YOUR WINDOWS MySQL INSTALLATION
DB_CONFIG = {
    'host': 'localhost',        # Usually 'localhost' for local MySQL
    'user': 'root',             # Default MySQL user on Windows
    'password': 'root',             # Leave empty if no password, otherwise add your password
    'database': 'snake_game',   # Database name (will be created automatically)
    'port': 3306,               # Default MySQL port
    'auth_plugin': 'mysql_native_password'  # Important for Windows MySQL
}
