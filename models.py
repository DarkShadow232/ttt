from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    birth_date = db.Column(db.Date)
    address = db.Column(db.Text)
    medical_history = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # العلاقات
    examinations = db.relationship('Examination', backref='patient', lazy=True)
    invoices = db.relationship('Invoice', backref='patient', lazy=True)

class Examination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    examination_type = db.Column(db.String(50), nullable=False)
    result = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    performed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    report_path = db.Column(db.String(255))
    
    # العلاقات
    performer = db.relationship('User', backref='performed_examinations')

    EXAMINATION_TYPES = {
        'xray': 'أشعة سينية',
        'ct': 'أشعة مقطعية',
        'mri': 'رنين مغناطيسي',
        'ultrasound': 'موجات صوتية',
        'mammogram': 'تصوير الثدي',
        'dexa': 'قياس كثافة العظام'
    }

    def get_examination_type_display(self):
        return self.EXAMINATION_TYPES.get(self.examination_type, self.examination_type)

    @property
    def status_color(self):
        status_colors = {
            'pending': 'warning',
            'in_progress': 'info',
            'completed': 'success',
            'cancelled': 'danger'
        }
        return status_colors.get(self.status, 'secondary')

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    examination_id = db.Column(db.Integer, db.ForeignKey('examination.id'), unique=True)
    amount = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    notes = db.Column(db.Text)
    
    # العلاقات
    examination = db.relationship('Examination', backref='invoice', uselist=False)
    created_by_user = db.relationship('User', backref='created_invoices')
    payments = db.relationship('Payment', backref='invoice', lazy=True)

    @property
    def paid_amount(self):
        return sum(payment.amount for payment in self.payments) if self.payments else 0.0

    @property
    def total_amount(self):
        return self.amount - (self.discount or 0.0)

    @property
    def remaining_amount(self):
        return self.total_amount - self.paid_amount

    @property
    def status(self):
        if not self.paid_amount:
            return 'pending'
        elif self.paid_amount >= self.total_amount:
            return 'paid'
        else:
            return 'partially_paid'

    @property
    def status_color(self):
        status_colors = {
            'pending': 'danger',
            'partially_paid': 'warning',
            'paid': 'success'
        }
        return status_colors.get(self.status, 'secondary')

    @property
    def status_display(self):
        status_display = {
            'pending': 'غير مدفوع',
            'partially_paid': 'مدفوع جزئياً',
            'paid': 'مدفوع'
        }
        return status_display.get(self.status, self.status)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    notes = db.Column(db.Text)

    # العلاقات
    created_by_user = db.relationship('User', backref='created_payments')

    PAYMENT_METHODS = {
        'cash': 'نقداً',
        'card': 'بطاقة ائتمان',
        'transfer': 'تحويل بنكي'
    }

    @property
    def payment_method_display(self):
        return self.PAYMENT_METHODS.get(self.payment_method, self.payment_method)
