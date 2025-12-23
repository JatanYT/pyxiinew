"""
Windows MySQL Database Setup for Snake Game
Run this script FIRST to create the database and tables
"""

import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG

def setup_database():
    """Setup MySQL database and tables for Snake Game on Windows"""
    connection = None
    cursor = None
    
    try:
        print("🔌 Connecting to MySQL server on Windows...")
        
        # First connect without database to create it
        temp_config = DB_CONFIG.copy()
        temp_config.pop('database', None)  # Remove database for initial connection
        
        connection = mysql.connector.connect(**temp_config)
        
        if connection.is_connected():
            cursor = connection.cursor()
            print("✅ Connected to MySQL server")
            
            # Create database if not exists
            print("📦 Creating database...")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
            cursor.execute(f"USE {DB_CONFIG['database']}")
            print(f"✅ Database '{DB_CONFIG['database']}' ready")
            
            # Create users table
            print("👤 Creating users table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("✅ Users table created")
            
            # Create scores table
            print("🏆 Creating scores table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scores (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    score INT NOT NULL,
                    level INT DEFAULT 1,
                    game_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            print("✅ Scores table created")
            
            # Create index for faster leaderboard queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_score ON scores(score DESC)')
            
            print("\n" + "="*50)
            print("🎉 DATABASE SETUP COMPLETED SUCCESSFULLY!")
            print("="*50)
            
    except Error as e:
        print(f"\n❌ Error during database setup: {e}")
        
        # Windows-specific troubleshooting
        if "Access denied" in str(e):
            print("\n🔧 WINDOWS MYSQL TROUBLESHOOTING:")
            print("1. MySQL might not be running: Open Services (services.msc) and start 'MySQL80' or 'MySQL'")
            print("2. You might need to set a password. Try these steps:")
            print("   a. Open Command Prompt as Administrator")
            print("   b. Run: mysql -u root -p")
            print("   c. If it asks for password, press Enter (empty password)")
            print("   d. Inside MySQL, run: ALTER USER 'root'@'localhost' IDENTIFIED BY 'new_password';")
            print("3. Update the password in config.py if you set one")
        
        elif "Can't connect" in str(e):
            print("\n🔧 MYSQL NOT RUNNING:")
            print("1. Open Services (press Win+R, type 'services.msc')")
            print("2. Find 'MySQL80' or 'MySQL' service")
            print("3. Right-click and select 'Start'")
            print("4. If service doesn't exist, install MySQL from: https://dev.mysql.com/downloads/installer/")
            
    finally:
        # Clean up resources
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
            print("🔌 Database connection closed")

def create_test_data():
    """Create test user and sample scores for quick testing"""
    connection = None
    cursor = None
    
    try:
        print("\n📝 Creating test data...")
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Create test user
        cursor.execute("INSERT IGNORE INTO users (username) VALUES ('test_player')")
        connection.commit()
        
        # Get user ID
        cursor.execute("SELECT id FROM users WHERE username = 'test_player'")
        user_id = cursor.fetchone()
        
        if user_id:
            # Clear any existing test scores
            cursor.execute("DELETE FROM scores WHERE user_id = %s", (user_id[0],))
            
            # Add sample scores
            sample_scores = [
                (user_id[0], 450, 5),
                (user_id[0], 320, 4),
                (user_id[0], 180, 3),
                (user_id[0], 90, 2),
                (user_id[0], 50, 1)
            ]
            
            cursor.executemany(
                "INSERT INTO scores (user_id, score, level) VALUES (%s, %s, %s)",
                sample_scores
            )
            connection.commit()
            print("✅ Test data created: User 'test_player' with 5 sample scores")
            
    except Error as e:
        print(f"⚠️  Could not create test data: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    print("="*50)
    print("SNAKE GAME - WINDOWS MySQL DATABASE SETUP")
    print("="*50)
    
    print("\n📋 Checking your configuration...")
    print(f"Host: {DB_CONFIG['host']}")
    print(f"User: {DB_CONFIG['user']}")
    print(f"Database: {DB_CONFIG.get('database', 'snake_game')}")
    print(f"Password: {'[SET]' if DB_CONFIG['password'] else '[NOT SET]'}")
    
    setup_database()
    
    # Ask if user wants test data
    response = input("\nDo you want to create test user with sample scores? (y/n): ").lower()
    if response == 'y':
        create_test_data()
    
    print("\n✅ SETUP COMPLETE!")
    print("\n📋 Next steps:")
    print("1. Install pygame if not done: pip install pygame")
    print("2. Run the game: python snake_game.py")
    print("3. If connection fails, check config.py and ensure MySQL is running")
    print("="*50)
