from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, TextAreaField, 
    SelectField, DateField, FileField, DecimalField, SubmitField
)
from wtforms.validators import DataRequired, Email, Length, Optional
from datetime import date
from models import Patient, Examination, User

class LoginForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    remember_me = BooleanField('تذكرني')
    submit = SubmitField('تسجيل الدخول')

class UserForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    name = StringField('الاسم', validators=[DataRequired()])
    role = SelectField('الدور', choices=[('admin', 'مدير'), ('doctor', 'طبيب')])
    submit = SubmitField('حفظ')

class PatientForm(FlaskForm):
    name = StringField('الاسم', validators=[DataRequired(), Length(min=2, max=100)])
    birth_date = DateField('تاريخ الميلاد', validators=[Optional()])
    phone = StringField('رقم الهاتف', validators=[Optional(), Length(max=20)])
    email = StringField('البريد الإلكتروني', validators=[Optional(), Email()])
    address = TextAreaField('العنوان', validators=[Optional(), Length(max=200)])
    medical_history = TextAreaField('التاريخ الطبي', validators=[Optional()])
    submit = SubmitField('حفظ')

class ExaminationForm(FlaskForm):
    EXAMINATION_TYPES = [
        ('xray', 'أشعة سينية'),
        ('ct', 'أشعة مقطعية'),
        ('mri', 'رنين مغناطيسي'),
        ('ultrasound', 'موجات صوتية'),
        ('mammogram', 'تصوير الثدي'),
        ('dexa', 'قياس كثافة العظام')
    ]
    
    patient_id = SelectField('المريض', coerce=int, validators=[DataRequired()])
    examination_type = SelectField('نوع الفحص', choices=EXAMINATION_TYPES, validators=[DataRequired()])
    result = TextAreaField('النتيجة', validators=[Optional()])
    recommendations = TextAreaField('التوصيات', validators=[Optional()])
    report_file = FileField('تقرير الفحص')
    submit = SubmitField('حفظ')

    def __init__(self, *args, **kwargs):
        super(ExaminationForm, self).__init__(*args, **kwargs)
        self.patient_id.choices = [(p.id, p.name) for p in Patient.query.order_by(Patient.name).all()]

class InvoiceForm(FlaskForm):
    PAYMENT_METHODS = [
        ('cash', 'نقداً'),
        ('card', 'بطاقة ائتمان'),
        ('transfer', 'تحويل بنكي')
    ]
    
    patient_id = SelectField('المريض', coerce=int, validators=[DataRequired()])
    examination_id = SelectField('الفحص', coerce=int, validators=[DataRequired()])
    total_amount = DecimalField('المبلغ الإجمالي', validators=[DataRequired()])
    discount = DecimalField('الخصم', validators=[Optional()], default=0.0)
    paid_amount = DecimalField('المبلغ المدفوع', validators=[Optional()], default=0.0)
    payment_method = SelectField('طريقة الدفع', choices=PAYMENT_METHODS, validators=[DataRequired()])
    notes = TextAreaField('ملاحظات', validators=[Optional()])
    submit = SubmitField('حفظ')

    def __init__(self, *args, **kwargs):
        super(InvoiceForm, self).__init__(*args, **kwargs)
        self.patient_id.choices = [(p.id, p.name) for p in Patient.query.order_by(Patient.name).all()]
        if 'patient_id' in kwargs:
            self.examination_id.choices = [(e.id, f"{e.get_examination_type_display()} - {e.created_at.strftime('%Y-%m-%d')}") 
                                         for e in Examination.query.filter_by(patient_id=kwargs['patient_id']).all()]
        else:
            self.examination_id.choices = []

class PaymentForm(FlaskForm):
    PAYMENT_METHODS = [
        ('cash', 'نقداً'),
        ('card', 'بطاقة ائتمان'),
        ('transfer', 'تحويل بنكي')
    ]
    
    amount = DecimalField('المبلغ', validators=[DataRequired()])
    payment_method = SelectField('طريقة الدفع', choices=PAYMENT_METHODS, validators=[DataRequired()])
    notes = TextAreaField('ملاحظات', validators=[Optional()])
    submit = SubmitField('حفظ')
