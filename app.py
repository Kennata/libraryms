from flask import Flask, jsonify, request, render_template
from datetime import date
import copy

app = Flask(__name__)

# ─── In-memory "database" ───────────────────────────────────────────────────

BOOKS = [
    {"id": "B001", "title": "Clean Code", "author": "Robert C. Martin", "year": 2008, "stock": 5},
    {"id": "B002", "title": "The Pragmatic Programmer", "author": "Hunt & Thomas", "year": 1999, "stock": 2},
    {"id": "B003", "title": "Design Patterns", "author": "Gang of Four", "year": 1994, "stock": 0},
    {"id": "B004", "title": "Refactoring", "author": "Martin Fowler", "year": 2018, "stock": 3},
    {"id": "B005", "title": "Structure and Interpretation of Computer Programs", "author": "Abelson & Sussman", "year": 1996, "stock": 1},
]

MEMBERS = [
    {"id": "M001", "name": "Andi Pratama", "email": "andi@example.com", "phone": "081234567890"},
    {"id": "M002", "name": "Budi Santoso", "email": "budi@example.com", "phone": "082345678901"},
    {"id": "M003", "name": "Citra Dewi", "email": "citra@example.com", "phone": "083456789012"},
]

LOANS = [
    {"id": "L001", "book_id": "B001", "member_id": "M001", "borrow_date": "2025-04-10", "return_date": None, "status": "active"},
    {"id": "L002", "book_id": "B002", "member_id": "M002", "borrow_date": "2025-04-01", "return_date": "2025-04-15", "status": "returned"},
    {"id": "L003", "book_id": "B003", "member_id": "M003", "borrow_date": "2025-04-20", "return_date": None, "status": "active"},
]

def next_id(collection, prefix):
    nums = [int(item["id"][len(prefix):]) for item in collection]
    return f"{prefix}{max(nums)+1:03d}" if nums else f"{prefix}001"

def find(collection, item_id):
    return next((x for x in collection if x["id"] == item_id), None)

# ─── Frontend ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

# ─── Books API ───────────────────────────────────────────────────────────────

@app.route("/api/books", methods=["GET"])
def get_books():
    return jsonify(BOOKS)

@app.route("/api/books/<book_id>", methods=["GET"])
def get_book(book_id):
    book = find(BOOKS, book_id)
    if not book: return jsonify({"error": "Book not found"}), 404
    return jsonify(book)

@app.route("/api/books", methods=["POST"])
def create_book():
    data = request.json
    if not data.get("title") or not data.get("author"):
        return jsonify({"error": "title and author are required"}), 400
    book = {
        "id": next_id(BOOKS, "B"),
        "title": data["title"],
        "author": data["author"],
        "year": data.get("year", date.today().year),
        "stock": int(data.get("stock", 1)),
    }
    BOOKS.append(book)
    return jsonify(book), 201

@app.route("/api/books/<book_id>", methods=["PUT"])
def update_book(book_id):
    book = find(BOOKS, book_id)
    if not book: return jsonify({"error": "Book not found"}), 404
    data = request.json
    book.update({
        "title": data.get("title", book["title"]),
        "author": data.get("author", book["author"]),
        "year": data.get("year", book["year"]),
        "stock": int(data.get("stock", book["stock"])),
    })
    return jsonify(book)

@app.route("/api/books/<book_id>", methods=["DELETE"])
def delete_book(book_id):
    book = find(BOOKS, book_id)
    if not book: return jsonify({"error": "Book not found"}), 404
    active = [l for l in LOANS if l["book_id"] == book_id and l["status"] == "active"]
    if active: return jsonify({"error": "Cannot delete book with active loans"}), 400
    BOOKS.remove(book)
    return jsonify({"message": "Book deleted"})

# ─── Members API ─────────────────────────────────────────────────────────────

@app.route("/api/members", methods=["GET"])
def get_members():
    return jsonify(MEMBERS)

@app.route("/api/members/<member_id>", methods=["GET"])
def get_member(member_id):
    member = find(MEMBERS, member_id)
    if not member: return jsonify({"error": "Member not found"}), 404
    return jsonify(member)

@app.route("/api/members", methods=["POST"])
def create_member():
    data = request.json
    if not data.get("name") or not data.get("email"):
        return jsonify({"error": "name and email are required"}), 400
    member = {
        "id": next_id(MEMBERS, "M"),
        "name": data["name"],
        "email": data["email"],
        "phone": data.get("phone", ""),
    }
    MEMBERS.append(member)
    return jsonify(member), 201

@app.route("/api/members/<member_id>", methods=["PUT"])
def update_member(member_id):
    member = find(MEMBERS, member_id)
    if not member: return jsonify({"error": "Member not found"}), 404
    data = request.json
    member.update({
        "name": data.get("name", member["name"]),
        "email": data.get("email", member["email"]),
        "phone": data.get("phone", member["phone"]),
    })
    return jsonify(member)

@app.route("/api/members/<member_id>", methods=["DELETE"])
def delete_member(member_id):
    member = find(MEMBERS, member_id)
    if not member: return jsonify({"error": "Member not found"}), 404
    active = [l for l in LOANS if l["member_id"] == member_id and l["status"] == "active"]
    if active: return jsonify({"error": "Cannot delete member with active loans"}), 400
    MEMBERS.remove(member)
    return jsonify({"message": "Member deleted"})

# ─── Loans API ───────────────────────────────────────────────────────────────

@app.route("/api/loans", methods=["GET"])
def get_loans():
    enriched = []
    for loan in LOANS:
        l = copy.copy(loan)
        book = find(BOOKS, loan["book_id"])
        member = find(MEMBERS, loan["member_id"])
        l["book_title"] = book["title"] if book else "Unknown"
        l["member_name"] = member["name"] if member else "Unknown"
        enriched.append(l)
    return jsonify(enriched)

@app.route("/api/loans", methods=["POST"])
def create_loan():
    data = request.json
    book_id = data.get("book_id")
    member_id = data.get("member_id")
    book = find(BOOKS, book_id)
    member = find(MEMBERS, member_id)
    if not book: return jsonify({"error": "Book not found"}), 404
    if not member: return jsonify({"error": "Member not found"}), 404
    if book["stock"] <= 0: return jsonify({"error": "Book is out of stock"}), 400
    # Check if member already borrowed this book
    existing = [l for l in LOANS if l["book_id"] == book_id and l["member_id"] == member_id and l["status"] == "active"]
    if existing: return jsonify({"error": "Member already has this book borrowed"}), 400
    book["stock"] -= 1
    loan = {
        "id": next_id(LOANS, "L"),
        "book_id": book_id,
        "member_id": member_id,
        "borrow_date": str(date.today()),
        "return_date": None,
        "status": "active",
    }
    LOANS.append(loan)
    l = copy.copy(loan)
    l["book_title"] = book["title"]
    l["member_name"] = member["name"]
    return jsonify(l), 201

@app.route("/api/loans/<loan_id>/return", methods=["PUT"])
def return_loan(loan_id):
    loan = find(LOANS, loan_id)
    if not loan: return jsonify({"error": "Loan not found"}), 404
    if loan["status"] == "returned": return jsonify({"error": "Already returned"}), 400
    book = find(BOOKS, loan["book_id"])
    if book: book["stock"] += 1
    loan["status"] = "returned"
    loan["return_date"] = str(date.today())
    return jsonify(loan)

@app.route("/api/loans/<loan_id>", methods=["DELETE"])
def delete_loan(loan_id):
    loan = find(LOANS, loan_id)
    if not loan: return jsonify({"error": "Loan not found"}), 404
    if loan["status"] == "active":
        book = find(BOOKS, loan["book_id"])
        if book: book["stock"] += 1
    LOANS.remove(loan)
    return jsonify({"message": "Loan deleted"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
