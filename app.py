from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your_very_long_and_very_secret_key_here123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pool.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Модели базы данных
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin' или 'user'

    def is_admin(self):
        return self.role == 'admin'

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    telegram_id = db.Column(db.String(50), unique=True)
    subscription_balance = db.Column(db.Integer, default=0)

class DailySlots(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    total_slots = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    visit_date = db.Column(db.DateTime, nullable=False)
    client = db.relationship('Client', backref=db.backref('visits', lazy=True))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('У вас нет прав для выполнения этого действия', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Admin.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        
        flash('Неверное имя пользователя или пароль')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/slots', methods=['GET', 'POST'])
@login_required
def manage_slots():
    if request.method == 'POST':
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        total_slots = int(request.form['total_slots'])
        
        slot = DailySlots.query.filter_by(date=date).first()
        if slot:
            slot.total_slots = total_slots
            slot.available_slots = total_slots
        else:
            slot = DailySlots(date=date, total_slots=total_slots, available_slots=total_slots)
            db.session.add(slot)
        
        db.session.commit()
        flash('Количество мест обновлено')
        return redirect(url_for('manage_slots'))
    
    slots = DailySlots.query.all()
    return render_template('slots.html', slots=slots)

@app.route('/visits')
@login_required
def visits_history():
    visits = Visit.query.order_by(Visit.visit_date.desc()).all()
    return render_template('visits.html', visits=visits)

@app.route('/clients')
@login_required
def clients():
    all_clients = Client.query.all()
    return render_template('clients.html', clients=all_clients)

@app.route('/client/<int:client_id>/add_visits', methods=['POST'])
@login_required
@admin_required
def add_visits(client_id):
    client = Client.query.get_or_404(client_id)
    visits = int(request.form['visits'])
    client.subscription_balance += visits
    db.session.commit()
    flash(f'Добавлено {visits} посещений', 'success')
    return redirect(url_for('clients'))

@app.route('/client/<int:client_id>/deduct', methods=['POST'])
@login_required
def deduct_visit(client_id):
    client = Client.query.get_or_404(client_id)
    if client.subscription_balance > 0:
        client.subscription_balance -= 1
        visit = Visit(client_id=client.id, visit_date=datetime.now())
        db.session.add(visit)
        db.session.commit()
        flash('Посещение списано')
    else:
        flash('Недостаточно посещений на абонементе', 'error')
    return redirect(url_for('clients'))

@app.route('/client/<int:client_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    try:
        Visit.query.filter_by(client_id=client.id).delete()
        db.session.delete(client)
        db.session.commit()
        flash('Клиент успешно удален', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Ошибка при удалении клиента', 'error')
        print(f"Error deleting client: {e}")
    return redirect(url_for('clients'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Создаем администратора и обычного пользователя по умолчанию
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(
                username='admin',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
        
        if not Admin.query.filter_by(username='user').first():
            user = Admin(
                username='user',
                password=generate_password_hash('user123'),
                role='user'
            )
            db.session.add(user)
            db.session.commit()

    app.run(debug=True)
