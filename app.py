from flask import Flask, redirect, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

app = Flask(__name__)
app.secret_key = "super-secret-key-change-this"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ===================== MODELS =====================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    due_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    def is_overdue(self):
        return datetime.datetime.now() >= self.due_time


# ===================== AUTH ROUTES =====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect('/')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect('/')
        else:
            return render_template(
                'login.html',
                error="Invalid username or password"
            )

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# ===================== MAIN APP =====================

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    if request.method == 'POST':
        content = request.form['content']
        due_time = datetime.datetime.strptime(
            request.form['due_time'], "%Y-%m-%dT%H:%M"
        )

        task = Todo(
            content=content,
            due_time=due_time,
            user_id=user_id
        )
        db.session.add(task)
        db.session.commit()
        return redirect('/')

    tasks = (
        Todo.query
        .filter_by(user_id=user_id)
        .order_by(Todo.due_time)
        .all()
    )

    now = datetime.datetime.now()
    return render_template('index.html', tasks=tasks, now=now)


@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    if 'user_id' not in session:
        return redirect('/login')

    task = Todo.query.get_or_404(id)

    if task.user_id != session['user_id']:
        return redirect('/')

    if request.method == 'POST':
        task.content = request.form['content']
        task.due_time = datetime.datetime.strptime(
            request.form['due_time'], "%Y-%m-%dT%H:%M"
        )
        db.session.commit()
        return redirect('/')

    return render_template('update.html', task=task)


@app.route('/delete/<int:id>')
def delete(id):
    if 'user_id' not in session:
        return redirect('/login')

    task = Todo.query.get_or_404(id)

    if task.user_id != session['user_id']:
        return redirect('/')

    db.session.delete(task)
    db.session.commit()
    return redirect('/')


# ===================== RUN =====================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
