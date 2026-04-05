"""Report routes for dashboard and analytics."""
from flask import Blueprint, jsonify, session
from database.db import query_db
from middleware.auth import login_required, admin_required
from datetime import date

reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')


@reports_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    today = date.today().isoformat()

    total_books = query_db('SELECT COUNT(*) as count FROM Books', one=True)['count']
    total_copies = query_db('SELECT COALESCE(SUM(Quantity), 0) as count FROM Books', one=True)['count']
    total_members = query_db("SELECT COUNT(*) as count FROM Members WHERE Role != 'admin'", one=True)['count']
    total_issued = query_db("SELECT COUNT(*) as count FROM Transactions WHERE Status = 'issued'", one=True)['count']
    total_overdue = query_db(
        "SELECT COUNT(*) as count FROM Transactions WHERE Status = 'issued' AND DueDate < ?",
        (today,), one=True
    )['count']
    total_returned = query_db("SELECT COUNT(*) as count FROM Transactions WHERE Status = 'returned'", one=True)['count']
    total_fines = query_db("SELECT COALESCE(SUM(Fine), 0) as total FROM Transactions WHERE Fine > 0", one=True)['total']

    # Recent transactions
    recent = query_db("""
        SELECT t.*, b.Title as BookTitle, m.Name as MemberName
        FROM Transactions t
        JOIN Books b ON t.BookID = b.BookID
        JOIN Members m ON t.MemberID = m.MemberID
        ORDER BY t.TransactionID DESC LIMIT 10
    """)

    # Popular books
    popular = query_db("""
        SELECT b.BookID, b.Title, b.Author, COUNT(t.TransactionID) as timesIssued
        FROM Books b
        LEFT JOIN Transactions t ON b.BookID = t.BookID
        GROUP BY b.BookID
        ORDER BY timesIssued DESC
        LIMIT 5
    """)

    # Category distribution
    categories = query_db("""
        SELECT Category, COUNT(*) as count, COALESCE(SUM(Quantity), 0) as totalCopies
        FROM Books GROUP BY Category ORDER BY count DESC
    """)

    return jsonify({
        'stats': {
            'totalBooks': total_books,
            'totalCopies': total_copies,
            'totalMembers': total_members,
            'totalIssued': total_issued,
            'totalOverdue': total_overdue,
            'totalReturned': total_returned,
            'totalFines': total_fines
        },
        'recentTransactions': recent,
        'popularBooks': popular,
        'categories': categories
    })


@reports_bp.route('/issued', methods=['GET'])
@admin_required
def issued_report():
    transactions = query_db("""
        SELECT t.*, b.Title as BookTitle, b.Author as BookAuthor,
               m.Name as MemberName, m.Email as MemberEmail
        FROM Transactions t
        JOIN Books b ON t.BookID = b.BookID
        JOIN Members m ON t.MemberID = m.MemberID
        WHERE t.Status = 'issued'
        ORDER BY t.IssueDate DESC
    """)
    return jsonify({'report': transactions})


@reports_bp.route('/overdue', methods=['GET'])
@admin_required
def overdue_report():
    today = date.today().isoformat()
    transactions = query_db("""
        SELECT t.*, b.Title as BookTitle, b.Author as BookAuthor,
               m.Name as MemberName, m.Email as MemberEmail, m.Phone as MemberPhone
        FROM Transactions t
        JOIN Books b ON t.BookID = b.BookID
        JOIN Members m ON t.MemberID = m.MemberID
        WHERE t.Status = 'issued' AND t.DueDate < ?
        ORDER BY t.DueDate ASC
    """, (today,))

    for item in transactions:
        due = date.fromisoformat(item['DueDate'])
        days = (date.today() - due).days
        item['overdueDays'] = days
        item['currentFine'] = days * 2.0

    return jsonify({'report': transactions})


@reports_bp.route('/activity', methods=['GET'])
@admin_required
def activity_report():
    members = query_db("""
        SELECT m.MemberID, m.Name, m.Email, m.MembershipType, m.BooksIssuedCount,
               COUNT(t.TransactionID) as totalTransactions,
               SUM(CASE WHEN t.Status = 'issued' THEN 1 ELSE 0 END) as currentlyIssued,
               SUM(CASE WHEN t.Status = 'returned' THEN 1 ELSE 0 END) as totalReturned,
               COALESCE(SUM(t.Fine), 0) as totalFines
        FROM Members m
        LEFT JOIN Transactions t ON m.MemberID = t.MemberID
        WHERE m.Role != 'admin'
        GROUP BY m.MemberID
        ORDER BY totalTransactions DESC
    """)
    return jsonify({'report': members})
