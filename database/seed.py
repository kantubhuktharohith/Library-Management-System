"""Seed the database with sample data."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database.db import init_db, get_db
from werkzeug.security import generate_password_hash
from datetime import date, timedelta


def seed():
    """Populate the database with sample books, members, and an admin."""
    init_db()
    conn = get_db()

    # --- Admin account ---
    admin_hash = generate_password_hash('admin123')
    conn.execute("""
        INSERT OR IGNORE INTO Members (Name, Email, Phone, MembershipType, JoinDate, ExpiryDate, PasswordHash, Role)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ('Admin', 'admin@library.com', '9999999999', 'Faculty',
          date.today().isoformat(), (date.today() + timedelta(days=3650)).isoformat(),
          admin_hash, 'admin'))

    # --- Sample members ---
    members = [
        ('Alice Johnson', 'alice@example.com', '9876543210', 'Student'),
        ('Bob Smith', 'bob@example.com', '9876543211', 'Student'),
        ('Carol Williams', 'carol@example.com', '9876543212', 'Faculty'),
        ('David Brown', 'david@example.com', '9876543213', 'Student'),
        ('Eva Davis', 'eva@example.com', '9876543214', 'Guest'),
    ]
    member_hash = generate_password_hash('member123')
    for name, email, phone, mtype in members:
        conn.execute("""
            INSERT OR IGNORE INTO Members (Name, Email, Phone, MembershipType, JoinDate, ExpiryDate, PasswordHash, Role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, email, phone, mtype,
              date.today().isoformat(), (date.today() + timedelta(days=365)).isoformat(),
              member_hash, 'member'))

    # --- Sample books ---
    books = [
        ('Database Management Systems', 'Henry F. Korth', 'McGraw-Hill', 'Computer Science', '978-0073523323', 5),
        ('Data Structures and Algorithms', 'Thomas H. Cormen', 'MIT Press', 'Computer Science', '978-0262033848', 4),
        ('Introduction to Algorithms', 'Thomas H. Cormen', 'MIT Press', 'Computer Science', '978-0262046305', 3),
        ('Operating System Concepts', 'Abraham Silberschatz', 'Wiley', 'Computer Science', '978-1119800361', 4),
        ('Computer Networking', 'James F. Kurose', 'Pearson', 'Computer Science', '978-0133594140', 3),
        ('Artificial Intelligence: A Modern Approach', 'Stuart Russell', 'Pearson', 'Artificial Intelligence', '978-0134610993', 2),
        ('Clean Code', 'Robert C. Martin', 'Prentice Hall', 'Software Engineering', '978-0132350884', 5),
        ('Design Patterns', 'Erich Gamma', 'Addison-Wesley', 'Software Engineering', '978-0201633610', 3),
        ('The Pragmatic Programmer', 'David Thomas', 'Addison-Wesley', 'Software Engineering', '978-0135957059', 4),
        ('Python Crash Course', 'Eric Matthes', 'No Starch Press', 'Programming', '978-1593279288', 6),
        ('Eloquent JavaScript', 'Marijn Haverbeke', 'No Starch Press', 'Programming', '978-1593279509', 4),
        ('Structure and Interpretation of Computer Programs', 'Harold Abelson', 'MIT Press', 'Computer Science', '978-0262510875', 2),
        ('The Art of Computer Programming', 'Donald E. Knuth', 'Addison-Wesley', 'Computer Science', '978-0201896831', 2),
        ('Machine Learning', 'Tom M. Mitchell', 'McGraw-Hill', 'Artificial Intelligence', '978-0070428072', 3),
        ('Digital Logic and Computer Design', 'M. Morris Mano', 'Pearson', 'Electronics', '978-8131714508', 5),
    ]
    for title, author, publisher, category, isbn, qty in books:
        conn.execute("""
            INSERT OR IGNORE INTO Books (Title, Author, Publisher, Category, ISBN, Quantity)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title, author, publisher, category, isbn, qty))

    conn.commit()
    conn.close()
    print("[SEED] Database seeded with sample data.")
    print("  Admin login: admin@library.com / admin123")
    print("  Member login: alice@example.com / member123")


if __name__ == '__main__':
    seed()
