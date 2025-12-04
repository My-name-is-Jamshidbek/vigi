import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

# Database path
DB_PATH = Path(__file__).parent / "users.db"

class User:
    """User model"""
    def __init__(self, telegram_id: int, fullname: str, status: str = "active", created_at: str = None, updated_at: str = None):
        self.telegram_id = telegram_id
        self.fullname = fullname
        self.status = status
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()

    def __repr__(self):
        return f"User(telegram_id={self.telegram_id}, fullname={self.fullname}, status={self.status})"

    def to_dict(self):
        return {
            "telegram_id": self.telegram_id,
            "fullname": self.fullname,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class Database:
    """Database operations"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                fullname TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, user: User) -> bool:
        """Create a new user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO users (telegram_id, fullname, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (user.telegram_id, user.fullname, user.status, user.created_at, user.updated_at))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_user(self, telegram_id: int) -> Optional[User]:
        """Get user by telegram_id"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT telegram_id, fullname, status, created_at, updated_at
            FROM users WHERE telegram_id = ?
        ''', (telegram_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(row[0], row[1], row[2], row[3], row[4])
        return None
    
    def update_user(self, telegram_id: int, fullname: str = None, status: str = None) -> bool:
        """Update user information"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            update_fields = []
            params = []
            
            if fullname is not None:
                update_fields.append("fullname = ?")
                params.append(fullname)
            
            if status is not None:
                update_fields.append("status = ?")
                params.append(status)
            
            if not update_fields:
                return False
            
            # Always update the updated_at timestamp
            update_fields.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            
            params.append(telegram_id)
            
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE telegram_id = ?"
            cursor.execute(query, params)
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
    
    def delete_user(self, telegram_id: int) -> bool:
        """Delete user by telegram_id"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM users WHERE telegram_id = ?', (telegram_id,))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
    
    def get_all_users(self) -> List[User]:
        """Get all users"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT telegram_id, fullname, status, created_at, updated_at
            FROM users
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [User(row[0], row[1], row[2], row[3], row[4]) for row in rows]
    
    def user_exists(self, telegram_id: int) -> bool:
        """Check if user exists"""
        return self.get_user(telegram_id) is not None
    
    def get_users_count(self) -> int:
        """Get total number of users"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    
    def get_users_by_status(self, status: str) -> List[User]:
        """Get users by status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT telegram_id, fullname, status, created_at, updated_at
            FROM users WHERE status = ?
        ''', (status,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [User(row[0], row[1], row[2], row[3], row[4]) for row in rows]


# Initialize database
db = Database()
