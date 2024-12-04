from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import Patient, db
from forms import PatientForm
from flask_login import login_required
from datetime import datetime, date

patients_bp = Blueprint('patients', __name__)

@patients_bp.route('/patients')
@login_required
def index():
    patients = Patient.query.all()
    return render_template('patients/index.html', patients=patients, today=date.today())

@patients_bp.route('/patients/<int:id>')
@login_required
def view(id):
    try:
        patient = Patient.query.get_or_404(id)
        return render_template('patients/view.html', patient=patient, today=date.today())
    except Exception as e:
        print(f"Error in view route: {str(e)}")  # Debug print
        flash('حدث خطأ أثناء عرض بيانات المريض', 'danger')
        return redirect(url_for('patients.index'))

@patients_bp.route('/patients/create', methods=['GET', 'POST'])
@login_required
def create():
    form = PatientForm()
    if form.validate_on_submit():
        patient = Patient(
            name=form.name.data,
            birth_date=form.birth_date.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
            medical_history=form.medical_history.data
        )
        db.session.add(patient)
        db.session.commit()
        flash('تم إضافة المريض بنجاح', 'success')
        return redirect(url_for('patients.view', id=patient.id))
    return render_template('patients/create.html', form=form, today=date.today())

@patients_bp.route('/patients/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    patient = Patient.query.get_or_404(id)
    form = PatientForm(obj=patient)
    if form.validate_on_submit():
        form.populate_obj(patient)
        db.session.commit()
        flash('تم تحديث بيانات المريض بنجاح', 'success')
        return redirect(url_for('patients.view', id=patient.id))
    return render_template('patients/edit.html', form=form, patient=patient, today=date.today())

@patients_bp.route('/patients/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    try:
        patient = Patient.query.get_or_404(id)
        if patient.examinations:
            flash('لا يمكن حذف المريض لوجود فحوصات مرتبطة به', 'danger')
            return redirect(url_for('patients.index'))
        
        db.session.delete(patient)
        db.session.commit()
        flash('تم حذف المريض بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting patient: {str(e)}")
        flash('حدث خطأ أثناء حذف المريض', 'danger')
    
    return redirect(url_for('patients.index'))

@patients_bp.route('/patients/<int:id>/medical-record')
@login_required
def medical_record(id):
    patient = Patient.query.get_or_404(id)
    return render_template('patients/medical_record.html', patient=patient, today=date.today())

# Debug route
@patients_bp.route('/patients/<int:id>/debug')
@login_required
def debug_patient(id):
    try:
        patient = Patient.query.get(id)
        if patient is None:
            return jsonify({'error': 'Patient not found'}), 404
        return jsonify({
            'id': patient.id,
            'name': patient.name,
            'email': patient.email,
            'phone': patient.phone,
            'examinations_count': len(patient.examinations) if patient.examinations else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
