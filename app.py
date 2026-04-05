"""Library Management System - Flask Application."""
import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from database.db import init_db

# Create Flask app
app = Flask(__name__, static_folder='public', static_url_path='')
app.secret_key = 'library-management-secret-key-2026'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True

CORS(app, supports_credentials=True)

# Initialize database
init_db()

# Register blueprints
from routes.auth import auth_bp
from routes.books import books_bp
from routes.members import members_bp
from routes.transactions import transactions_bp
from routes.reports import reports_bp
from routes.requests import requests_bp

app.register_blueprint(auth_bp)
app.register_blueprint(books_bp)
app.register_blueprint(members_bp)
app.register_blueprint(transactions_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(requests_bp)


# Serve frontend pages
@app.route('/')
def index():
    return send_from_directory('public', 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('public', filename)


if __name__ == '__main__':
    # Seed database if empty
    from database.db import query_db
    books = query_db('SELECT COUNT(*) as count FROM Books')
    if books[0]['count'] == 0:
        from database.seed import seed
        seed()

    print("\n📚 Library Management System")
    print("   http://localhost:5000")
    print("   Admin: admin@library.com / admin123")
    print("   Member: alice@example.com / member123\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
