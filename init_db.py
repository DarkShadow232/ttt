from app import app, db
from models import User, Patient, Examination, Invoice, Payment
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        # إنشاء مستخدم المشرف
        admin = User(
            username='admin',
            email='admin@example.com',
            name='مدير النظام',
            role='admin'
        )
        admin.set_password('admin123')
        
        # إنشاء طبيب
        doctor = User(
            username='doctor',
            email='doctor@example.com',
            name='د. أحمد محمد',
            role='doctor'
        )
        doctor.set_password('doctor123')
        
        db.session.add(admin)
        db.session.add(doctor)
        db.session.commit()
        
        # إضافة مرضى وهميين
        patients = [
            Patient(
                name='محمد أحمد',
                birth_date=datetime(1980, 5, 15),
                phone='0501234567',
                email='mohammed@example.com',
                address='الرياض - حي النزهة',
                medical_history='يعاني من ارتفاع ضغط الدم'
            ),
            Patient(
                name='فاطمة علي',
                birth_date=datetime(1992, 8, 20),
                phone='0557891234',
                email='fatima@example.com',
                address='الرياض - حي الملز',
                medical_history='لا يوجد أمراض مزمنة'
            ),
            Patient(
                name='عبدالله محمد',
                birth_date=datetime(1975, 3, 10),
                phone='0534567890',
                email='abdullah@example.com',
                address='الرياض - حي السليمانية',
                medical_history='مريض سكري'
            ),
            Patient(
                name='نورة سعد',
                birth_date=datetime(1988, 11, 25),
                phone='0567891234',
                email='noura@example.com',
                address='الرياض - حي الورود',
                medical_history='حساسية من البنسلين'
            ),
            Patient(
                name='خالد عبدالرحمن',
                birth_date=datetime(1995, 7, 5),
                phone='0512345678',
                email='khalid@example.com',
                address='الرياض - حي الياسمين',
                medical_history='لا يوجد'
            )
        ]
        
        for patient in patients:
            db.session.add(patient)
        db.session.commit()
        
        # إضافة فحوصات وهمية
        examinations = [
            Examination(
                examination_type='xray',
                patient_id=1,
                performed_by=2,
                status='completed',
                result='فحص الصدر - طبيعي',
                created_at=datetime.now() - timedelta(days=5)
            ),
            Examination(
                examination_type='mri',
                patient_id=2,
                performed_by=2,
                status='completed',
                result='فحص الركبة - تمزق في الرباط',
                created_at=datetime.now() - timedelta(days=3)
            ),
            Examination(
                examination_type='ct',
                patient_id=3,
                performed_by=2,
                status='completed',
                result='فحص البطن - طبيعي',
                created_at=datetime.now() - timedelta(days=2)
            ),
            Examination(
                examination_type='ultrasound',
                patient_id=4,
                performed_by=2,
                status='pending',
                result='فحص الغدة الدرقية',
                created_at=datetime.now() - timedelta(days=1)
            ),
            Examination(
                examination_type='xray',
                patient_id=5,
                performed_by=2,
                status='in_progress',
                result='فحص اليد اليمنى',
                created_at=datetime.now()
            )
        ]
        
        # قائمة بتكاليف الفحوصات
        examination_costs = {
            'xray': 250.00,
            'mri': 800.00,
            'ct': 500.00,
            'ultrasound': 300.00
        }
        
        for exam in examinations:
            db.session.add(exam)
        db.session.commit()
        
        # إضافة فواتير للفحوصات المكتملة
        completed_exams = Examination.query.filter_by(status='completed').all()
        for exam in completed_exams:
            cost = examination_costs[exam.examination_type]
            invoice = Invoice(
                patient_id=exam.patient_id,
                examination_id=exam.id,
                amount=cost,
                created_at=exam.created_at + timedelta(hours=1),
                created_by=1,
                notes='تم إنشاء الفاتورة تلقائياً'
            )
            db.session.add(invoice)
            db.session.commit()
            
            # إضافة دفعة كاملة للفاتورة
            payment = Payment(
                invoice_id=invoice.id,
                amount=cost,
                payment_method='cash',
                payment_date=exam.created_at + timedelta(hours=1),
                created_by=1,
                notes='تم الدفع نقداً'
            )
            db.session.add(payment)
            db.session.commit()
        
        print('تم إنشاء قاعدة البيانات وإضافة البيانات الوهمية بنجاح')

if __name__ == '__main__':
    init_db()
