from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from datetime import datetime, date
import os
from models import db, User, Patient, Examination, Invoice, Payment
from forms import LoginForm, UserForm, PatientForm, ExaminationForm, InvoiceForm
from werkzeug.utils import secure_filename
from routes.patients import patients_bp
from routes.examinations import examinations_bp
from routes.invoices import invoices_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # تغيير هذا في الإنتاج
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///radiology.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')

# إنشاء مجلد التحميلات إذا لم يكن موجوداً
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# تهيئة قاعدة البيانات
db.init_app(app)
migrate = Migrate(app, db)

# تهيئة نظام تسجيل الدخول
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# تسجيل Blueprints
app.register_blueprint(patients_bp)
app.register_blueprint(examinations_bp)
app.register_blueprint(invoices_bp)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.template_filter('strftime')
def _jinja2_filter_datetime(date, fmt=None):
    if not date:
        return ''
    if fmt:
        return date.strftime(fmt)
    return date.strftime('%Y-%m-%d %H:%M:%S')

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'error')
    return render_template('auth/login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/users', methods=['GET'])
@login_required
def users():
    if current_user.role != 'admin':
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('users/index.html', users=users)

@app.route('/users/new', methods=['GET', 'POST'])
@login_required
def new_user():
    if current_user.role != 'admin':
        flash('غير مصرح لك بالوصول إلى هذه الصفحة', 'danger')
        return redirect(url_for('index'))
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            name=form.name.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('تم إنشاء المستخدم بنجاح', 'success')
        return redirect(url_for('users'))
    return render_template('users/new.html', form=form)

@app.route('/patients', methods=['GET'])
@login_required
def patients():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    per_page = 10
    
    query = Patient.query
    if search:
        query = query.filter(
            db.or_(
                Patient.name.ilike(f'%{search}%'),
                Patient.phone.ilike(f'%{search}%')
            )
        )
    
    pagination = query.order_by(Patient.id.desc()).paginate(page=page, per_page=per_page)
    return render_template('patients/index.html',
                         patients=pagination.items,
                         page=page,
                         pages=pagination.pages,
                         today=datetime.now().date())

@app.route('/patients/new', methods=['GET', 'POST'])
@login_required
def new_patient():
    form = PatientForm()
    if form.validate_on_submit():
        patient = Patient(
            name=form.name.data,
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
            medical_history=form.medical_history.data
        )
        db.session.add(patient)
        db.session.commit()
        flash('تم إضافة المريض بنجاح', 'success')
        return redirect(url_for('patients'))
    return render_template('patients/new.html', form=form)

@app.route('/patients/<int:id>')
@login_required
def view_patient(id):
    patient = Patient.query.get_or_404(id)
    return render_template('patients/view.html', patient=patient)

@app.route('/patients/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(id):
    patient = Patient.query.get_or_404(id)
    form = PatientForm(obj=patient)
    if form.validate_on_submit():
        form.populate_obj(patient)
        db.session.commit()
        flash('تم تحديث بيانات المريض بنجاح', 'success')
        return redirect(url_for('patients'))
    return render_template('patients/edit.html', form=form, patient=patient)

@app.route('/patients/<int:id>/medical-record')
@login_required
def patient_medical_record(id):
    patient = Patient.query.get_or_404(id)
    examinations = Examination.query.filter_by(patient_id=id).order_by(Examination.created_at.desc()).all()
    return render_template('patients/medical_record.html',
                         patient=patient,
                         examinations=examinations,
                         today=datetime.now().date())

@app.route('/patients/<int:id>', methods=['DELETE'])
@login_required
def delete_patient(id):
    patient = Patient.query.get_or_404(id)
    db.session.delete(patient)
    db.session.commit()
    return {'success': True}

@app.route('/appointments')
@login_required
def appointments():
    page = request.args.get('page', 1, type=int)
    date = request.args.get('date')
    exam_type = request.args.get('type')
    status = request.args.get('status')
    per_page = 10
    
    # قائمة فارغة مؤقتاً حتى يتم تنفيذ نظام المواعيد
    appointments = []
    pages = 1
    page = 1
    
    return render_template('appointments/index.html',
                         appointments=appointments,
                         page=page,
                         pages=pages)

@app.route('/appointments/new', methods=['GET', 'POST'])
@login_required
def new_appointment():
    return redirect(url_for('appointments'))

@app.route('/appointments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_appointment(id):
    return redirect(url_for('appointments'))

@app.route('/appointments/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(id):
    return {'success': True}

@app.route('/appointments/<int:appointment_id>/examination', methods=['GET', 'POST'])
@login_required
def create_examination_from_appointment(appointment_id):
    return redirect(url_for('appointments'))

@app.route('/invoices', methods=['GET'])
@login_required
def invoices():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # تصفية الفواتير
    query = Invoice.query
    
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    status = request.args.get('status')
    
    if date_from:
        query = query.filter(Invoice.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(Invoice.created_at <= datetime.strptime(date_to, '%Y-%m-%d'))
    if status:
        query = query.filter_by(status=status)
    
    # إحصائيات
    total_amount = db.session.query(db.func.sum(Invoice.amount)).scalar() or 0
    total_paid = db.session.query(db.func.sum(Payment.amount)).scalar() or 0
    
    # قائمة الفواتير مع الترقيم
    pagination = query.order_by(Invoice.created_at.desc()).paginate(page=page, per_page=per_page)
    
    examination_types = {
        'xray': 'أشعة سينية',
        'mri': 'رنين مغناطيسي',
        'ct': 'أشعة مقطعية',
        'ultrasound': 'موجات صوتية',
        'blood_test': 'تحليل دم',
        'urine_test': 'تحليل بول'
    }
    
    return render_template('invoices/index.html',
                         invoices=pagination.items,
                         page=page,
                         pages=pagination.pages,
                         total_amount=total_amount,
                         total_paid=total_paid,
                         examination_types=examination_types)

@app.route('/invoices/new', methods=['GET', 'POST'])
@login_required
def new_invoice():
    patient_id = request.args.get('patient_id', type=int)
    form = InvoiceForm(patient_id=patient_id) if patient_id else InvoiceForm()
    
    if form.validate_on_submit():
        invoice = Invoice(
            patient_id=form.patient_id.data,
            examination_id=form.examination_id.data,
            amount=form.amount.data,
            discount=form.discount.data or 0,
            notes=form.notes.data,
            created_by=current_user.id
        )
        db.session.add(invoice)
        db.session.commit()
        
        flash('تم إنشاء الفاتورة بنجاح', 'success')
        return redirect(url_for('invoices'))
    
    return render_template('invoices/new.html', form=form)

@app.route('/invoices/<int:id>')
@login_required
def view_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    return render_template('invoices/view.html', invoice=invoice)

@app.route('/invoices/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    form = InvoiceForm(obj=invoice)
    
    if form.validate_on_submit():
        invoice.amount = form.amount.data
        invoice.discount = form.discount.data
        invoice.notes = form.notes.data
        
        db.session.commit()
        flash('تم تحديث الفاتورة بنجاح', 'success')
        return redirect(url_for('view_invoice', id=id))
    
    return render_template('invoices/edit.html', form=form, invoice=invoice)

@app.route('/invoices/<int:id>/payment', methods=['POST'])
@login_required
def add_payment(id):
    invoice = Invoice.query.get_or_404(id)
    
    if invoice.status == 'paid':
        return {'success': False, 'message': 'الفاتورة مدفوعة بالكامل'}
    
    amount = float(request.form.get('amount', 0))
    if amount <= 0:
        return {'success': False, 'message': 'المبلغ غير صحيح'}
    
    payment = Payment(
        invoice=invoice,
        amount=amount,
        payment_method=request.form.get('payment_method'),
        notes=request.form.get('notes'),
        created_by=current_user.id
    )
    
    db.session.add(payment)
    db.session.commit()
    
    return {'success': True}

@app.route('/invoices/<int:id>/print')
@login_required
def print_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    return render_template('invoices/print.html', invoice=invoice)

@app.route('/api/patients/<int:id>/examinations')
@login_required
def get_patient_examinations(id):
    examinations = Examination.query.filter_by(patient_id=id).order_by(Examination.created_at.desc()).all()
    return [{
        'id': e.id,
        'type': e.examination_type,
        'date': e.created_at.strftime('%Y-%m-%d')
    } for e in examinations]

@app.route('/reports/analytics')
@login_required
def analytics_report():
    # استخراج معايير التصفية
    date_from = request.args.get('date_from', 
                               (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

    # حساب مؤشرات الأداء الرئيسية
    query = Invoice.query.filter(
        Invoice.created_at.between(date_from, date_to)
    )
    
    avg_invoice_amount = query.with_entities(
        db.func.avg(Invoice.amount)
    ).scalar() or 0
    
    kpis = {
        'avg_invoice_amount': avg_invoice_amount
    }
    
    return render_template('reports/analytics.html', kpis=kpis)

@app.route('/reports/financial')
@login_required
def financial_report():
    # استخراج معايير التصفية
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    # إنشاء الاستعلام الأساسي
    query = Invoice.query

    # تطبيق الفلترة
    if date_from:
        query = query.filter(Invoice.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(Invoice.created_at <= datetime.strptime(date_to, '%Y-%m-%d'))

    # حساب الإحصائيات
    total_amount = query.with_entities(db.func.sum(Invoice.amount)).scalar() or 0
    total_payments = db.session.query(db.func.sum(Payment.amount)).join(Invoice).filter(
        query.whereclause if query.whereclause is not None else True
    ).scalar() or 0
    total_payments_count = db.session.query(Payment).join(Invoice).filter(
        query.whereclause if query.whereclause is not None else True
    ).count()
    
    # حساب المبالغ المستحقة والمتأخرة
    today = datetime.now().date()
    due_invoices = query.filter(Invoice.status.in_(['pending', 'partially_paid'])).all()
    
    total_due = 0
    total_overdue = 0
    total_due_count = 0
    total_overdue_count = 0
    
    for invoice in due_invoices:
        remaining = invoice.amount - invoice.paid_amount - invoice.discount
        if remaining > 0:
            total_due += remaining
            total_due_count += 1
            if (today - invoice.created_at.date()).days > 30:  # اعتبار الفاتورة متأخرة بعد 30 يوم
                total_overdue += remaining
                total_overdue_count += 1
    
    stats = {
        'total_amount': total_amount,
        'total_payments': total_payments,
        'total_payments_count': total_payments_count,
        'total_due': total_due,
        'total_due_count': total_due_count,
        'total_overdue': total_overdue,
        'total_overdue_count': total_overdue_count
    }
    
    # تجهيز بيانات التقرير
    reports = []
    invoices = query.order_by(Invoice.created_at.desc()).all()
    
    for invoice in invoices:
        reports.append({
            'invoice_number': invoice.id,
            'date': invoice.created_at.strftime('%Y-%m-%d'),
            'amount': invoice.amount,
            'payment_status': invoice.status_display,
            'examination_type': examination_types[invoice.examination.examination_type]
        })
    
    return render_template('reports/financial.html',
                         stats=stats,
                         reports=reports)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
