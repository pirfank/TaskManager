from flask import Flask, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    due_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def is_overdue(self):
        return datetime.datetime.now() >= self.due_time

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        content = request.form['content']
        due_time = datetime.datetime.strptime(
            request.form['due_time'], "%Y-%m-%dT%H:%M"
        )
        task = Todo(content=content, due_time=due_time)
        db.session.add(task)
        db.session.commit()
        return redirect('/')

    tasks = Todo.query.order_by(Todo.due_time).all()
    now = datetime.datetime.now()
    return render_template('index.html', tasks=tasks, now=now)

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task = Todo.query.get_or_404(id)

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
    task = Todo.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return redirect('/')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
