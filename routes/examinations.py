from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models import db, Examination, Patient
from forms import ExaminationForm
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import date

examinations_bp = Blueprint('examinations', __name__)

@examinations_bp.route('/examinations')
@login_required
def index():
    examinations = Examination.query.order_by(Examination.created_at.desc()).all()
    return render_template('examinations/index.html', examinations=examinations)

@examinations_bp.route('/examinations/new/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def new(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    form = ExaminationForm()
    
    if form.validate_on_submit():
        examination = Examination(
            patient_id=patient_id,
            examination_type=form.examination_type.data,
            result=form.result.data,
            recommendations=form.recommendations.data,
            performed_by=current_user.id,
            status='completed'
        )
        
        if form.report_file.data:
            file = form.report_file.data
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            examination.report_path = filename
        
        db.session.add(examination)
        db.session.commit()
        
        flash('تم إضافة الفحص بنجاح', 'success')
        return redirect(url_for('patients.medical_record', id=patient_id))
    
    return render_template('examinations/new.html', form=form, patient=patient)

@examinations_bp.route('/examinations/<int:id>')
@login_required
def view(id):
    examination = Examination.query.get_or_404(id)
    return render_template('examinations/view.html', examination=examination)

@examinations_bp.route('/examinations/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    examination = Examination.query.get_or_404(id)
    form = ExaminationForm(obj=examination)
    
    if form.validate_on_submit():
        examination.examination_type = form.examination_type.data
        examination.result = form.result.data
        examination.recommendations = form.recommendations.data
        
        if form.report_file.data:
            # حذف الملف القديم إذا وجد
            if examination.report_path:
                old_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], examination.report_path)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            
            # حفظ الملف الجديد
            file = form.report_file.data
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            examination.report_path = filename
        
        db.session.commit()
        flash('تم تحديث الفحص بنجاح', 'success')
        return redirect(url_for('examinations.view', id=examination.id))
    
    return render_template('examinations/edit.html', form=form, examination=examination)

@examinations_bp.route('/examinations/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    examination = Examination.query.get_or_404(id)
    patient_id = examination.patient_id
    
    # حذف ملف التقرير إذا وجد
    if examination.report_path:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], examination.report_path)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    db.session.delete(examination)
    db.session.commit()
    
    flash('تم حذف الفحص بنجاح', 'success')
    return redirect(url_for('patients.medical_record', id=patient_id))
