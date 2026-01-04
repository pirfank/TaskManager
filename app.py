from flask import Flask, render_template, request, redirect, session, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import os

app = Flask(__name__)

# ---------------- CONFIG ----------------
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///taskmanager.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

db = SQLAlchemy(app)

SESSION_USER_KEY = "uid"

# ---------------- MODELS ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    nickname = db.Column(db.String(100), nullable=False)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    due_time = db.Column(db.DateTime, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

# ---------------- DB INIT ----------------
with app.app_context():
    db.create_all()

# ---------------- HELPERS ----------------
def login_required():
    if SESSION_USER_KEY not in session:
        return False
    return True

# ---------------- ROUTES ----------------
@app.route("/", methods=["GET", "POST"])
def home():
    if not login_required():
        return redirect("/login")

    uid = session[SESSION_USER_KEY]
    user = User.query.get(uid)

    if request.method == "POST":
        content = request.form.get("content", "").strip()
        due_time_raw = request.form.get("due_time", "")

        if not content or len(content) > 500:
            abort(400, "Invalid task content")

        try:
            due_time = datetime.datetime.strptime(due_time_raw, "%Y-%m-%dT%H:%M")
        except ValueError:
            abort(400, "Invalid date format")

        task = Todo(
            content=content,
            due_time=due_time,
            user_id=uid
        )
        db.session.add(task)
        db.session.commit()
        return redirect("/")

    tasks = Todo.query.filter_by(user_id=uid).order_by(Todo.due_time).all()
    return render_template("index.html", tasks=tasks, nickname=user.nickname)

# ---------------- AUTH ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        nickname = request.form.get("nickname", "").strip()

        if not username or not password or not nickname:
            abort(400, "All fields required")

        if len(password) < 6:
            abort(400, "Password too short")

        if User.query.filter_by(username=username).first():
            abort(400, "Username already exists")

        hashed = generate_password_hash(password)

        user = User(
            username=username,
            password=hashed,
            nickname=nickname
        )
        db.session.add(user)
        db.session.commit()
        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password, password):
            abort(401, "Invalid credentials")

        session[SESSION_USER_KEY] = user.id
        return redirect("/")

    return render_template("login.html")

@app.route("/logout", methods=["POST"])
def logout():
    session.pop(SESSION_USER_KEY, None)
    return redirect("/login")

# ---------------- TASK ACTIONS ----------------
@app.route("/complete/<int:id>")
def complete(id):
    if not login_required():
        return redirect("/login")

    task = Todo.query.filter_by(
        id=id,
        user_id=session[SESSION_USER_KEY]
    ).first_or_404()

    task.completed = not task.completed
    db.session.commit()
    return redirect("/")

@app.route("/delete/<int:id>")
def delete(id):
    if not login_required():
        return redirect("/login")

    task = Todo.query.filter_by(
        id=id,
        user_id=session[SESSION_USER_KEY]
    ).first_or_404()

    db.session.delete(task)
    db.session.commit()
    return redirect("/")
@app.route("/update/<int:id>", methods=["GET", "POST"])
def update(id):
    if "uid" not in session:
        return redirect("/login")

    task = Todo.query.filter_by(
        id=id,
        user_id=session["uid"]
    ).first_or_404()

    if request.method == "POST":
        content = request.form.get("content", "").strip()
        due_time_raw = request.form.get("due_time", "")

        if not content:
            return "Task content cannot be empty", 400

        try:
            due_time = datetime.datetime.strptime(
                due_time_raw, "%Y-%m-%dT%H:%M"
            )
        except ValueError:
            return "Invalid date format", 400

        task.content = content
        task.due_time = due_time
        db.session.commit()

        return redirect("/")

    return render_template("update.html", task=task)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)

