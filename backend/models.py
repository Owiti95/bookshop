from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import validates
from config import db
from sqlalchemy import MetaData, Table
from sqlalchemy_serializer import SerializerMixin
from flask_bcrypt import Bcrypt
import re
from datetime import datetime

bcrypt = Bcrypt()
metadata = MetaData()



class User(db.Model, SerializerMixin):
    __tablename__ = 'users'
    serialize_rules = ('-orders.user', '-orders.books', '-borrowings.user', '-cart.user', '-transactions.user')

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    # Relationships
    orders = db.relationship('Order', back_populates='user')
    borrowings = db.relationship('Borrowing', back_populates='user')
    cart = db.relationship('Cart', uselist=False, back_populates='user')
    transactions = db.relationship('MpesaTransaction', back_populates='user')

    @validates('email')
    def validate_email(self, key, email):
        valid_email = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(valid_email, email):
            raise ValueError("Invalid email")
        return email

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.name}, Email: {self.email}>'

# Association table for the many-to-many relationship between Order and Book
order_books = Table(
    'order_books', db.Model.metadata,
    db.Column('order_id', db.Integer, db.ForeignKey('orders.id'), primary_key=True),
    db.Column('book_id', db.Integer, db.ForeignKey('books.id'), primary_key=True),
    db.Column('quantity', db.Integer, nullable=False, default=1)
)

class Book(db.Model, SerializerMixin):
    __tablename__ = 'books'
    serialize_rules = ('-orders.books', '-category.books', '-borrowings.book', '-cart_items.book')

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String)
    stock = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    is_available_for_borrowing = db.Column(db.Boolean, default=True)

    # Relationships
    category = db.relationship('Category', back_populates='books')
    orders = db.relationship('Order', secondary=order_books, back_populates='books')
    borrowings = db.relationship('Borrowing', back_populates='book')
    cart_items = db.relationship('CartItem', back_populates='book')

    def __repr__(self):
        return f'<Book {self.title} by {self.author}, Price: ${self.price}>'

class Order(db.Model, SerializerMixin):
    __tablename__ = 'orders'
    serialize_rules = ('-user.orders', '-books.orders')

    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String, nullable=False, default='Pending')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Relationships
    user = db.relationship('User', back_populates='orders')
    books = db.relationship('Book', secondary=order_books, back_populates='orders')

    VALID_STATUSES = ['Pending', 'Shipped', 'Delivered', 'Cancelled']

    @validates('status')
    def validate_status(self, key, status):
        if status not in self.VALID_STATUSES:
            raise ValueError("Invalid order status")
        return status

    def __repr__(self):
        return f'<Order {self.id} by User {self.user_id}, Status: {self.status}>'




# class User(db.Model, SerializerMixin):
#     __tablename__ = 'users'
#     serialize_rules = ('-orders.user', '-orders.books', '-borrowings.user', '-cart.user', '-transactions.user')

#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String, nullable=False)
#     email = db.Column(db.String, unique=True, nullable=False)
#     password_hash = db.Column(db.String, nullable=False)
#     is_admin = db.Column(db.Boolean, default=False)

#     # Relationships
#     orders = db.relationship('Order', back_populates='user')
#     borrowings = db.relationship('Borrowing', back_populates='user')
#     cart = db.relationship('Cart', uselist=False, back_populates='user')
#     transactions = db.relationship('MpesaTransaction', back_populates='user')

#     @validates('email')
#     def validate_email(self, key, email):
#         valid_email = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
#         if not re.match(valid_email, email):
#             raise ValueError("Invalid email")
#         return email

#     def set_password(self, password):
#         self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

#     def check_password(self, password):
#         return bcrypt.check_password_hash(self.password_hash, password)

#     def __repr__(self):
#         return f'<User {self.name}, Email: {self.email}>'

# # Association table for the many-to-many relationship between Order and Book
# order_books = Table(
#     'order_books', db.Model.metadata,
#     db.Column('order_id', db.Integer, db.ForeignKey('orders.id'), primary_key=True),
#     db.Column('book_id', db.Integer, db.ForeignKey('books.id'), primary_key=True)
# )

# class Book(db.Model, SerializerMixin):
#     __tablename__ = 'books'
#     serialize_rules = ('-orders.books', '-category.books', '-borrowings.book', '-cart_items.book')

#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String, nullable=False)
#     author = db.Column(db.String, nullable=False)
#     price = db.Column(db.Float, nullable=False)
#     description = db.Column(db.String)
#     stock = db.Column(db.Integer, default=0)
#     category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
#     is_available_for_borrowing = db.Column(db.Boolean, default=True)

#     # Relationships
#     category = db.relationship('Category', back_populates='books')
#     orders = db.relationship('Order', secondary=order_books, back_populates='books')
#     borrowings = db.relationship('Borrowing', back_populates='book')
#     cart_items = db.relationship('CartItem', back_populates='book')

#     def __repr__(self):
#         return f'<Book {self.title} by {self.author}, Price: ${self.price}>'

# class Order(db.Model, SerializerMixin):
#     __tablename__ = 'orders'
#     serialize_rules = ('-user.orders', '-books.orders')

#     id = db.Column(db.Integer, primary_key=True)
#     order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
#     status = db.Column(db.String, nullable=False, default='Pending')
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

#     # Relationships
#     user = db.relationship('User', back_populates='orders')
#     books = db.relationship('Book', secondary=order_books, back_populates='orders')

#     VALID_STATUSES = ['Pending', 'Shipped', 'Delivered', 'Cancelled']

#     @validates('status')
#     def validate_status(self, key, status):
#         if status not in self.VALID_STATUSES:
#             raise ValueError("Invalid order status")
#         return status

#     def __repr__(self):
#         return f'<Order {self.id} by User {self.user_id}, Status: {self.status}>'

class Borrowing(db.Model, SerializerMixin):
    __tablename__ = 'borrowings'
    serialize_rules = ('-user.borrowings', '-book.borrowings')

    id = db.Column(db.Integer, primary_key=True)
    borrow_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime)  # Nullable, as it will be populated when the book is returned
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='borrowings')
    book = db.relationship('Book', back_populates='borrowings')

    def __repr__(self):
        return f'<Borrowing of {self.book.title} by {self.user.name}, Due on {self.due_date}>'

class Cart(db.Model, SerializerMixin):
    __tablename__ = 'carts'
    serialize_rules = ('-user.cart', '-items.cart')

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='cart')
    items = db.relationship('CartItem', back_populates='cart', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Cart for User {self.user_id}>'

class CartItem(db.Model, SerializerMixin):
    __tablename__ = 'cart_items'
    serialize_rules = ('-cart.items', '-book.cart_items')

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    # Relationships
    cart = db.relationship('Cart', back_populates='items')
    book = db.relationship('Book', back_populates='cart_items')

    def __repr__(self):
        return f'<CartItem {self.quantity} of Book {self.book.title} in Cart {self.cart_id}>'

class MpesaTransaction(db.Model, SerializerMixin):
    __tablename__ = 'mpesa_transactions'
    serialize_rules = ('-user.transactions',)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    mpesa_receipt = db.Column(db.String, unique=True, nullable=False)
    status = db.Column(db.String, nullable=False, default='Pending')

    # Relationships
    user = db.relationship('User', back_populates='transactions')

    def __repr__(self):
        return f'<MpesaTransaction {self.id} for User {self.user_id}, Amount: {self.amount}, Status: {self.status}>'

class Category(db.Model, SerializerMixin):
    __tablename__ = 'categories'
    serialize_rules = ('-books.category',)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)

    # Relationships
    books = db.relationship('Book', back_populates='category')

    def __repr__(self):
        return f'<Category {self.name}>'




















# from flask_sqlalchemy import SQLAlchemy
# from flask_bcrypt import Bcrypt
# from datetime import datetime
# import uuid

# db = SQLAlchemy()
# bcrypt = Bcrypt()

# # User Model
# class User(db.Model):
#     __tablename__ = 'users'
    
#     id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
#     username = db.Column(db.String(50), nullable=False, unique=True)
#     email = db.Column(db.String(120), nullable=False, unique=True)
#     password_hash = db.Column(db.String(128), nullable=False)
#     phone_number = db.Column(db.String(20), nullable=False)
#     is_active = db.Column(db.Boolean, default=True)
    
#     borrowed_books = db.relationship('BorrowedBook', back_populates='user')
#     purchase_history = db.relationship('Order', back_populates='user')
    
#     two_factor_auth_code = db.Column(db.String(6), nullable=True)
    
#     def set_password(self, password):
#         self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
#     def check_password(self, password):
#         return bcrypt.check_password_hash(self.password_hash, password)

# # Book Model
# class Book(db.Model):
#     __tablename__ = 'books'
    
#     id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
#     title = db.Column(db.String(100), nullable=False)
#     author = db.Column(db.String(100), nullable=False)
#     category_id = db.Column(db.String(36), db.ForeignKey('categories.id'), nullable=True)
#     isbn = db.Column(db.String(13), unique=True)
#     description = db.Column(db.Text, nullable=True)
#     price = db.Column(db.Float, nullable=False)
#     is_available = db.Column(db.Boolean, default=True)
#     is_borrowable = db.Column(db.Boolean, default=False)
#     borrow_fee = db.Column(db.Float, nullable=True)
#     stock = db.Column(db.Integer, default=0)
#     cover_image = db.Column(db.String(255), nullable=True)
    
#     category = db.relationship('Category', back_populates='books')

# # Category Model
# class Category(db.Model):
#     __tablename__ = 'categories'
    
#     id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
#     name = db.Column(db.String(50), nullable=False, unique=True)
#     description = db.Column(db.String(255), nullable=True)
    
#     books = db.relationship('Book', back_populates='category')

# # Order Model
# class Order(db.Model):
#     __tablename__ = 'orders'
    
#     id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
#     user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
#     total_price = db.Column(db.Float, nullable=False)
#     status = db.Column(db.String(50), default="Pending")
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
#     user = db.relationship('User', back_populates='purchase_history')
#     books = db.relationship('Book', secondary='order_books', backref='orders')

# # Association table for Order and Book
# order_books = db.Table('order_books',
#     db.Column('order_id', db.String(36), db.ForeignKey('orders.id')),
#     db.Column('book_id', db.String(36), db.ForeignKey('books.id'))
# )

# # BorrowedBook Model
# class BorrowedBook(db.Model):
#     __tablename__ = 'borrowed_books'
    
#     id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
#     user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
#     book_id = db.Column(db.String(36), db.ForeignKey('books.id'), nullable=False)
#     borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
#     due_date = db.Column(db.DateTime, nullable=False)
#     status = db.Column(db.String(20), default="Active")
#     fee_paid = db.Column(db.Float, nullable=True)
    
#     user = db.relationship('User', back_populates='borrowed_books')
#     book = db.relationship('Book')

# # MpesaTransaction Model
# class MpesaTransaction(db.Model):
#     __tablename__ = 'mpesa_transactions'
    
#     id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
#     order_id = db.Column(db.String(36), db.ForeignKey('orders.id'), nullable=False)
#     transaction_id = db.Column(db.String(50), unique=True, nullable=False)
#     status = db.Column(db.String(20), default="Pending")
#     amount = db.Column(db.Float, nullable=False)
#     phone_number = db.Column(db.String(20), nullable=False)
#     timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
#     order = db.relationship('Order')

# # Cart Model (Optional)
# class Cart(db.Model):
#     __tablename__ = 'carts'
    
#     id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
#     user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
#     user = db.relationship('User')
#     books = db.relationship('Book', secondary='cart_books', backref='carts')

# # Association table for Cart and Book
# cart_books = db.Table('cart_books',
#     db.Column('cart_id', db.String(36), db.ForeignKey('carts.id')),
#     db.Column('book_id', db.String(36), db.ForeignKey('books.id'))
# )

# # Review Model (Optional)
# class Review(db.Model):
#     __tablename__ = 'reviews'
    
#     id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
#     user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
#     book_id = db.Column(db.String(36), db.ForeignKey('books.id'), nullable=False)
#     rating = db.Column(db.Integer, nullable=False)
#     comment = db.Column(db.Text, nullable=True)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
#     user = db.relationship('User')
#     book = db.relationship('Book')
