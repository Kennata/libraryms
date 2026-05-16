from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)


# ─────────────────────────────────────────
# SERVE FRONTEND
# ─────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

# ─────────────────────────────────────────
# IN-MEMORY DATA STORE
# ─────────────────────────────────────────

books = [
    {"id": 1, "title": "The Midnight Library",  "author": "Matt Haig",        "year": 2020, "stock": 12, "isbn": "978-0525559474"},
    {"id": 2, "title": "Atomic Habits",          "author": "James Clear",       "year": 2018, "stock":  7, "isbn": "978-0735211292"},
    {"id": 3, "title": "Circe",                  "author": "Madeline Miller",   "year": 2018, "stock":  0, "isbn": "978-0316556347"},
    {"id": 4, "title": "Project Hail Mary",      "author": "Andy Weir",         "year": 2021, "stock":  5, "isbn": "978-0593135204"},
    {"id": 5, "title": "The Alchemist",          "author": "Paulo Coelho",      "year": 1988, "stock": 15, "isbn": "978-0062315007"},
]

members = [
    {"id": 1, "name": "Rafid Al Afif",     "email": "rafid@example.com",    "phone": "(+62) 081-23456789"},
    {"id": 2, "name": "Dzaky Superman",    "email": "dc@example.com",        "phone": "(+62) 081-23456789"},
    {"id": 3, "name": "Kennata Al Arifi",  "email": "risang@example.com",    "phone": "(+62) 081-23456789"},
    {"id": 4, "name": "Faza Vario Borup",  "email": "maslaqal@example.com",  "phone": "(+62) 081-23456789"},
    {"id": 5, "name": "Ravitihi Athallah", "email": "cburnson@example.com",  "phone": "(+62) 081-23456789"},
]

_today = datetime.today()
loans = [
    {"id": 1, "member_id": 1, "book_id": 1,
     "borrow_date": (_today - timedelta(days=5)).strftime("%d/%m/%Y"),
     "due_date":    (_today + timedelta(days=9)).strftime("%d/%m/%Y"),
     "return_date": None, "status": "active"},
    {"id": 2, "member_id": 2, "book_id": 2,
     "borrow_date": (_today - timedelta(days=3)).strftime("%d/%m/%Y"),
     "due_date":    (_today + timedelta(days=11)).strftime("%d/%m/%Y"),
     "return_date": _today.strftime("%d/%m/%Y"), "status": "returned"},
    {"id": 3, "member_id": 3, "book_id": 3,
     "borrow_date": (_today - timedelta(days=16)).strftime("%d/%m/%Y"),
     "due_date":    (_today - timedelta(days=2)).strftime("%d/%m/%Y"),
     "return_date": None, "status": "overdue"},
    {"id": 4, "member_id": 4, "book_id": 4,
     "borrow_date": (_today - timedelta(days=7)).strftime("%d/%m/%Y"),
     "due_date":    (_today + timedelta(days=7)).strftime("%d/%m/%Y"),
     "return_date": _today.strftime("%d/%m/%Y"), "status": "returned"},
]

book_id_counter   = max(b["id"] for b in books)   + 1
member_id_counter = max(m["id"] for m in members) + 1
loan_id_counter   = max(l["id"] for l in loans)   + 1


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def find_by_id(lst, id_):
    return next((x for x in lst if x["id"] == id_), None)

def update_overdue():
    now = datetime.today()
    for loan in loans:
        if loan["status"] == "active":
            due = datetime.strptime(loan["due_date"], "%d/%m/%Y")
            if due < now:
                loan["status"] = "overdue"

def paginate(lst, page, per_page):
    start = (page - 1) * per_page
    return lst[start:start + per_page]

def enrich_loan(loan):
    member = find_by_id(members, loan["member_id"]) or {}
    book   = find_by_id(books,   loan["book_id"])   or {}
    return {**loan, "member_name": member.get("name", "—"), "book_title": book.get("title", "—")}


# ─────────────────────────────────────────
# STATS
# ─────────────────────────────────────────

@app.route("/api/stats")
def stats():
    update_overdue()
    today_str = datetime.today().strftime("%d/%m/%Y")
    active_borrower_ids = {l["member_id"] for l in loans if l["status"] == "active"}
    return jsonify({
        "books":            len(books),
        "total_stock":      sum(b["stock"] for b in books),
        "out_of_stock":     sum(1 for b in books if b["stock"] == 0),
        "members":          len(members),
        "active_borrowers": len(active_borrower_ids),
        "total_loans":      len(loans),
        "active_loans":     sum(1 for l in loans if l["status"] == "active"),
        "overdue":          sum(1 for l in loans if l["status"] == "overdue"),
        "returns_today":    sum(1 for l in loans if l["return_date"] == today_str),
    })


# ─────────────────────────────────────────
# BOOKS
# ─────────────────────────────────────────

@app.route("/api/books", methods=["GET"])
def get_books():
    q        = request.args.get("q", "").strip().lower()
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))

    result = [b for b in books if
              not q or q in b["title"].lower() or q in b["author"].lower() or q in str(b["id"])
             ]
    return jsonify({
        "total": len(result), "page": page, "per_page": per_page,
        "books": paginate(result, page, per_page)
    })

@app.route("/api/books", methods=["POST"])
def add_book():
    global book_id_counter
    data = request.get_json()
    if not data.get("title") or not data.get("author"):
        return jsonify({"error": "title and author are required"}), 400
    book = {
        "id":     book_id_counter,
        "title":  data["title"].strip(),
        "author": data["author"].strip(),
        "year":   data.get("year"),
        "stock":  int(data.get("stock", 0)),
        "isbn":   data.get("isbn", ""),
    }
    books.append(book)
    book_id_counter += 1
    return jsonify({"id": book["id"], "message": "Book added"}), 201

@app.route("/api/books/<int:book_id>", methods=["PUT"])
def update_book(book_id):
    book = find_by_id(books, book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    data = request.get_json()
    book.update({k: data[k] for k in ("title", "author", "year", "stock", "isbn") if k in data})
    return jsonify({"message": "Book updated"})

@app.route("/api/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    book = find_by_id(books, book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    books.remove(book)
    return jsonify({"message": "Book deleted"})


# ─────────────────────────────────────────
# MEMBERS
# ─────────────────────────────────────────

@app.route("/api/members", methods=["GET"])
def get_members():
    q        = request.args.get("q", "").strip().lower()
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))

    result = [m for m in members if
              not q or q in m["name"].lower() or q in m["email"].lower() or q in str(m["id"])
             ]
    paged = paginate(result, page, per_page)

    enriched = []
    for m in paged:
        active = sum(1 for l in loans if l["member_id"] == m["id"] and l["status"] == "active")
        enriched.append({**m, "active_loans": active})

    return jsonify({"total": len(result), "page": page, "per_page": per_page, "members": enriched})

@app.route("/api/members", methods=["POST"])
def add_member():
    global member_id_counter
    data = request.get_json()
    if not data.get("name") or not data.get("email"):
        return jsonify({"error": "name and email are required"}), 400
    if any(m["email"] == data["email"].strip() for m in members):
        return jsonify({"error": "Email already exists"}), 409
    member = {
        "id":    member_id_counter,
        "name":  data["name"].strip(),
        "email": data["email"].strip(),
        "phone": data.get("phone", ""),
    }
    members.append(member)
    member_id_counter += 1
    return jsonify({"id": member["id"], "message": "Member registered"}), 201

@app.route("/api/members/<int:member_id>", methods=["PUT"])
def update_member(member_id):
    member = find_by_id(members, member_id)
    if not member:
        return jsonify({"error": "Member not found"}), 404
    data = request.get_json()
    member.update({k: data[k] for k in ("name", "email", "phone") if k in data})
    return jsonify({"message": "Member updated"})

@app.route("/api/members/<int:member_id>", methods=["DELETE"])
def delete_member(member_id):
    member = find_by_id(members, member_id)
    if not member:
        return jsonify({"error": "Member not found"}), 404
    members.remove(member)
    return jsonify({"message": "Member deleted"})


# ─────────────────────────────────────────
# LOANS
# ─────────────────────────────────────────

@app.route("/api/loans", methods=["GET"])
def get_loans():
    update_overdue()
    status_filter = request.args.get("status", "all")
    q        = request.args.get("q", "").strip().lower()
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))

    enriched = [enrich_loan(l) for l in reversed(loans)]  # newest first

    if status_filter != "all":
        enriched = [l for l in enriched if l["status"] == status_filter]

    if q:
        enriched = [l for l in enriched if
                    q in l["member_name"].lower() or
                    q in l["book_title"].lower()  or
                    q in str(l["id"])]

    return jsonify({
        "total": len(enriched), "page": page, "per_page": per_page,
        "loans": paginate(enriched, page, per_page)
    })

@app.route("/api/loans", methods=["POST"])
def create_loan():
    global loan_id_counter
    data      = request.get_json()
    member_id = data.get("member_id")
    book_id   = data.get("book_id")
    due_date  = data.get("due_date")

    if not all([member_id, book_id, due_date]):
        return jsonify({"error": "member_id, book_id, and due_date are required"}), 400

    book = find_by_id(books, book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    if book["stock"] < 1:
        return jsonify({"error": "Book is out of stock"}), 409

    loan = {
        "id":          loan_id_counter,
        "member_id":   member_id,
        "book_id":     book_id,
        "borrow_date": datetime.today().strftime("%d/%m/%Y"),
        "due_date":    due_date,
        "return_date": None,
        "status":      "active",
    }
    loans.append(loan)
    book["stock"] -= 1
    loan_id_counter += 1
    return jsonify({"id": loan["id"], "message": "Loan created"}), 201

@app.route("/api/loans/<int:loan_id>/return", methods=["POST"])
def return_loan(loan_id):
    loan = find_by_id(loans, loan_id)
    if not loan:
        return jsonify({"error": "Loan not found"}), 404
    if loan["status"] == "returned":
        return jsonify({"error": "Already returned"}), 409

    loan["status"]      = "returned"
    loan["return_date"] = datetime.today().strftime("%d/%m/%Y")

    book = find_by_id(books, loan["book_id"])
    if book:
        book["stock"] += 1

    return jsonify({"message": "Book returned successfully"})


# ─────────────────────────────────────────
# RECENT ACTIVITY
# ─────────────────────────────────────────

@app.route("/api/activity")
def get_activity():
    recent = [enrich_loan(l) for l in reversed(loans[-10:])]
    return jsonify(recent)


# ─────────────────────────────────────────
# RUN
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("✅  LibraryMS Flask API  →  http://127.0.0.1:5000")
    print("⚠️   Data is in-memory only — resets when server restarts")
    app.run(debug=True, port=5000)
