from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_mail import Mail, Message
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)

# Configure application settings
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME")

# Initialize extensions
db = SQLAlchemy(app)
mail = Mail(app)

# Validate environment variables
def validate_env_vars():
    required_vars = ["MAIL_USERNAME", "MAIL_PASSWORD"]
    for var in required_vars:
        if not os.getenv(var):
            raise RuntimeError(f"Missing required environment variable: {var}")

validate_env_vars()

# Define database models
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"

# Create database tables
with app.app_context():
    db.create_all()

# Utility function to send email notifications
def send_admin_notification(subject, body):
    try:
        msg = Message(subject, recipients=["samiraroble02@gmail.com"])
        msg.body = body
        mail.send(msg)
    except Exception as e:
        app.logger.error(f"Failed to send email: {e}")

# Routes
@app.route("/api/signup", methods=["POST"])
def signup():
    try:
        data = request.json
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not all([username, email, password]):
            return jsonify({"error": "All fields are required"}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already exists"}), 400

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": f"Welcome {username}, your signup was successful!"}), 201

    except Exception as e:
        app.logger.error(f"Signup error: {e}")
        return jsonify({"error": "An error occurred during signup. Please try again later."}), 500

@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.json
        email = data.get("email")
        password = data.get("password")

        if not all([email, password]):
            return jsonify({"error": "Email and password are required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user or not bcrypt.check_password_hash(user.password, password):
            return jsonify({"error": "Invalid email or password"}), 401

        return jsonify({"message": "Login successful", "user": {"username": user.username, "email": user.email}}), 200

    except Exception as e:
        app.logger.error(f"Login error: {e}")
        return jsonify({"error": "An error occurred during login. Please try again later."}), 500

@app.route("/api/contact", methods=["POST"])
def contact_us():
    try:
        data = request.json
        subject = data.get("subject", "No Subject")
        message = data.get("message", "")
        sender_email = data.get("email", "")

        if not message or not sender_email:
            return jsonify({"error": "Message and email are required"}), 400

        msg = Message(subject=subject, recipients=["samiraroble02@gmail.com"])
        msg.body = f"Message from: {sender_email}\n\n{message}"
        mail.send(msg)

        return jsonify({"message": "Message sent successfully!"}), 200

    except Exception as e:
        app.logger.error(f"Error sending contact message: {e}")
        return jsonify({"error": "Failed to send the message. Please try again later."}), 500

@app.route("/api/checkout", methods=["POST"])
def checkout():
    try:
        data = request.json
        full_name = data.get("full_name")
        email = data.get("email")
        address = data.get("address")
        payment_method = data.get("payment_method")
        cart_items = data.get("cart_items", [])

        if not all([full_name, email, address, payment_method]) or not cart_items:
            app.logger.error(f"Validation failed: {data}")
            return jsonify({"error": "All fields and cart items are required"}), 400

        send_admin_notification(
            subject="New Order Received",
            body=f"Customer: {full_name}\nEmail: {email}\nAddress: {address}\nPayment Method: {payment_method}\nItems: {cart_items}",
        )

        return jsonify({"message": "Order placed successfully!"}), 201

    except Exception as e:
        app.logger.error(f"Error processing checkout: {e}")
        return jsonify({"error": "Failed to place the order. Please try again later."}), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)
