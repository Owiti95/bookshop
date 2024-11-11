#!/usr/bin/env python3

# Standard library imports
from datetime import datetime, timedelta
import os  # For interacting with the operating system (e.g., to load environment variables).

# Remote library imports
from flask import make_response, request, session, jsonify, render_template
from flask_mpesa import MpesaAPI
from flask_restful import Api, Resource
from flask_migrate import Migrate
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

# Load environment variables from .env file.
load_dotenv()

# Local imports
from config import db, app, api
from models import User, order_books, Book, Order, Borrowing, Cart, MpesaTransaction

# Set secret key for sessions and configure database URI.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')  # Secret key for managing sessions and cookies.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI')  # URI for connecting to the database.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disables Flask-SQLAlchemy event system for performance.

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')  # Secret key for JWT
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)  # Set the expiry time for access tokens.

# Initialize extensions
mpesa_api = MpesaAPI(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)  # Initialize JWTManager.

# Helper function to check if the current user is an admin.
def is_admin():
    user_id = session.get('user_id')
    if not user_id:
        return False
    user = User.query.get(user_id)
    print("User ID:", user_id, "Is Admin:", user.is_admin if user else "No user found")
    return user.is_admin if user else False


# Admin check route
@app.route('/admin_check', methods=['GET'])
@jwt_required()
def admin_check():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user and user.is_admin:
        return jsonify({"message": "User is an admin"}), 200
    return jsonify({"message": "User is not an admin"}), 403


# Resource for user registration (registering a new user).
class Register(Resource):
    def post(self):
        data = request.json
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')

        if not name or not email or not password:
            return {"error": "Missing required fields"}, 400

        if User.query.filter_by(email=email).first():
            return {"error": "Email already exists"}, 400

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        return user.to_dict(), 201
    

class Login(Resource):
    def post(self):
        data = request.json
        email = data.get('email')
        password = data.get('password')

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            # Generate JWT token after successful login.
            access_token = create_access_token(identity=user.id)
            response_data = {
                "message": "Login successful",
                "access_token": access_token,
                "user": user.to_dict()
            }
            response = make_response(jsonify(response_data), 200)
            return response
        else:
            return {"error": "Invalid credentials"}, 401



# # Resource for user login (logging in an existing user).
# class Login(Resource):
#     def post(self):
#         data = request.json
#         email = data.get('email')
#         password = data.get('password')

#         user = User.query.filter_by(email=email).first()
#         if user and user.check_password(password):
#             # Generate JWT token after successful login.
#             access_token = create_access_token(identity=user.id)
#             return jsonify({
#                 "message": "Login successful",
#                 "access_token": access_token,
#                 "user": user.to_dict()
#             }), 200
#         else:
#             return {"error": "Invalid credentials"}, 401

# Resource for viewing and managing the user's cart (requires JWT authentication).




class CartResource(Resource):
    @jwt_required()
    def get(self):
        try:
            user_id = get_jwt_identity()  # Get the current user ID from the JWT.
        except Exception as e:
            return {"error": "Invalid or expired token"}, 401
        
        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart:
            return {"error": "No cart found for user"}, 404
        
        return cart.to_dict(), 200

    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()  # Get the current user ID from the JWT.
        data = request.json
        book_id = data.get('book_id')
        quantity = data.get('quantity')

        if not book_id or not quantity:
            return {"error": "Missing required fields"}, 400

        # Get the book instance by ID
        book = Book.query.get(book_id)
        if not book:
            return {"error": "Book not found"}, 404

        # Get the user's cart or create a new one if it doesn't exist
        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart:
            cart = Cart(user_id=user_id)
            db.session.add(cart)

        # Create an Order instance
        order = Order(user_id=user_id)
        db.session.add(order)

        # Append the book to the order's books list
        order.books.append(book)

        # Insert the book with quantity into the association table
        # This assumes the `order_books` table is being used to track relationships
        db.session.execute(
            order_books.insert().values(order_id=order.id, book_id=book.id, quantity=quantity)
        )
        
        db.session.commit()  # Commit the transaction to the database

        return order.to_dict(), 201




# class CartResource(Resource):
#     @jwt_required()
#     def get(self):
#         try:
#             user_id = get_jwt_identity()  # Get the current user ID from the JWT.
#         except Exception as e:
#             return {"error": "Invalid or expired token"}, 401
#         cart = Cart.query.filter_by(user_id=user_id).first()
#         if not cart:
#             return {"error": "No cart found for user"}, 404
#         return cart.to_dict(), 200

#     # @jwt_required()
#     # def get(self):
#     #     user_id = get_jwt_identity()  # Get the current user ID from the JWT.
#     #     cart = Cart.query.filter_by(user_id=user_id).first()
#     #     if not cart:
#     #         return {"error": "No cart found for user"}, 404
#     #     return cart.to_dict(), 200

#     @jwt_required()
#     def post(self):
#         user_id = get_jwt_identity()  # Get the current user ID from the JWT.
#         data = request.json
#         book_id = data.get('book_id')
#         quantity = data.get('quantity')

#         if not book_id or not quantity:
#             return {"error": "Missing required fields"}, 400

#         cart = Cart.query.filter_by(user_id=user_id).first()
#         if not cart:
#             cart = Cart(user_id=user_id)
#             db.session.add(cart)

#         order = Order(book_id=book_id, quantity=quantity, user_id=user_id)
#         db.session.add(order)
#         db.session.commit()

#         return order.to_dict(), 201

# Resource for handling Mpesa transactions.
class MpesaTransactionResource(Resource):
    @jwt_required()
    def post(self):
        user_id = get_jwt_identity()
        data = request.json
        amount = data.get('amount')

        if not amount:
            return {"error": "Amount is required"}, 400

        transaction = MpesaTransaction(amount=amount, user_id=user_id)
        db.session.add(transaction)
        db.session.commit()

        return transaction.to_dict(), 201

# Resource for viewing the user's orders (requires JWT authentication).
class UserOrders(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        orders = Order.query.filter_by(user_id=user_id).all()
        return [order.to_dict() for order in orders], 200

# Resource for viewing the user's borrowings (requires JWT authentication).
class UserBorrowings(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        borrowings = Borrowing.query.filter_by(user_id=user_id).all()
        return [borrowing.to_dict() for borrowing in borrowings], 200

# Admin resource to manage users.
class AdminUserList(Resource):
    @jwt_required()
    def get(self):
        if not is_admin():
            return {"error": "Admin privileges required"}, 403
        users = User.query.all()
        return [user.to_dict() for user in users], 200

# Admin resource to view transactions.
class AdminTransactionList(Resource):
    @jwt_required()
    def get(self):
        if not is_admin():
            return {"error": "Admin privileges required"}, 403
        transactions = MpesaTransaction.query.all()
        return [transaction.to_dict() for transaction in transactions], 200

# Admin resource to view all borrowings.
class AdminBorrowingList(Resource):
    @jwt_required()
    def get(self):
        if not is_admin():
            return {"error": "Admin privileges required"}, 403
        borrowings = Borrowing.query.all()
        return [borrowing.to_dict() for borrowing in borrowings], 200

# Admin logout (clears session, no JWT required).
class AdminLogout(Resource):
    def post(self):
        session.pop('user_id', None)
        return {"message": "Logged out successfully"}, 200

# Example Mpesa B2C Transaction Endpoint
@app.route('/transact/b2c', methods=['POST'])
def b2c_transact():
    data = {
        "initiator_name": os.environ.get("MPESA_INITIATOR_NAME"),
        "security_credential": os.environ.get("MPESA_SECURITY_CREDENTIAL"),
        "amount": request.json.get("amount", "1000"),
        "command_id": "BusinessPayment",
        "party_a": os.environ.get("MPESA_PARTY_A"),
        "party_b": request.json.get("party_b"),
        "remarks": "Test Payment",
        "queue_timeout_url": os.environ.get("MPESA_TIMEOUT_URL"),
        "result_url": os.environ.get("MPESA_RESULT_URL"),
        "occassion": "Test"
    }
    response = mpesa_api.B2C.transact(**data)
    return jsonify(response)

# Example Mpesa C2B Transaction Endpoint
@app.route('/transact/c2b', methods=['POST'])
def c2b_transact():
    reg_data = {
        "shortcode": os.environ.get("MPESA_SHORTCODE"),
        "response_type": "Completed",
        "confirmation_url": os.environ.get("MPESA_CONFIRMATION_URL"),
        "validation_url": os.environ.get("MPESA_VALIDATION_URL")
    }
    mpesa_api.C2B.register(**reg_data)
    
    test_data = {
        "shortcode": os.environ.get("MPESA_SHORTCODE"),
        "command_id": "CustomerPayBillOnline",
        "amount": request.json.get("amount", "100"),
        "msisdn": request.json.get("msisdn"),
        "bill_ref_number": "account"
    }
    response = mpesa_api.C2B.simulate(**test_data)
    return jsonify(response)

# Example MpesaExpress STK Push Endpoint
@app.route('/transact/mpesaexpress', methods=['POST'])
def simulate_stk_push():
    data = {
        "business_shortcode": os.environ.get("MPESA_BUSINESS_SHORTCODE"),
        "passcode": os.environ.get("MPESA_PASSCODE"),
        "amount": request.json.get("amount", "1"),
        "phone_number": request.json.get("phone_number"),
        "reference_code": "Order12345",
        "callback_url": os.environ.get("MPESA_CALLBACK_URL"),
        "description": "Test Transaction"
    }
    response = mpesa_api.MpesaExpress.stk_push(**data)
    return jsonify(response)

# Callback URL for MpesaExpress
@app.route('/callback-url', methods=["POST"])
def callback_url():
    json_data = request.get_json()
    result_code = json_data["Body"]["stkCallback"]["ResultCode"]
    if result_code == 0:
        print("Payment was successful")
    else:
        print("Payment failed")
    return jsonify(json_data)

# Add resources to the API
api.add_resource(Register, '/register')
api.add_resource(Login, '/login')
api.add_resource(CartResource, '/cart')
api.add_resource(MpesaTransactionResource, '/mpesa-transaction')
api.add_resource(UserOrders, '/user/orders')
api.add_resource(UserBorrowings, '/user/borrowings')
api.add_resource(AdminUserList, '/admin/users')
api.add_resource(AdminTransactionList, '/admin/transactions')
api.add_resource(AdminBorrowingList, '/admin/borrowings')
api.add_resource(AdminLogout, '/admin/logout')

if __name__ == "__main__":
    # Initialize )migrations and start the app
    migrate = Migrate(app, db)
    # Migrate(app, db)
    # CORS(app)
    # app.run(debug=True)


















# #!/usr/bin/env python3

# # Standard library imports
# # No standard library imports in this snippet, but this is where they would go.

# # Remote library imports
# from flask import request, session, jsonify, render_template # Flask imports for handling HTTP requests, sessions, and JSON responses.
# from flask_mpesa import MpesaAPI

# from flask_restful import Api, Resource  # Flask-Restful for creating RESTful API endpoints.
# from flask_migrate import Migrate  # Flask-Migrate to handle database migrations.
# from flask_cors import CORS  # Flask-CORS to handle Cross-Origin Resource Sharing (CORS).
# from flask_bcrypt import Bcrypt  # Flask-Bcrypt for password hashing and verification.
# from datetime import datetime  # For handling dates and times (though not used in this snippet).
# import os  # For interacting with the operating system (e.g., to load environment variables).
# from dotenv import load_dotenv  # To load environment variables from a .env file.

# # Load environment variables from .env file.
# load_dotenv()

# # Local imports
# from config import db, app, api  # Imports the Flask app, database object, and API instance from config.
# from models import User, Order, Borrowing, Cart, MpesaTransaction  # Imports models for interacting with the database.

# # Set secret key for sessions and configure database URI.
# app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')  # Secret key for managing sessions and cookies.
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI')  # URI for connecting to the database.
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disables Flask-SQLAlchemy event system for performance.



# # Mpesa configuration
# app.config["API_ENVIRONMENT"] = "sandbox"  # Set to 'production' for live transactions
# app.config["APP_KEY"] = os.environ.get("MPESA_APP_KEY")  # Set your App Key from .env
# app.config["APP_SECRET"] = os.environ.get("MPESA_APP_SECRET")  # Set your App Secret from .env


# # Initialize MpesaAPI
# mpesa_api = MpesaAPI(app)


# # Initialize bcrypt for hashing passwords.
# bcrypt = Bcrypt(app)

# # Helper function to check if the current user is an admin.
# def is_admin():
#     user_id = session.get('user_id')  # Retrieve the user ID from the session.
#     if not user_id:
#         return False  # If no user is logged in, return False.
#     user = User.query.get(user_id)  # Query the database for the user.
#     print("User ID:", user_id, "Is Admin:", user.is_admin if user else "No user found")  # Debugging line.
#     return user.is_admin if user else False  # Return True if the user is an admin, otherwise False.

# # Resource for user registration (registering a new user).
# class Register(Resource):
#     def post(self):
#         data = request.json  # Get data from the request body (expected to be JSON).
#         name = data.get('name')
#         email = data.get('email')
#         password = data.get('password')

#         # Validate the incoming data.
#         if not name or not email or not password:
#             return {"error": "Missing required fields"}, 400  # Return error if fields are missing.

#         if User.query.filter_by(email=email).first():
#             return {"error": "Email already exists"}, 400  # Return error if the email is already taken.

#         # Create the new user and hash the password.
#         user = User(name=name, email=email)
#         user.set_password(password)  # Method for setting the hashed password.
#         db.session.add(user)  # Add the user to the database session.
#         db.session.commit()  # Commit the transaction to save the user.

#         return user.to_dict(), 201  # Return the created user data.

# # Resource for user login (logging in an existing user).
# class Login(Resource):
#     def post(self):
#         data = request.json  # Get login data from the request.
#         email = data.get('email')
#         password = data.get('password')

#         user = User.query.filter_by(email=email).first()  # Check if a user exists with the provided email.
#         if user and user.check_password(password):  # Check if password matches.
#             session['user_id'] = user.id  # Store the user ID in the session.
#             session['user_name'] = user.name  # Store the user's name in the session.
#             return {"message": "Login successful", "user": user.to_dict()}, 200  # Return success message and user data.
#         else:
#             return {"error": "Invalid credentials"}, 401  # Return error if credentials are incorrect.

# # Resource for viewing and managing the user's cart.
# class CartResource(Resource):
#     def get(self):
#         user_id = session.get('user_id')  # Retrieve the user ID from the session.
#         if not user_id:
#             return {"error": "Unauthorized"}, 401  # Return error if the user is not logged in.

#         cart = Cart.query.filter_by(user_id=user_id).first()  # Retrieve the user's cart.
#         if not cart:
#             return {"error": "No cart found for user"}, 404  # Return error if no cart is found.

#         return cart.to_dict(), 200  # Return the cart data.

#     def post(self):
#         user_id = session.get('user_id')  # Retrieve the user ID from the session.
#         if not user_id:
#             return {"error": "Unauthorized"}, 401  # Return error if the user is not logged in.

#         data = request.json  # Get the request data.
#         book_id = data.get('book_id')
#         quantity = data.get('quantity')

#         if not book_id or not quantity:
#             return {"error": "Missing required fields"}, 400  # Return error if required fields are missing.

#         cart = Cart.query.filter_by(user_id=user_id).first()  # Check if the user already has a cart.
#         if not cart:
#             cart = Cart(user_id=user_id)  # Create a new cart if one doesn't exist.
#             db.session.add(cart)

#         order = Order(book_id=book_id, quantity=quantity, user_id=user_id)  # Create a new order.
#         db.session.add(order)  # Add the order to the session.
#         db.session.commit()  # Commit the transaction to save the order.

#         return order.to_dict(), 201  # Return the created order.

# # Resource for handling Mpesa transactions.
# class MpesaTransactionResource(Resource):
#     def post(self):
#         user_id = session.get('user_id')  # Retrieve the user ID from the session.
#         if not user_id:
#             return {"error": "Unauthorized"}, 401  # Return error if the user is not logged in.

#         data = request.json  # Get the request data.
#         amount = data.get('amount')

#         if not amount:
#             return {"error": "Amount is required"}, 400  # Return error if amount is not provided.

#         transaction = MpesaTransaction(amount=amount, user_id=user_id)  # Create a new transaction.
#         db.session.add(transaction)  # Add the transaction to the session.
#         db.session.commit()  # Commit the transaction to the database.

#         return transaction.to_dict(), 201  # Return the created transaction.

# # Resource for viewing the user's orders.
# class UserOrders(Resource):
#     def get(self):
#         user_id = session.get('user_id')  # Retrieve the user ID from the session.
#         if not user_id:
#             return {"error": "Unauthorized"}, 401  # Return error if the user is not logged in.

#         orders = Order.query.filter_by(user_id=user_id).all()  # Retrieve the user's orders.
#         return [order.to_dict() for order in orders], 200  # Return a list of orders.

# # Resource for viewing the user's borrowings.
# class UserBorrowings(Resource):
#     def get(self):
#         user_id = session.get('user_id')  # Retrieve the user ID from the session.
#         if not user_id:
#             return {"error": "Unauthorized"}, 401  # Return error if the user is not logged in.

#         borrowings = Borrowing.query.filter_by(user_id=user_id).all()  # Retrieve the user's borrowings.
#         return [borrowing.to_dict() for borrowing in borrowings], 200  # Return a list of borrowings.

# # Admin resource to manage users.
# class AdminUserList(Resource):
#     def get(self):
#         if not is_admin():  # Check if the current user is an admin.
#             return {"error": "Admin privileges required"}, 403  # Return error if not an admin.

#         users = User.query.all()  # Retrieve all users.
#         return [user.to_dict() for user in users], 200  # Return a list of users.

# # Admin resource to view transactions.
# class AdminTransactionList(Resource):
#     def get(self):
#         if not is_admin():  # Check if the current user is an admin.
#             return {"error": "Admin privileges required"}, 403  # Return error if not an admin.

#         transactions = MpesaTransaction.query.all()  # Retrieve all transactions.
#         return [transaction.to_dict() for transaction in transactions], 200  # Return a list of transactions.

# # Admin resource to view all borrowings.
# class AdminBorrowingList(Resource):
#     def get(self):
#         if not is_admin():  # Check if the current user is an admin.
#             return {"error": "Admin privileges required"}, 403  # Return error if not an admin.

#         borrowings = Borrowing.query.all()  # Retrieve all borrowings.
#         return [borrowing.to_dict() for borrowing in borrowings], 200  # Return a list of borrowings.

# # Admin logout.
# class AdminLogout(Resource):
#     def post(self):
#         session.pop('user_id', None)  # Remove the user ID from the session (logging out).
#         return {"message": "Logged out successfully"}, 200  # Return success message.



# # Example Mpesa B2C Transaction Endpoint
# @app.route('/transact/b2c', methods=['POST'])
# def b2c_transact():
#     data = {
#         "initiator_name": os.environ.get("MPESA_INITIATOR_NAME"),
#         "security_credential": os.environ.get("MPESA_SECURITY_CREDENTIAL"),
#         "amount": request.json.get("amount", "1000"),
#         "command_id": "BusinessPayment",
#         "party_a": os.environ.get("MPESA_PARTY_A"),  # Business short code
#         "party_b": request.json.get("party_b"),  # Customer phone number
#         "remarks": "Test Payment",
#         "queue_timeout_url": os.environ.get("MPESA_TIMEOUT_URL"),
#         "result_url": os.environ.get("MPESA_RESULT_URL"),
#         "occassion": "Test"
#     }
#     response = mpesa_api.B2C.transact(**data)
#     return jsonify(response)

# # Example Mpesa C2B Transaction Endpoint
# @app.route('/transact/c2b', methods=['POST'])
# def c2b_transact():
#     reg_data = {
#         "shortcode": os.environ.get("MPESA_SHORTCODE"),
#         "response_type": "Completed",
#         "confirmation_url": os.environ.get("MPESA_CONFIRMATION_URL"),
#         "validation_url": os.environ.get("MPESA_VALIDATION_URL")
#     }
#     mpesa_api.C2B.register(**reg_data)
    
#     test_data = {
#         "shortcode": os.environ.get("MPESA_SHORTCODE"),
#         "command_id": "CustomerPayBillOnline",
#         "amount": request.json.get("amount", "100"),
#         "msisdn": request.json.get("msisdn"),  # Customer phone number
#         "bill_ref_number": "account"
#     }
#     response = mpesa_api.C2B.simulate(**test_data)
#     return jsonify(response)

# # Example MpesaExpress STK Push Endpoint
# @app.route('/transact/mpesaexpress', methods=['POST'])
# def simulate_stk_push():
#     data = {
#         "business_shortcode": os.environ.get("MPESA_BUSINESS_SHORTCODE"),
#         "passcode": os.environ.get("MPESA_PASSCODE"),
#         "amount": request.json.get("amount", "1"),
#         "phone_number": request.json.get("phone_number"),
#         "reference_code": "Order12345",
#         "callback_url": os.environ.get("MPESA_CALLBACK_URL"),
#         "description": "Test Transaction"
#     }
#     response = mpesa_api.MpesaExpress.stk_push(**data)
#     return jsonify(response)

# # Callback URL for MpesaExpress
# @app.route('/callback-url', methods=["POST"])
# def callback_url():
#     json_data = request.get_json()
#     result_code = json_data["Body"]["stkCallback"]["ResultCode"]
    
#     # Store transaction status based on result_code (0 for success)
#     if result_code == 0:
#         # Process successful transaction data (e.g., save to database)
#         message = {
#             "ResultCode": 0,
#             "ResultDesc": "Success",
#             "ThirdPartyTransID": "YourTransactionID"
#         }
#     else:
#         # Handle failed transaction data
#         message = {
#             "ResultCode": 1,
#             "ResultDesc": "Failed"
#         }
#     return jsonify(message), 200





# # Add the API resources to the app
# api.add_resource(Register, '/register')  # Register resource at '/register'
# api.add_resource(Login, '/login')  # Login resource at '/login'
# api.add_resource(CartResource, '/cart')  # Cart resource at '/cart'
# api.add_resource(MpesaTransactionResource, '/mpesa-transaction')  # Mpesa transaction resource at '/mpesa-transaction'
# api.add_resource(UserOrders, '/orders')  # User orders resource at '/orders'
# api.add_resource(UserBorrowings, '/borrowings')  # User borrowings resource at '/borrowings'
# api.add_resource(AdminUserList, '/admin/users')  # Admin users resource at '/admin/users'
# api.add_resource(AdminTransactionList, '/admin/transactions')  # Admin transactions resource at '/admin/transactions'
# api.add_resource(AdminBorrowingList, '/admin/borrowings')  # Admin borrowings resource at '/admin/borrowings'
# api.add_resource(AdminLogout, '/admin/logout')  # Admin logout at '/admin/logout'

# # Initialize the database migration tool
# migrate = Migrate(app, db)



# # from flask import Flask
# # from flask_sqlalchemy import SQLAlchemy
# # from flask_bcrypt import Bcrypt
# # from config import Config
# # from models import db, bcrypt

# # app = Flask(__name__)
# # app.config.from_object(Config)

# # # Initialize extensions
# # db.init_app(app)
# # bcrypt.init_app(app)

# # # Create tables
# # with app.app_context():
# #     db.create_all()

# # if __name__ == "__main__":
# #     app.run(debug=True)
