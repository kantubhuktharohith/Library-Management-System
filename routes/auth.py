"""Authentication routes."""
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import query_db, execute_db
from datetime import date, timedelta

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    user = query_db('SELECT * FROM Members WHERE LOWER(Email) = ?', (email,), one=True)
    if not user or not check_password_hash(user['PasswordHash'], password):
        return jsonify({'error': 'Invalid email or password'}), 401

    session['user_id'] = user['MemberID']
    session['role'] = user['Role']
    session['name'] = user['Name']
    session['email'] = user['Email']

    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user['MemberID'],
            'name': user['Name'],
            'email': user['Email'],
            'role': user['Role'],
            'membershipType': user['MembershipType']
        }
    })


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    password = data.get('password', '')
    membership_type = data.get('membershipType', 'Student')

    if not all([name, email, phone, password]):
        return jsonify({'error': 'All fields are required'}), 400

    existing = query_db('SELECT MemberID FROM Members WHERE LOWER(Email) = ?', (email,), one=True)
    if existing:
        return jsonify({'error': 'Email already registered'}), 409

    password_hash = generate_password_hash(password)
    join_date = date.today().isoformat()
    expiry_date = (date.today() + timedelta(days=365)).isoformat()

    member_id = execute_db("""
        INSERT INTO Members (Name, Email, Phone, MembershipType, JoinDate, ExpiryDate, PasswordHash, Role)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'member')
    """, (name, email, phone, membership_type, join_date, expiry_date, password_hash))

    return jsonify({'message': 'Registration successful', 'memberId': member_id}), 201


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})


@auth_bp.route('/me', methods=['GET'])
def me():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    user = query_db('SELECT * FROM Members WHERE MemberID = ?', (session['user_id'],), one=True)
    if not user:
        session.clear()
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'user': {
            'id': user['MemberID'],
            'name': user['Name'],
            'email': user['Email'],
            'role': user['Role'],
            'phone': user['Phone'],
            'membershipType': user['MembershipType'],
            'joinDate': user['JoinDate'],
            'expiryDate': user['ExpiryDate'],
            'booksIssued': user['BooksIssuedCount']
        }
    })
