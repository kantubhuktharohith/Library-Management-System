-- Library Management System - Database Schema

CREATE TABLE IF NOT EXISTS Books (
    BookID INTEGER PRIMARY KEY AUTOINCREMENT,
    Title VARCHAR(100) NOT NULL,
    Author VARCHAR(100) NOT NULL,
    Publisher VARCHAR(100) DEFAULT '',
    Category VARCHAR(50) DEFAULT 'General',
    ISBN VARCHAR(20) DEFAULT '',
    Quantity INTEGER NOT NULL DEFAULT 1,
    IssuedCount INTEGER NOT NULL DEFAULT 0,
    AddedDate DATE NOT NULL DEFAULT (DATE('now')),
    Description TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS Members (
    MemberID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name VARCHAR(50) NOT NULL,
    Email VARCHAR(50) UNIQUE NOT NULL,
    Phone VARCHAR(15) NOT NULL,
    MembershipType VARCHAR(20) NOT NULL DEFAULT 'Student',
    JoinDate DATE NOT NULL DEFAULT (DATE('now')),
    ExpiryDate DATE NOT NULL,
    BooksIssuedCount INTEGER NOT NULL DEFAULT 0,
    PasswordHash VARCHAR(255) NOT NULL,
    Role VARCHAR(10) NOT NULL DEFAULT 'member'
);

CREATE TABLE IF NOT EXISTS Transactions (
    TransactionID INTEGER PRIMARY KEY AUTOINCREMENT,
    MemberID INTEGER NOT NULL,
    BookID INTEGER NOT NULL,
    IssueDate DATE NOT NULL DEFAULT (DATE('now')),
    DueDate DATE NOT NULL,
    ReturnDate DATE DEFAULT NULL,
    Fine REAL NOT NULL DEFAULT 0.0,
    Status VARCHAR(10) NOT NULL DEFAULT 'issued',
    FOREIGN KEY (MemberID) REFERENCES Members(MemberID),
    FOREIGN KEY (BookID) REFERENCES Books(BookID)
);

CREATE TABLE IF NOT EXISTS BookRequests (
    RequestID INTEGER PRIMARY KEY AUTOINCREMENT,
    MemberID INTEGER NOT NULL,
    BookID INTEGER NOT NULL,
    RequestDate DATE NOT NULL DEFAULT (DATE('now')),
    Message TEXT DEFAULT '',
    Status VARCHAR(15) NOT NULL DEFAULT 'pending',
    AdminResponse TEXT DEFAULT '',
    ResponseDate DATE DEFAULT NULL,
    FOREIGN KEY (MemberID) REFERENCES Members(MemberID),
    FOREIGN KEY (BookID) REFERENCES Books(BookID)
);

-- Index for faster searches
CREATE INDEX IF NOT EXISTS idx_books_title ON Books(Title);
CREATE INDEX IF NOT EXISTS idx_books_author ON Books(Author);
CREATE INDEX IF NOT EXISTS idx_members_email ON Members(Email);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON Transactions(Status);
CREATE INDEX IF NOT EXISTS idx_transactions_member ON Transactions(MemberID);
CREATE INDEX IF NOT EXISTS idx_requests_status ON BookRequests(Status);
CREATE INDEX IF NOT EXISTS idx_requests_member ON BookRequests(MemberID);
