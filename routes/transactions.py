"""Transaction (Issue/Return) routes."""
from flask import Blueprint, request, jsonify, session
from database.db import query_db, execute_db, get_db
from middleware.auth import login_required, admin_required
from datetime import date, timedelta

transactions_bp = Blueprint('transactions', __name__, url_prefix='/api/transactions')

LOAN_PERIOD_DAYS = 14
FINE_PER_DAY = 2.0  # ₹2 per day


@transactions_bp.route('/issue', methods=['POST'])
@admin_required
def issue_book():
    data = request.get_json()
    member_id = data.get('memberId')
    book_id = data.get('bookId')

    if not member_id or not book_id:
        return jsonify({'error': 'Member ID and Book ID are required'}), 400

    # Validate member
    member = query_db('SELECT * FROM Members WHERE MemberID = ?', (member_id,), one=True)
    if not member:
        return jsonify({'error': 'Invalid Member ID'}), 404
    if member['Role'] == 'admin':
        return jsonify({'error': 'Cannot issue books to admin account'}), 400

    # Validate book
    book = query_db('SELECT * FROM Books WHERE BookID = ?', (book_id,), one=True)
    if not book:
        return jsonify({'error': 'Invalid Book ID'}), 404

    available = book['Quantity'] - book['IssuedCount']
    if available <= 0:
        return jsonify({'error': 'Book not available — all copies are issued'}), 400

    # Check if already issued to this member
    already = query_db(
        "SELECT * FROM Transactions WHERE MemberID = ? AND BookID = ? AND Status = 'issued'",
        (member_id, book_id), one=True
    )
    if already:
        return jsonify({'error': 'This book is already issued to this member'}), 400

    # Issue
    issue_date = date.today().isoformat()
    due_date = (date.today() + timedelta(days=LOAN_PERIOD_DAYS)).isoformat()

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO Transactions (MemberID, BookID, IssueDate, DueDate, Status) VALUES (?, ?, ?, ?, 'issued')",
            (member_id, book_id, issue_date, due_date)
        )
        conn.execute("UPDATE Books SET IssuedCount = IssuedCount + 1 WHERE BookID = ?", (book_id,))
        conn.execute("UPDATE Members SET BooksIssuedCount = BooksIssuedCount + 1 WHERE MemberID = ?", (member_id,))
        conn.commit()
    finally:
        conn.close()

    return jsonify({
        'message': f"Book '{book['Title']}' issued to {member['Name']}",
        'dueDate': due_date
    }), 201


@transactions_bp.route('/return', methods=['POST'])
@admin_required
def return_book():
    data = request.get_json()
    member_id = data.get('memberId')
    book_id = data.get('bookId')

    if not member_id or not book_id:
        return jsonify({'error': 'Member ID and Book ID are required'}), 400

    # Find the issued transaction
    txn = query_db(
        "SELECT * FROM Transactions WHERE MemberID = ? AND BookID = ? AND Status = 'issued'",
        (member_id, book_id), one=True
    )
    if not txn:
        return jsonify({'error': 'No active issue record found for this book and member'}), 404

    return_date = date.today()
    due_date = date.fromisoformat(txn['DueDate'])
    fine = 0.0

    if return_date > due_date:
        overdue_days = (return_date - due_date).days
        fine = overdue_days * FINE_PER_DAY

    conn = get_db()
    try:
        conn.execute(
            "UPDATE Transactions SET ReturnDate = ?, Fine = ?, Status = 'returned' WHERE TransactionID = ?",
            (return_date.isoformat(), fine, txn['TransactionID'])
        )
        conn.execute("UPDATE Books SET IssuedCount = IssuedCount - 1 WHERE BookID = ?", (book_id,))
        conn.execute("UPDATE Members SET BooksIssuedCount = BooksIssuedCount - 1 WHERE MemberID = ?", (member_id,))
        conn.commit()
    finally:
        conn.close()

    member = query_db('SELECT Name FROM Members WHERE MemberID = ?', (member_id,), one=True)
    book = query_db('SELECT Title FROM Books WHERE BookID = ?', (book_id,), one=True)

    return jsonify({
        'message': f"Book '{book['Title']}' returned by {member['Name']}",
        'fine': fine,
        'overdueDays': max(0, (return_date - due_date).days) if return_date > due_date else 0
    })


@transactions_bp.route('', methods=['GET'])
@login_required
def list_transactions():
    status = request.args.get('status', '').strip()
    member_filter = request.args.get('memberId', '').strip()

    query = """
        SELECT t.*, b.Title as BookTitle, b.Author as BookAuthor, m.Name as MemberName
        FROM Transactions t
        JOIN Books b ON t.BookID = b.BookID
        JOIN Members m ON t.MemberID = m.MemberID
        WHERE 1=1
    """
    params = []

    # Non-admin can only see their own transactions
    if session.get('role') != 'admin':
        query += ' AND t.MemberID = ?'
        params.append(session['user_id'])
    elif member_filter:
        query += ' AND t.MemberID = ?'
        params.append(int(member_filter))

    if status:
        query += ' AND t.Status = ?'
        params.append(status)

    query += ' ORDER BY t.IssueDate DESC'
    transactions = query_db(query, params)
    return jsonify({'transactions': transactions})


@transactions_bp.route('/overdue', methods=['GET'])
@login_required
def overdue_books():
    today = date.today().isoformat()
    query = """
        SELECT t.*, b.Title as BookTitle, b.Author as BookAuthor, m.Name as MemberName, m.Email as MemberEmail
        FROM Transactions t
        JOIN Books b ON t.BookID = b.BookID
        JOIN Members m ON t.MemberID = m.MemberID
        WHERE t.Status = 'issued' AND t.DueDate < ?
    """
    params = [today]

    if session.get('role') != 'admin':
        query += ' AND t.MemberID = ?'
        params.append(session['user_id'])

    query += ' ORDER BY t.DueDate ASC'
    overdue = query_db(query, params)

    # Calculate current fine for each
    for item in overdue:
        due = date.fromisoformat(item['DueDate'])
        days = (date.today() - due).days
        item['overdueDays'] = days
        item['currentFine'] = days * FINE_PER_DAY

    return jsonify({'overdue': overdue})
