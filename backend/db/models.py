from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ----------------- Association Table -----------------
doctor_patient = db.Table(
    'doctor_patient',
    db.Column('doctor_id', db.Integer, db.ForeignKey('doctor.id'), primary_key=True),
    db.Column('patient_id', db.Integer, db.ForeignKey('patient.id'), primary_key=True)
)

# ----------------- Admin -----------------
class Admin(db.Model):
    __tablename__ = 'admin'
    admin_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)


# ----------------- Doctor -----------------
class Doctor(db.Model):
    __tablename__ = 'doctor'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    wallet_address = db.Column(db.String(120), nullable=True)
    d_wallet = db.Column(db.Float, default=0.0)
    ratings = db.Column(db.Float, default=0.0)
    review_count = db.Column(db.Integer, default=0)
    certification_file = db.Column(db.String(300), nullable=True)

    patients = db.relationship('Patient', secondary=doctor_patient, back_populates='doctors')
    appointments = db.relationship('Appointment', back_populates='doctor', lazy=True)
    prescriptions = db.relationship('Prescription', back_populates='doctor', lazy=True)
    transactions_as_payee = db.relationship('Transaction', back_populates='payee_doctor', foreign_keys='Transaction.payee_doctor_id')


# ----------------- Doctor Applicant -----------------
class DoctorApplicant(db.Model):
    __tablename__ = 'doctor_applicant'
    appl_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    specialization = db.Column(db.String(100), nullable=True)
    certification_file = db.Column(db.String(300), nullable=True)
    wallet_address = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(20), default="pending")
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)


# ----------------- Patient -----------------
class Patient(db.Model):
    __tablename__ = 'patient'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    wallet_address = db.Column(db.String(120), nullable=True)
    wallet = db.Column(db.Float, default=0.0)

    doctors = db.relationship('Doctor', secondary=doctor_patient, back_populates='patients')
    appointments = db.relationship('Appointment', back_populates='patient', lazy=True)
    prescriptions = db.relationship('Prescription', back_populates='patient', lazy=True)
    transactions_as_payer = db.relationship('Transaction', back_populates='payer_patient', foreign_keys='Transaction.payer_patient_id')
    consents = db.relationship('Consent', back_populates='patient', lazy=True)


# ----------------- Appointment -----------------
class Appointment(db.Model):
    __tablename__ = 'appointment'
    ap_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_t = db.Column(db.String(20), nullable=False)
    time = db.Column(db.DateTime, nullable=False)
    doc_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    p_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')

    doctor = db.relationship('Doctor', back_populates='appointments')
    patient = db.relationship('Patient', back_populates='appointments')


# ----------------- Prescription -----------------
class Prescription(db.Model):
    __tablename__ = 'prescription'
    pres_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_time = db.Column(db.DateTime, default=datetime.utcnow)
    medication = db.Column(db.String(1000), nullable=False)
    doc_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    p_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)

    doctor = db.relationship('Doctor', back_populates='prescriptions')
    patient = db.relationship('Patient', back_populates='prescriptions')


# ----------------- Transaction -----------------
class Transaction(db.Model):
    __tablename__ = 'transaction'
    txn_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    payer_patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=True)
    payee_doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=True)

    payer_patient = db.relationship('Patient', back_populates='transactions_as_payer', foreign_keys=[payer_patient_id])
    payee_doctor = db.relationship('Doctor', back_populates='transactions_as_payee', foreign_keys=[payee_doctor_id])


# ----------------- Consent -----------------
class Consent(db.Model):
    __tablename__ = 'consent'
    consent_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_wallet = db.Column(db.String(120), nullable=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    active = db.Column(db.Boolean, default=True)

    patient = db.relationship('Patient', back_populates='consents')
