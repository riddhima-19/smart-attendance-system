import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def initialize_database():
    """Initialize database with all required tables"""
    try:
        conn = sqlite3.connect('college.db')
        c = conn.cursor()
        
        # Enable foreign key support
        c.execute("PRAGMA foreign_keys = ON")

        # Student information table
        c.execute('''CREATE TABLE IF NOT EXISTS student_info (
        college_id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        course TEXT NOT NULL,
        year TEXT NOT NULL,
        phone_number TEXT,
        email TEXT,
        parents_name TEXT,
        address TEXT,
        profile_photo BLOB,
        face_data BLOB,
        password TEXT,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

        # Attendance records table with improved constraints
        c.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                college_id TEXT NOT NULL,
                name TEXT NOT NULL,
                course TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT DEFAULT 'Present',
                FOREIGN KEY(college_id) REFERENCES student_info(college_id) ON DELETE CASCADE,
                UNIQUE(college_id, date)  -- Prevent duplicate daily attendance
            )
        ''')

        # College IDs table for verification
        c.execute('''
            CREATE TABLE IF NOT EXISTS college_ids (
                college_id TEXT PRIMARY KEY,
                is_used BOOLEAN DEFAULT FALSE
            )
        ''')

        # Create indexes for better performance
        c.execute('CREATE INDEX IF NOT EXISTS idx_student_id ON student_info(college_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(college_id)')

        conn.commit()
        logging.info("Database tables created successfully")
        
    except sqlite3.Error as e:
        logging.error(f"Database initialization failed: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    initialize_database()