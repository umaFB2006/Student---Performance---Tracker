import sqlite3

DATABASE = "database.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():

    conn = get_db_connection()
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    """)

    # STUDENTS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT NOT NULL,
        rollno TEXT UNIQUE NOT NULL,
        gender TEXT NOT NULL
    )
    """)

    # GRADES TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS grades(
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        student_name TEXT NOT NULL,
        rollno TEXT NOT NULL,

        telugu INTEGER,
        hindi INTEGER,
        english INTEGER,
        social INTEGER,
        physics INTEGER,
        maths INTEGER,
        biology INTEGER
    )
    """)

    conn.commit()
    conn.close()