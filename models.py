# -*- coding: utf-8 -*-

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import logging

db = SQLAlchemy()

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    
    # Права доступа
    can_manage_users = db.Column(db.Boolean, default=False)
    can_manage_slots = db.Column(db.Boolean, default=False)
    can_confirm_visits = db.Column(db.Boolean, default=False)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Связи
    role = db.relationship('Role', backref=db.backref('users', lazy=True))
    
    def set_password(self, password):
        logging.info(f"Setting password for user {self.username}")
        self.password_hash = generate_password_hash(password)
        logging.info(f"Password hash: {self.password_hash}")
    
    def check_password(self, password):
        logging.info(f"Checking password for user {self.username}")
        logging.info(f"Stored hash: {self.password_hash}")
        result = check_password_hash(self.password_hash, password)
        logging.info(f"Password check result: {result}")
        return result

class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True)
    telegram_id = db.Column(db.String(50), unique=True)
    subscription_balance = db.Column(db.Integer, default=0)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)

class DailySlot(db.Model):
    __tablename__ = 'daily_slots'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    total_slots = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='Открыт')  # Открыт, Закрыт
    reason = db.Column(db.String(255), nullable=True)  # Причина закрытия

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    daily_slot_id = db.Column(db.Integer, db.ForeignKey('daily_slots.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Ожидание')
    confirmed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Связи
    client = db.relationship('Client', backref=db.backref('bookings', lazy=True))
    daily_slot = db.relationship('DailySlot', backref=db.backref('bookings', lazy=True))
    confirmed_by = db.relationship('User', backref=db.backref('confirmed_bookings', lazy=True))

class Visit(db.Model):
    __tablename__ = 'visits'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    visit_date = db.Column(db.DateTime, nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=True)
    confirmed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    client = db.relationship('Client', backref=db.backref('visits', lazy=True))
    booking = db.relationship('Booking', backref=db.backref('visit', uselist=False))
    confirmed_by = db.relationship('User', backref=db.backref('confirmed_visits', lazy=True))

class SubscriptionLog(db.Model):
    __tablename__ = 'subscription_logs'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # purchase, deduction, etc.
    amount = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    client = db.relationship('Client', backref=db.backref('subscription_logs', lazy=True))
    user = db.relationship('User', backref=db.backref('subscription_actions', lazy=True))
