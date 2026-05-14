# LibraryMS — Library Management System

A simple full-stack web application built with **Flask** (backend) and **vanilla HTML/CSS/JS** (frontend).

## Problem Statement
Libraries in schools and universities often struggle to efficiently manage book collections, member data, and loan processes. Without an organized system, staff find it difficult to track book availability, borrowing history, and return status — leading to lost books, unmanaged member data, and slow service. This application provides a centralized CRUD interface to manage all library operations.

## Entities
| Entity | Fields |
|--------|--------|
| Book | id, title, author, year, stock |
| Member | id, name, email, phone |
| Loan | id, book_id, member_id, borrow_date, return_date, status |

> ⚠ No database used — all data is stored in-memory as Python lists/dicts (JSON-like).

## Features
- **Books CRUD** — Add, view, edit, delete books with stock tracking
- **Members CRUD** — Register, view, edit, delete library members
- **Borrow Book** — Multi-entity: links Member + Book, auto-decrements stock
- **Return Book** — Multi-entity: marks loan returned, auto-increments stock
- **Active Loans** — View all ongoing loans with days-borrowed indicator
- **Loan History** — Full record with status filter (all/active/returned)

## Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the Flask development server
python app.py

# 3. Open your browser
http://localhost:5000
```

## Project Structure
```
libraryms/
├── app.py              ← Flask backend (API routes + data)
├── requirements.txt
└── templates/
    └── index.html      ← Single-page frontend (HTML + CSS + JS)
```

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/books | Get all books |
| POST | /api/books | Create book |
| PUT | /api/books/:id | Update book |
| DELETE | /api/books/:id | Delete book |
| GET | /api/members | Get all members |
| POST | /api/members | Create member |
| PUT | /api/members/:id | Update member |
| DELETE | /api/members/:id | Delete member |
| GET | /api/loans | Get all loans (enriched) |
| POST | /api/loans | Create loan (borrow) |
| PUT | /api/loans/:id/return | Return a book |
| DELETE | /api/loans/:id | Delete loan record |
