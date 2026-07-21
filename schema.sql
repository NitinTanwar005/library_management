-- ============================================================
--  Library Management System - Database Schema
--  Database: MySQL 8.0+
-- ============================================================

CREATE DATABASE IF NOT EXISTS library_db
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE library_db;

-- ------------------------------------------------------------
-- Table: users  (staff / librarian login accounts)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id      INT AUTO_INCREMENT PRIMARY KEY,
    full_name    VARCHAR(100)  NOT NULL,
    username     VARCHAR(50)   NOT NULL UNIQUE,
    password     VARCHAR(255)  NOT NULL,        -- stored as SHA-256 hash
    role         VARCHAR(20)   NOT NULL DEFAULT 'Librarian',
    email        VARCHAR(100),
    created_at   TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Table: books
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS books (
    book_id            VARCHAR(20)  PRIMARY KEY,
    title              VARCHAR(200) NOT NULL,
    author             VARCHAR(150) NOT NULL,
    publisher          VARCHAR(150),
    category           VARCHAR(80),
    isbn               VARCHAR(30)  UNIQUE,
    total_copies       INT NOT NULL DEFAULT 1,
    available_copies   INT NOT NULL DEFAULT 1,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (available_copies >= 0 AND available_copies <= total_copies)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Table: members  (library members / borrowers)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS members (
    member_id     VARCHAR(20)  PRIMARY KEY,
    name          VARCHAR(120) NOT NULL,
    roll_no       VARCHAR(50),                  -- Roll No / Employee No
    email         VARCHAR(100),
    phone         VARCHAR(20),
    address       VARCHAR(255),
    joined_on     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Table: issued_books  (issue / return transactions)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS issued_books (
    issue_id      INT AUTO_INCREMENT PRIMARY KEY,
    book_id       VARCHAR(20) NOT NULL,
    member_id     VARCHAR(20) NOT NULL,
    issue_date    DATE NOT NULL,
    due_date      DATE NOT NULL,
    return_date   DATE NULL,
    fine          DECIMAL(8,2) NOT NULL DEFAULT 0.00,
    status        VARCHAR(20)  NOT NULL DEFAULT 'Issued',   -- Issued / Returned
    FOREIGN KEY (book_id)   REFERENCES books(book_id)   ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES members(member_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Seed data: default administrator account
-- Username: admin   Password: admin123
-- (password is stored as SHA-256 hash by the application, this
--  seed row uses the hash of "admin123")
-- ------------------------------------------------------------
INSERT INTO users (full_name, username, password, role, email)
VALUES (
    'System Administrator',
    'admin',
    '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', -- sha256('admin123')
    'Admin',
    'admin@library.local'
) ON DUPLICATE KEY UPDATE username = username;
