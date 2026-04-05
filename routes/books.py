"""Book management routes."""
from flask import Blueprint, request, jsonify
from database.db import query_db, execute_db
from middleware.auth import login_required, admin_required

books_bp = Blueprint('books', __name__, url_prefix='/api/books')


@books_bp.route('', methods=['GET'])
@login_required
def list_books():
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()

    query = 'SELECT * FROM Books WHERE 1=1'
    params = []

    if search:
        query += ' AND (Title LIKE ? OR Author LIKE ? OR ISBN LIKE ?)'
        like = f'%{search}%'
        params.extend([like, like, like])

    if category:
        query += ' AND Category = ?'
        params.append(category)

    query += ' ORDER BY Title ASC'
    books = query_db(query, params)
    return jsonify({'books': books})


@books_bp.route('/categories', methods=['GET'])
@login_required
def get_categories():
    cats = query_db('SELECT DISTINCT Category FROM Books ORDER BY Category ASC')
    return jsonify({'categories': [c['Category'] for c in cats]})


@books_bp.route('/<int:book_id>', methods=['GET'])
@login_required
def get_book(book_id):
    book = query_db('SELECT * FROM Books WHERE BookID = ?', (book_id,), one=True)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    return jsonify({'book': book})


@books_bp.route('', methods=['POST'])
@admin_required
def add_book():
    data = request.get_json()
    title = data.get('title', '').strip()
    author = data.get('author', '').strip()
    publisher = data.get('publisher', '').strip()
    category = data.get('category', 'General').strip()
    isbn = data.get('isbn', '').strip()
    quantity = data.get('quantity', 1)
    description = data.get('description', '').strip()

    if not title or not author:
        return jsonify({'error': 'Title and Author are required'}), 400

    try:
        quantity = int(quantity)
        if quantity < 1:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': 'Quantity must be a positive integer'}), 400

    book_id = execute_db("""
        INSERT INTO Books (Title, Author, Publisher, Category, ISBN, Quantity, Description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (title, author, publisher, category, isbn, quantity, description))

    return jsonify({'message': 'Book added successfully', 'bookId': book_id}), 201


@books_bp.route('/<int:book_id>', methods=['PUT'])
@admin_required
def update_book(book_id):
    book = query_db('SELECT * FROM Books WHERE BookID = ?', (book_id,), one=True)
    if not book:
        return jsonify({'error': 'Book not found'}), 404

    data = request.get_json()
    title = data.get('title', book['Title']).strip()
    author = data.get('author', book['Author']).strip()
    publisher = data.get('publisher', book['Publisher']).strip()
    category = data.get('category', book['Category']).strip()
    isbn = data.get('isbn', book['ISBN']).strip()
    quantity = data.get('quantity', book['Quantity'])
    description = data.get('description', book['Description']).strip()

    try:
        quantity = int(quantity)
        if quantity < 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': 'Quantity must be a non-negative integer'}), 400

    execute_db("""
        UPDATE Books SET Title=?, Author=?, Publisher=?, Category=?, ISBN=?, Quantity=?, Description=?
        WHERE BookID=?
    """, (title, author, publisher, category, isbn, quantity, description, book_id))

    return jsonify({'message': 'Book updated successfully'})


@books_bp.route('/<int:book_id>', methods=['DELETE'])
@admin_required
def delete_book(book_id):
    book = query_db('SELECT * FROM Books WHERE BookID = ?', (book_id,), one=True)
    if not book:
        return jsonify({'error': 'Book not found'}), 404

    # Check if book is currently issued
    issued = query_db(
        "SELECT COUNT(*) as cnt FROM Transactions WHERE BookID = ? AND Status = 'issued'",
        (book_id,), one=True
    )
    if issued and issued['cnt'] > 0:
        return jsonify({'error': 'Cannot delete book that is currently issued'}), 400

    execute_db('DELETE FROM Books WHERE BookID = ?', (book_id,))
    return jsonify({'message': 'Book deleted successfully'})
