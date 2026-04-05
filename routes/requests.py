"""Book Request routes — Members request books, Admin approves/rejects."""
from flask import Blueprint, request, jsonify, session
from database.db import query_db, execute_db, get_db
from middleware.auth import login_required, admin_required
from datetime import date, timedelta

requests_bp = Blueprint('requests', __name__, url_prefix='/api/requests')


@requests_bp.route('', methods=['POST'])
@login_required
def create_request():
    """Member requests a book."""
    data = request.get_json()
    book_id = data.get('bookId')
    message = data.get('message', '').strip()

    if not book_id:
        return jsonify({'error': 'Book ID is required'}), 400

    # Validate book exists
    book = query_db('SELECT * FROM Books WHERE BookID = ?', (book_id,), one=True)
    if not book:
        return jsonify({'error': 'Book not found'}), 404

    member_id = session['user_id']

    # Check if already has a pending request for this book
    existing = query_db(
        "SELECT * FROM BookRequests WHERE MemberID = ? AND BookID = ? AND Status = 'pending'",
        (member_id, book_id), one=True
    )
    if existing:
        return jsonify({'error': 'You already have a pending request for this book'}), 400

    # Check if book is already issued to this member
    issued = query_db(
        "SELECT * FROM Transactions WHERE MemberID = ? AND BookID = ? AND Status = 'issued'",
        (member_id, book_id), one=True
    )
    if issued:
        return jsonify({'error': 'This book is already issued to you'}), 400

    request_id = execute_db("""
        INSERT INTO BookRequests (MemberID, BookID, Message, Status)
        VALUES (?, ?, ?, 'pending')
    """, (member_id, book_id, message))

    return jsonify({
        'message': f"Request submitted for '{book['Title']}'. The admin will review it shortly.",
        'requestId': request_id
    }), 201


@requests_bp.route('', methods=['GET'])
@login_required
def list_requests():
    """List requests — admin sees all, member sees own."""
    status = request.args.get('status', '').strip()

    query = """
        SELECT r.*, b.Title as BookTitle, b.Author as BookAuthor,
               b.Quantity as BookQuantity, b.IssuedCount as BookIssuedCount,
               m.Name as MemberName, m.Email as MemberEmail
        FROM BookRequests r
        JOIN Books b ON r.BookID = b.BookID
        JOIN Members m ON r.MemberID = m.MemberID
        WHERE 1=1
    """
    params = []

    # Non-admin can only see their own requests
    if session.get('role') != 'admin':
        query += ' AND r.MemberID = ?'
        params.append(session['user_id'])

    if status:
        query += ' AND r.Status = ?'
        params.append(status)

    query += ' ORDER BY r.RequestDate DESC, r.RequestID DESC'
    requests_list = query_db(query, params)
    return jsonify({'requests': requests_list})


@requests_bp.route('/<int:request_id>/approve', methods=['POST'])
@admin_required
def approve_request(request_id):
    """Admin approves a request and issues the book."""
    req = query_db('SELECT * FROM BookRequests WHERE RequestID = ?', (request_id,), one=True)
    if not req:
        return jsonify({'error': 'Request not found'}), 404

    if req['Status'] != 'pending':
        return jsonify({'error': f"Request is already {req['Status']}"}), 400

    data = request.get_json() or {}
    admin_response = data.get('response', 'Approved by admin').strip()

    # Check book availability
    book = query_db('SELECT * FROM Books WHERE BookID = ?', (req['BookID'],), one=True)
    available = book['Quantity'] - book['IssuedCount']
    if available <= 0:
        return jsonify({'error': 'Book not available — all copies are currently issued'}), 400

    # Check if already issued to this member
    already = query_db(
        "SELECT * FROM Transactions WHERE MemberID = ? AND BookID = ? AND Status = 'issued'",
        (req['MemberID'], req['BookID']), one=True
    )
    if already:
        # Just approve the request without re-issuing
        execute_db("""
            UPDATE BookRequests SET Status = 'approved', AdminResponse = ?, ResponseDate = ?
            WHERE RequestID = ?
        """, ('Book is already issued to you', date.today().isoformat(), request_id))
        return jsonify({'message': 'Request approved (book already issued to member)'})

    # Issue the book
    issue_date = date.today().isoformat()
    due_date = (date.today() + timedelta(days=14)).isoformat()

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO Transactions (MemberID, BookID, IssueDate, DueDate, Status) VALUES (?, ?, ?, ?, 'issued')",
            (req['MemberID'], req['BookID'], issue_date, due_date)
        )
        conn.execute("UPDATE Books SET IssuedCount = IssuedCount + 1 WHERE BookID = ?", (req['BookID'],))
        conn.execute("UPDATE Members SET BooksIssuedCount = BooksIssuedCount + 1 WHERE MemberID = ?", (req['MemberID'],))
        conn.execute("""
            UPDATE BookRequests SET Status = 'approved', AdminResponse = ?, ResponseDate = ?
            WHERE RequestID = ?
        """, (admin_response, date.today().isoformat(), request_id))
        conn.commit()
    finally:
        conn.close()

    member = query_db('SELECT Name FROM Members WHERE MemberID = ?', (req['MemberID'],), one=True)

    return jsonify({
        'message': f"Request approved! '{book['Title']}' has been issued to {member['Name']} (due: {due_date})"
    })


@requests_bp.route('/<int:request_id>/reject', methods=['POST'])
@admin_required
def reject_request(request_id):
    """Admin rejects a request."""
    req = query_db('SELECT * FROM BookRequests WHERE RequestID = ?', (request_id,), one=True)
    if not req:
        return jsonify({'error': 'Request not found'}), 404

    if req['Status'] != 'pending':
        return jsonify({'error': f"Request is already {req['Status']}"}), 400

    data = request.get_json() or {}
    admin_response = data.get('response', 'Request denied by admin').strip()

    execute_db("""
        UPDATE BookRequests SET Status = 'rejected', AdminResponse = ?, ResponseDate = ?
        WHERE RequestID = ?
    """, (admin_response, date.today().isoformat(), request_id))

    book = query_db('SELECT Title FROM Books WHERE BookID = ?', (req['BookID'],), one=True)

    return jsonify({'message': f"Request for '{book['Title']}' has been rejected"})


@requests_bp.route('/<int:request_id>', methods=['DELETE'])
@login_required
def cancel_request(request_id):
    """Member cancels their own pending request."""
    req = query_db('SELECT * FROM BookRequests WHERE RequestID = ?', (request_id,), one=True)
    if not req:
        return jsonify({'error': 'Request not found'}), 404

    # Only own requests, and only pending ones
    if session.get('role') != 'admin' and req['MemberID'] != session['user_id']:
        return jsonify({'error': 'Access denied'}), 403

    if req['Status'] != 'pending':
        return jsonify({'error': 'Can only cancel pending requests'}), 400

    execute_db('DELETE FROM BookRequests WHERE RequestID = ?', (request_id,))
    return jsonify({'message': 'Request cancelled'})


@requests_bp.route('/count', methods=['GET'])
@admin_required
def pending_count():
    """Get count of pending requests for badge display."""
    count = query_db("SELECT COUNT(*) as count FROM BookRequests WHERE Status = 'pending'", one=True)
    return jsonify({'count': count['count']})
