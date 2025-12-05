from flask import Flask, jsonify, request, g
from werkzeug.security import generate_password_hash, check_password_hash
from dataclasses import dataclass, asdict
from functools import wraps
import json
import os
from typing import Dict, Tuple, Optional

app = Flask(__name__)

USERS_FILE = "users.json"


# -------------------- Data Models --------------------


@dataclass
class Book:
    """
    Simple data model for a book resource.
    """
    id: str
    title: str
    author: str
    publisher: str
    year: int
    genre: str
    stock: int
    owner: str  # username of the user who created/owns this book


# In-memory "database" of books: {book_id: Book}
books: Dict[str, Book] = {
    "BK001": Book(
        id="BK001",
        title="Designing Your Life",
        author="Bill Burnett",
        publisher="Knopf",
        year=2016,
        genre="Self-help",
        stock=5,
        owner="admin",
    ),
    "BK002": Book(
        id="BK002",
        title="Atomic Habits",
        author="James Clear",
        publisher="Avery",
        year=2018,
        genre="Self-help",
        stock=8,
        owner="admin",
    ),
    "BK003": Book(
        id="BK003",
        title="Mindset: The New Psychology of Success",
        author="Carol S. Dweck",
        publisher="Random House",
        year=2006,
        genre="Psychology",
        stock=4,
        owner="admin",
    ),
}


# -------------------- User Persistence --------------------


def load_users() -> Dict[str, Dict[str, str]]:
    """
    Load users from a JSON file.
    Structure on disk:
    {
      "alice": {"password_hash": "..."},
      "bob":   {"password_hash": "..."}
    }
    """
    if not os.path.exists(USERS_FILE):
        return {}

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                # basic shape validation
                cleaned = {}
                for username, info in data.items():
                    if isinstance(info, dict) and "password_hash" in info:
                        cleaned[username] = {"password_hash": info["password_hash"]}
                return cleaned
    except (OSError, json.JSONDecodeError):
        # In case of any file error, fall back to empty user store
        return {}

    return {}


def save_users(users: Dict[str, Dict[str, str]]) -> None:
    """
    Persist users to JSON file in a structured format.
    """
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2)
    except OSError:
        # For this assignment we just log to console;
        # in a real app we'd use proper logging.
        print("Warning: Failed to write users.json")


# load existing users (if any) at startup
users: Dict[str, Dict[str, str]] = load_users()

# Optional: create a default admin user if no users exist
if not users:
    users["admin"] = {
        "password_hash": generate_password_hash("admin123")
    }
    save_users(users)


# -------------------- Authentication Helpers --------------------


def validate_password(password: str) -> Optional[str]:
    """
    Enforce a very simple password policy:
    - at least 8 characters
    - must contain at least one digit and one letter
    Returns an error message string if invalid, or None if OK.
    """
    if len(password) < 8:
        return "Password must be at least 8 characters long."

    has_digit = any(c.isdigit() for c in password)
    has_alpha = any(c.isalpha() for c in password)

    if not (has_digit and has_alpha):
        return "Password must contain at least one letter and one number."

    return None


def require_auth(func):
    """
    Decorator that enforces HTTP Basic Authentication.
    On success sets g.current_user to the authenticated username.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        auth = request.authorization

        if not auth or not auth.username or not auth.password:
            return (
                jsonify({"detail": "Authentication required"}),
                401,
                {"WWW-Authenticate": 'Basic realm="Login required"'},
            )

        username = auth.username
        password = auth.password

        user_record = users.get(username)
        if not user_record:
            return (
                jsonify({"detail": "Invalid username or password"}),
                401,
                {"WWW-Authenticate": 'Basic realm="Login required"'},
            )

        if not check_password_hash(user_record["password_hash"], password):
            return (
                jsonify({"detail": "Invalid username or password"}),
                401,
                {"WWW-Authenticate": 'Basic realm="Login required"'},
            )

        g.current_user = username
        return func(*args, **kwargs)

    return wrapper


# -------------------- Helpers for Books --------------------


def book_to_dict(book: Book) -> Dict:
    """
    Convert a Book dataclass to a serializable dict.
    """
    return asdict(book)


def get_book_or_404(book_id: str) -> Tuple[Optional[Book], Optional[Tuple]]:
    """
    Helper to fetch a book or return a prepared 404 response.
    """
    book = books.get(book_id)
    if not book:
        return None, (jsonify({"error": "Book not found"}), 404)
    return book, None


def ensure_owner(book: Book) -> Optional[Tuple]:
    """
    Ensure the authenticated user is the owner of the book.
    Returns a (response, status) tuple if not allowed, else None.
    """
    current_user = getattr(g, "current_user", None)
    if not current_user:
        return jsonify({"error": "Authentication required"}), 401

    if book.owner != current_user:
        return jsonify({"error": "Forbidden: not the owner of this resource"}), 403

    return None


# -------------------- Registration & Auth Endpoints --------------------


@app.route("/register", methods=["POST"])
def register():
    """
    Register a new user.

    Request JSON:
    {
      "username": "alice",
      "password": "MyStrongP4ss"
    }
    """
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    if len(username) < 3:
        return jsonify({"error": "username must be at least 3 characters"}), 400

    if username in users:
        return jsonify({"error": "username already exists"}), 400

    pw_error = validate_password(password)
    if pw_error:
        return jsonify({"error": pw_error}), 400

    password_hash = generate_password_hash(password)
    users[username] = {"password_hash": password_hash}
    save_users(users)

    return jsonify({"message": "User registered successfully"}), 201


@app.route("/me", methods=["GET"])
@require_auth
def me():
    """
    Simple endpoint to verify authentication.
    """
    return jsonify({"username": g.current_user}), 200


# -------------------- Book Endpoints --------------------


@app.route("/books", methods=["GET"])
def list_books():
    """
    Public endpoint.
    Returns all books in the catalog.
    """
    return jsonify({book_id: book_to_dict(book) for book_id, book in books.items()}), 200


@app.route("/books/<string:book_id>", methods=["GET"])
def get_book(book_id: str):
    """
    Public endpoint.
    Returns a single book by its ID.
    """
    book, error_response = get_book_or_404(book_id)
    if error_response:
        return error_response

    return jsonify(book_to_dict(book)), 200


@app.route("/books", methods=["POST"])
@require_auth
def create_book():
    """
    Create a new book owned by the authenticated user.

    Expected JSON body:
    {
      "id": "BK004",
      "title": "...",
      "author": "...",
      "publisher": "...",
      "year": 2024,
      "genre": "...",
      "stock": 3
    }
    """
    data = request.get_json() or {}
    book_id = data.get("id")

    if not book_id:
        return jsonify({"error": "Field 'id' is required"}), 400

    if book_id in books:
        return jsonify({"error": "Book with this id already exists"}), 400

    required_fields = ["title", "author", "publisher", "year", "genre", "stock"]
    missing = [field for field in required_fields if field not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        year = int(data["year"])
        stock = int(data["stock"])
    except (TypeError, ValueError):
        return jsonify({"error": "year and stock must be integers"}), 400

    new_book = Book(
        id=book_id,
        title=data["title"],
        author=data["author"],
        publisher=data["publisher"],
        year=year,
        genre=data["genre"],
        stock=stock,
        owner=g.current_user,
    )

    books[book_id] = new_book
    return jsonify({"message": "Book created", "book": book_to_dict(new_book)}), 201


@app.route("/books/<string:book_id>", methods=["PUT"])
@require_auth
def update_book(book_id: str):
    """
    Update fields for a book.
    Only the owner of the book may modify it.
    """
    book, error_response = get_book_or_404(book_id)
    if error_response:
        return error_response

    forbidden = ensure_owner(book)
    if forbidden:
        return forbidden

    data = request.get_json() or {}

    # Do not allow changing the owner or id via API
    data.pop("owner", None)
    data.pop("id", None)

    if "year" in data:
        try:
            data["year"] = int(data["year"])
        except (TypeError, ValueError):
            return jsonify({"error": "year must be an integer"}), 400

    if "stock" in data:
        try:
            data["stock"] = int(data["stock"])
        except (TypeError, ValueError):
            return jsonify({"error": "stock must be an integer"}), 400

    for field, value in data.items():
        if hasattr(book, field):
            setattr(book, field, value)

    return jsonify({"message": "Book updated", "book": book_to_dict(book)}), 200


@app.route("/books/<string:book_id>", methods=["DELETE"])
@require_auth
def delete_book(book_id: str):
    """
    Delete a book.
    Only the owner of the book may delete it.
    """
    book, error_response = get_book_or_404(book_id)
    if error_response:
        return error_response

    forbidden = ensure_owner(book)
    if forbidden:
        return forbidden

    del books[book_id]
    return jsonify({"message": "Book deleted"}), 200


if __name__ == "__main__":
    # In production, debug=False and a proper WSGI server would be used.
    app.run(debug=True, port=5000)
