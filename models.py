from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


# -----------------------------
# User Model
# -----------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    expenses = db.relationship("Expense", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.name}>"


# -----------------------------
# Expense Model
# -----------------------------
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(100), nullable=False)

    amount = db.Column(db.Float, nullable=False)

    category = db.Column(db.String(50), nullable=False)

    expense_date = db.Column(
        db.Date,
        nullable=False,
        default=datetime.utcnow
    )

    description = db.Column(db.String(300))

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    def __repr__(self):
        return f"<Expense {self.title}>"


# -----------------------------
# Budget Model
# -----------------------------
class Budget(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    monthly_budget = db.Column(
        db.Float,
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
        unique=True
    )