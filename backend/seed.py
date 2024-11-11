from config import db, app
from models import User, Book, Order, Borrowing, Cart, Category, MpesaTransaction, CartItem
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt

# Initialize Bcrypt for password hashing
bcrypt = Bcrypt()

print("Starting seed...")

# Use the application context to access the database
with app.app_context():
    # Drop all existing tables and create new ones
    db.drop_all()
    db.create_all()
    print("Created all tables.")

    # Create categories first
    try:
        categories = [
            Category(name="Fiction"),
            Category(name="Non-fiction"),
            Category(name="Science"),
            Category(name="Biography"),
            Category(name="Technology"),
        ]
        
        # Add categories to the session and commit
        db.session.add_all(categories)
        db.session.commit()
        print("Categories added successfully.")
    except Exception as e:
        print(f"Error creating categories: {e}")

    # Create users manually
    try:
        users = [
            User(name="Alice", email="alice@example.com", password_hash=bcrypt.generate_password_hash("password").decode('utf-8')),
            User(name="Bob", email="bob@example.com", password_hash=bcrypt.generate_password_hash("password").decode('utf-8')),
            User(name="Charlie", email="charlie@example.com", password_hash=bcrypt.generate_password_hash("password").decode('utf-8')),
            User(name="David", email="david@example.com", password_hash=bcrypt.generate_password_hash("password").decode('utf-8')),
            User(name="Eve", email="eve@example.com", password_hash=bcrypt.generate_password_hash("password").decode('utf-8')),
        ]
        
        # Add all users to the session and commit
        db.session.add_all(users)
        db.session.commit()
        print("Users added successfully.")
    except Exception as e:
        print(f"Error creating users: {e}")

    # Create books manually
    try:
        books = [
            Book(title="The Great Gatsby", author="F. Scott Fitzgerald", price=10.99, stock=5, category_id=1),
            Book(title="1984", author="George Orwell", price=8.99, stock=10, category_id=1),
            Book(title="Sapiens", author="Yuval Noah Harari", price=15.99, stock=7, category_id=2),
            Book(title="Educated", author="Tara Westover", price=12.99, stock=3, category_id=4),
            Book(title="Clean Code", author="Robert C. Martin", price=25.99, stock=8, category_id=5),
        ]
        
        # Add books to the session and commit
        db.session.add_all(books)
        db.session.commit()
        print("Books added successfully.")
    except Exception as e:
        print(f"Error creating books: {e}")

    # Create orders manually
    try:
        orders = [
            Order(order_date=datetime.utcnow(), status="Pending", user_id=1),
            Order(order_date=datetime.utcnow() - timedelta(days=1), status="Shipped", user_id=2),
            Order(order_date=datetime.utcnow() - timedelta(days=2), status="Delivered", user_id=3),
            Order(order_date=datetime.utcnow() - timedelta(days=3), status="Cancelled", user_id=4),
            Order(order_date=datetime.utcnow() - timedelta(days=4), status="Pending", user_id=5),
        ]
        
        # Add orders to the session and commit
        db.session.add_all(orders)
        db.session.commit()
        print("Orders added successfully.")
    except Exception as e:
        print(f"Error creating orders: {e}")

    # Create borrowings manually
    try:
        borrowings = [
            Borrowing(borrow_date=datetime.utcnow(), due_date=datetime.utcnow() + timedelta(days=7), user_id=1, book_id=2),
            Borrowing(borrow_date=datetime.utcnow() - timedelta(days=1), due_date=datetime.utcnow() + timedelta(days=7), user_id=2, book_id=3),
            Borrowing(borrow_date=datetime.utcnow() - timedelta(days=2), due_date=datetime.utcnow() + timedelta(days=7), user_id=3, book_id=1),
            Borrowing(borrow_date=datetime.utcnow() - timedelta(days=3), due_date=datetime.utcnow() + timedelta(days=7), user_id=4, book_id=4),
            Borrowing(borrow_date=datetime.utcnow() - timedelta(days=4), due_date=datetime.utcnow() + timedelta(days=7), user_id=5, book_id=5),
        ]
        
        # Add borrowings to the session and commit
        db.session.add_all(borrowings)
        db.session.commit()
        print("Borrowings added successfully.")
    except Exception as e:
        print(f"Error creating borrowings: {e}")

    # Create carts manually
    try:
        carts = [
            Cart(user_id=1),
            Cart(user_id=2),
            Cart(user_id=3),
            Cart(user_id=4),
            Cart(user_id=5),
        ]
        
        # Add carts to the session and commit
        db.session.add_all(carts)
        db.session.commit()
        print("Carts added successfully.")
    except Exception as e:
        print(f"Error creating carts: {e}")

    # Create cart items manually
    try:
        cart_items = [
            CartItem(cart_id=1, book_id=1, quantity=2),
            CartItem(cart_id=2, book_id=3, quantity=1),
            CartItem(cart_id=3, book_id=2, quantity=4),
            CartItem(cart_id=4, book_id=4, quantity=1),
            CartItem(cart_id=5, book_id=5, quantity=3),
        ]
        
        # Add cart items to the session and commit
        db.session.add_all(cart_items)
        db.session.commit()
        print("Cart items added successfully.")
    except Exception as e:
        print(f"Error creating cart items: {e}")

    # Create Mpesa transactions manually
    try:
        transactions = [
            MpesaTransaction(user_id=1, amount=100.0, mpesa_receipt="123456", status="Completed"),
            MpesaTransaction(user_id=2, amount=200.0, mpesa_receipt="654321", status="Pending"),
            MpesaTransaction(user_id=3, amount=300.0, mpesa_receipt="789123", status="Failed"),
            MpesaTransaction(user_id=4, amount=150.0, mpesa_receipt="321789", status="Completed"),
            MpesaTransaction(user_id=5, amount=50.0, mpesa_receipt="987654", status="Pending"),
        ]
        
        # Add Mpesa transactions to the session and commit
        db.session.add_all(transactions)
        db.session.commit()
        print("Mpesa transactions added successfully.")
    except Exception as e:
        print(f"Error creating Mpesa transactions: {e}")

print("Seeding complete.")
