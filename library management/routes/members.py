"""Member management routes."""
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash
from database.db import query_db, execute_db
from middleware.auth import login_required, admin_required
from datetime import date, timedelta

members_bp = Blueprint('members', __name__, url_prefix='/api/members')


@members_bp.route('', methods=['GET'])
@admin_required
def list_members():
    search = request.args.get('search', '').strip()
    query = "SELECT MemberID, Name, Email, Phone, MembershipType, JoinDate, ExpiryDate, BooksIssuedCount, Role FROM Members WHERE Role != 'admin'"
    params = []

    if search:
        query += ' AND (Name LIKE ? OR Email LIKE ? OR Phone LIKE ?)'
        like = f'%{search}%'
        params.extend([like, like, like])

    query += ' ORDER BY Name ASC'
    members = query_db(query, params)
    return jsonify({'members': members})


@members_bp.route('/<int:member_id>', methods=['GET'])
@login_required
def get_member(member_id):
    # Members can only view their own profile, admins can view any
    if session.get('role') != 'admin' and session.get('user_id') != member_id:
        return jsonify({'error': 'Access denied'}), 403

    member = query_db(
        'SELECT MemberID, Name, Email, Phone, MembershipType, JoinDate, ExpiryDate, BooksIssuedCount, Role FROM Members WHERE MemberID = ?',
        (member_id,), one=True
    )
    if not member:
        return jsonify({'error': 'Member not found'}), 404
    return jsonify({'member': member})


@members_bp.route('', methods=['POST'])
@admin_required
def add_member():
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    membership_type = data.get('membershipType', 'Student')
    password = data.get('password', 'member123')

    if not all([name, email, phone]):
        return jsonify({'error': 'Name, email, and phone are required'}), 400

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

    return jsonify({'message': 'Member added successfully', 'memberId': member_id}), 201


@members_bp.route('/<int:member_id>', methods=['PUT'])
@admin_required
def update_member(member_id):
    member = query_db('SELECT * FROM Members WHERE MemberID = ?', (member_id,), one=True)
    if not member:
        return jsonify({'error': 'Member not found'}), 404

    data = request.get_json()
    name = data.get('name', member['Name']).strip()
    phone = data.get('phone', member['Phone']).strip()
    membership_type = data.get('membershipType', member['MembershipType'])
    expiry_date = data.get('expiryDate', member['ExpiryDate'])

    execute_db("""
        UPDATE Members SET Name=?, Phone=?, MembershipType=?, ExpiryDate=?
        WHERE MemberID=?
    """, (name, phone, membership_type, expiry_date, member_id))

    return jsonify({'message': 'Member updated successfully'})


@members_bp.route('/<int:member_id>', methods=['DELETE'])
@admin_required
def delete_member(member_id):
    member = query_db('SELECT * FROM Members WHERE MemberID = ?', (member_id,), one=True)
    if not member:
        return jsonify({'error': 'Member not found'}), 404

    if member['Role'] == 'admin':
        return jsonify({'error': 'Cannot delete admin account'}), 400

    # Check if member has books issued
    if member['BooksIssuedCount'] > 0:
        return jsonify({'error': 'Cannot delete member with books currently issued'}), 400

    execute_db('DELETE FROM Transactions WHERE MemberID = ?', (member_id,))
    execute_db('DELETE FROM Members WHERE MemberID = ?', (member_id,))
    return jsonify({'message': 'Member deleted successfully'})
