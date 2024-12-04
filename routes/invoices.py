from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, Invoice, Patient, Examination, Payment
from forms import InvoiceForm, PaymentForm
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import func, exists

invoices_bp = Blueprint('invoices', __name__)

EXAMINATION_TYPES = {
    'xray': 'أشعة سينية',
    'ct': 'أشعة مقطعية',
    'mri': 'رنين مغناطيسي',
    'ultrasound': 'موجات صوتية',
    'mammogram': 'تصوير الثدي',
    'dexa': 'قياس كثافة العظام'
}

@invoices_bp.route('/invoices')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # فلترة الفواتير
    query = Invoice.query
    
    date_from = request.args.get('date_from')
    if date_from:
        query = query.filter(Invoice.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    
    date_to = request.args.get('date_to')
    if date_to:
        query = query.filter(Invoice.created_at <= datetime.strptime(date_to, '%Y-%m-%d'))
    
    status = request.args.get('status')
    if status:
        if status == 'pending':
            query = query.filter(~exists().where(Payment.invoice_id == Invoice.id))
        elif status == 'partially_paid':
            subq = db.session.query(
                Payment.invoice_id,
                func.sum(Payment.amount).label('total_paid')
            ).group_by(Payment.invoice_id).subquery()
            
            query = query.join(subq, Invoice.id == subq.c.invoice_id)
            query = query.filter(subq.c.total_paid < Invoice.amount)
        elif status == 'paid':
            subq = db.session.query(
                Payment.invoice_id,
                func.sum(Payment.amount).label('total_paid')
            ).group_by(Payment.invoice_id).subquery()
            
            query = query.join(subq, Invoice.id == subq.c.invoice_id)
            query = query.filter(subq.c.total_paid >= Invoice.amount)
    
    # حساب المجاميع
    totals = db.session.query(
        func.sum(Invoice.amount).label('total_amount'),
        func.sum(Invoice.discount).label('total_discount')
    ).first()
    
    payments_total = db.session.query(
        func.sum(Payment.amount).label('total_paid')
    ).first()
    
    total_amount = (totals.total_amount or 0) - (totals.total_discount or 0)
    total_paid = payments_total.total_paid or 0
    
    # جلب الفواتير مع الترقيم
    invoices = query.order_by(Invoice.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('invoices/index.html',
                         invoices=invoices,
                         total_amount=total_amount,
                         total_paid=total_paid,
                         examination_types=EXAMINATION_TYPES,
                         page=page)

@invoices_bp.route('/invoices/new/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def new(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = InvoiceForm()
    
    if form.validate_on_submit():
        invoice = Invoice(
            patient_id=patient_id,
            examination_id=form.examination_id.data,
            amount=form.total_amount.data,
            discount=form.discount.data or 0.0,
            created_by=current_user.id,
            notes=form.notes.data
        )
        
        if form.paid_amount.data > 0:
            payment = Payment(
                amount=form.paid_amount.data,
                payment_method=form.payment_method.data,
                created_by=current_user.id
            )
            invoice.payments.append(payment)
        
        db.session.add(invoice)
        db.session.commit()
        
        flash('تم إنشاء الفاتورة بنجاح', 'success')
        return redirect(url_for('invoices.view', id=invoice.id))
    
    return render_template('invoices/new.html', form=form, patient=patient)

@invoices_bp.route('/invoices/<int:id>')
@login_required
def view(id):
    invoice = Invoice.query.get_or_404(id)
    return render_template('invoices/view.html', invoice=invoice, examination_types=EXAMINATION_TYPES)

@invoices_bp.route('/invoices/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    invoice = Invoice.query.get_or_404(id)
    form = InvoiceForm(obj=invoice)
    
    if form.validate_on_submit():
        invoice.amount = form.total_amount.data
        invoice.discount = form.discount.data or 0.0
        invoice.notes = form.notes.data
        
        db.session.commit()
        flash('تم تحديث الفاتورة بنجاح', 'success')
        return redirect(url_for('invoices.view', id=invoice.id))
    
    return render_template('invoices/edit.html', form=form, invoice=invoice)

@invoices_bp.route('/invoices/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    invoice = Invoice.query.get_or_404(id)
    db.session.delete(invoice)
    db.session.commit()
    flash('تم حذف الفاتورة بنجاح', 'success')
    return redirect(url_for('invoices.index'))

@invoices_bp.route('/invoices/<int:id>/print')
@login_required
def print_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    return render_template('invoices/print.html', invoice=invoice, examination_types=EXAMINATION_TYPES)

@invoices_bp.route('/invoices/<int:id>/add-payment', methods=['POST'])
@login_required
def add_payment(id):
    invoice = Invoice.query.get_or_404(id)
    form = PaymentForm()
    
    if form.validate_on_submit():
        payment = Payment(
            invoice_id=id,
            amount=form.amount.data,
            payment_method=form.payment_method.data,
            notes=form.notes.data,
            created_by=current_user.id
        )
        db.session.add(payment)
        db.session.commit()
        
        flash('تم تسجيل الدفعة بنجاح', 'success')
        return redirect(url_for('invoices.view', id=invoice.id))
    
    return jsonify({'status': 'error', 'message': 'بيانات غير صحيحة'})
