from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    Response
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import csv
import io


app = Flask(__name__)

# -----------------------------
# Configuration
# -----------------------------
app.config["SECRET_KEY"] = "mysecretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///expense.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -----------------------------
# Login Manager
# -----------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

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

    monthly_budget = db.Column(db.Float, nullable=False)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
        unique=True
    )
    # -----------------------------
# Category Model
# -----------------------------
class Category(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(50), nullable=False)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    def __repr__(self):
        return f"<Category {self.name}>"


# -----------------------------
# Load User
# -----------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -----------------------------
# Home
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# About
# -----------------------------
@app.route("/about")
def about():
    return render_template("about.html")


# -----------------------------
# Contact
# -----------------------------
@app.route("/contact")
def contact():
    return render_template("contact.html")


# -----------------------------
# Register
# -----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Email already registered!", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration Successful! Please Login.", "success")

        return redirect(url_for("login"))

    return render_template("register.html")


# -----------------------------
# Login
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            login_user(user)

            flash("Login Successful!", "success")

            return redirect(url_for("dashboard"))

        flash("Invalid Email or Password", "danger")

    return render_template("login.html")

# -----------------------------
# Dashboard
# -----------------------------
@app.route("/dashboard")
@login_required
def dashboard():

    expenses = Expense.query.filter_by(
        user_id=current_user.id
    ).all()

    total_expenses = len(expenses)

    total_amount = sum(exp.amount for exp in expenses)

    # Expense Summary
    highest_expense = max(
        expenses,
        key=lambda x: x.amount,
        default=None
    )

    lowest_expense = min(
        expenses,
        key=lambda x: x.amount,
        default=None
    )

    average_expense = (
        total_amount / total_expenses
        if total_expenses > 0
        else 0
    )

    total_categories = len(
        set(exp.category for exp in expenses)
    )

    latest_expense = Expense.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Expense.expense_date.desc()
    ).first()

    # Budget Information
    budget = Budget.query.filter_by(
        user_id=current_user.id
    ).first()

    budget_amount = budget.monthly_budget if budget else 0

    remaining_budget = budget_amount - total_amount

    return render_template(
        "dashboard.html",
        total_expenses=total_expenses,
        total_amount=total_amount,
        total_categories=total_categories,
        latest_expense=latest_expense,
        budget_amount=budget_amount,
        remaining_budget=remaining_budget,
        highest_expense=highest_expense,
        lowest_expense=lowest_expense,
        average_expense=average_expense
    )

# -----------------------------
# Add Expense
# -----------------------------
@app.route("/add-expense", methods=["GET", "POST"])
@login_required
def add_expense():

    if request.method == "POST":

        title = request.form["title"]

        amount = float(request.form["amount"])

        category = request.form["category"]

        expense_date = datetime.strptime(
            request.form["expense_date"],
            "%Y-%m-%d"
        ).date()

        description = request.form["description"]

        expense = Expense(
            title=title,
            amount=amount,
            category=category,
            expense_date=expense_date,
            description=description,
            user_id=current_user.id
        )

        db.session.add(expense)

        db.session.commit()

        flash("Expense Added Successfully!", "success")

        return redirect(url_for("dashboard"))

    return render_template("add_expense.html")
# -----------------------------
# Set Budget
# -----------------------------
@app.route("/set-budget", methods=["GET", "POST"])
@login_required
def set_budget():

    budget = Budget.query.filter_by(
        user_id=current_user.id
    ).first()

    if request.method == "POST":

        amount = float(request.form["monthly_budget"])

        if budget:

            budget.monthly_budget = amount

        else:

            budget = Budget(
                monthly_budget=amount,
                user_id=current_user.id
            )

            db.session.add(budget)

        db.session.commit()

        flash("Budget Saved Successfully!", "success")

        return redirect(url_for("dashboard"))

    return render_template(
        "set_budget.html",
        budget=budget
    )
# -----------------------------
# Manage Categories
# -----------------------------
@app.route("/categories", methods=["GET", "POST"])
@login_required
def categories():

    if request.method == "POST":

        category_name = request.form["name"].strip()

        existing = Category.query.filter_by(
            name=category_name,
            user_id=current_user.id
        ).first()

        if existing:

            flash("Category already exists!", "warning")

        else:

            new_category = Category(
                name=category_name,
                user_id=current_user.id
            )

            db.session.add(new_category)
            db.session.commit()

            flash("Category Added Successfully!", "success")

        return redirect(url_for("categories"))

    categories = Category.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        "categories.html",
        categories=categories
    )
# -----------------------------
# View Expenses
# -----------------------------
@app.route("/expenses")
@login_required
def expenses():

    search = request.args.get("search", "")
    category = request.args.get("category", "")
    expense_date = request.args.get("expense_date", "")

    query = Expense.query.filter_by(user_id=current_user.id)

    if search:
        query = query.filter(
            Expense.title.ilike(f"%{search}%")
        )

    if category:
        query = query.filter_by(category=category)

    if expense_date:
        query = query.filter_by(expense_date=expense_date)

    expenses = query.order_by(
        Expense.expense_date.desc()
    ).all()

    total_amount = sum(exp.amount for exp in expenses)

    categories = db.session.query(
        Expense.category
    ).filter_by(
        user_id=current_user.id
    ).distinct().all()

    categories = [c[0] for c in categories]

    return render_template(
        "expenses.html",
        expenses=expenses,
        total_amount=total_amount,
        categories=categories
    )
# -----------------------------
# Monthly Report
# -----------------------------
@app.route("/monthly-report", methods=["GET", "POST"])
@login_required
def monthly_report():

    expenses = []
    total_amount = 0
    selected_month = ""

    if request.method == "POST":

        selected_month = request.form["month"]

        year, month = selected_month.split("-")

        expenses = Expense.query.filter(
            Expense.user_id == current_user.id,
            db.extract("year", Expense.expense_date) == int(year),
            db.extract("month", Expense.expense_date) == int(month)
        ).all()

        total_amount = sum(exp.amount for exp in expenses)

    return render_template(
        "monthly_report.html",
        expenses=expenses,
        total_amount=total_amount,
        selected_month=selected_month
    )
# -----------------------------
# User Profile
# -----------------------------
# -----------------------------
# User Profile
# -----------------------------
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    if request.method == "POST":

        current_user.name = request.form["name"]

        current_user.email = request.form["email"]

        new_password = request.form["password"]

        if new_password.strip() != "":
            current_user.password = generate_password_hash(new_password)

        db.session.commit()

        flash("Profile Updated Successfully!", "success")

        return redirect(url_for("profile"))

    return render_template("profile.html")
# -----------------------------
# Edit Expense
# -----------------------------
@app.route("/edit-expense/<int:id>", methods=["GET", "POST"])
@login_required
def edit_expense(id):

    expense = Expense.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    if request.method == "POST":

        expense.title = request.form["title"]

        expense.amount = float(request.form["amount"])

        expense.category = request.form["category"]

        expense.expense_date = datetime.strptime(
            request.form["expense_date"],
            "%Y-%m-%d"
        ).date()

        expense.description = request.form["description"]

        db.session.commit()

        flash("Expense Updated Successfully!", "success")

        return redirect(url_for("expenses"))

    return render_template(
        "edit_expense.html",
        expense=expense
    )

# -----------------------------
# Export Expenses to CSV
# -----------------------------
@app.route("/export-csv")
@login_required
def export_csv():

    expenses = Expense.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Expense.expense_date.desc()
    ).all()

    output = io.StringIO()

    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Title",
        "Amount",
        "Category",
        "Date",
        "Description"
    ])

    # Data
    for expense in expenses:
        writer.writerow([
            expense.title,
            expense.amount,
            expense.category,
            expense.expense_date,
            expense.description
        ])

    csv_data = output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=expenses.csv"
        }
    )
# -----------------------------
# Delete Expense
# -----------------------------
@app.route("/delete-expense/<int:id>")
@login_required
def delete_expense(id):

    expense = Expense.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(expense)

    db.session.commit()

    flash("Expense Deleted Successfully!", "success")

    return redirect(url_for("expenses"))


# -----------------------------
# Logout
# -----------------------------
@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged Out Successfully!", "info")

    return redirect(url_for("home"))


# -----------------------------
# Create Database Tables
# -----------------------------
with app.app_context():
    db.create_all()

# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)