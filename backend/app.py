# backend/app.py
import os
import json
import tempfile
from datetime import datetime, timedelta
from functools import wraps


from flask import Flask, jsonify, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, verify_jwt_in_request, get_jwt_identity, get_jwt
from flask_mail import Mail
from dotenv import load_dotenv
from web3 import Web3
import ipfshttpclient

from db.models import db, Patient, DoctorApplicant,doctor_patient,Appointment

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})


# ---------------- Configuration ----------------
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-jwt-key')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'super-secret')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

# ---------------- Extensions ----------------

bcrypt = Bcrypt(app)
jwt = JWTManager(app)
mail = Mail(app)
migrate = Migrate(app, db)
db.init_app(app) 
with app.app_context():
    db.create_all()
    print("Tables created successfully!")


# ---------------- Web3 ----------------
RPC_URL = os.getenv('BLOCKCHAIN_RPC', 'http://127.0.0.1:7545')
w3 = Web3(Web3.HTTPProvider(RPC_URL))
SERVER_ADDRESS = Web3.to_checksum_address(os.getenv('SERVER_ADDRESS', '0x0000000000000000000000000000000000000000'))
PRIVATE_KEY = os.getenv('PRIVATE_KEY')

MEDRECORD_JSON_PATH = os.getenv('CONTRACT_MEDRECORD_JSON', 'blockchain/build/contracts/MedRecord.json')
DOCTOR_JSON_PATH = os.getenv('CONTRACT_DOCTOR_JSON', 'blockchain/build/contracts/DoctorVerification.json')

def load_contract(json_path):
    with open(json_path) as f:
        artifact = json.load(f)
    abi = artifact.get('abi')
    networks = artifact.get('networks', {})
    if networks:
        first_net = next(iter(networks.values()))
        address = first_net.get('address')
        if address:
            return w3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)
    env_addr = os.getenv(os.path.basename(json_path).split('.')[0].upper() + '_ADDRESS')
    if env_addr:
        return w3.eth.contract(address=Web3.to_checksum_address(env_addr), abi=abi)
    return None

try:
    medrecord_contract = load_contract(MEDRECORD_JSON_PATH)
    doctor_contract = load_contract(DOCTOR_JSON_PATH)
except Exception as e:
    medrecord_contract = None
    doctor_contract = None
    print("Warning: could not load contract(s):", e)





# ---------------- Models ----------------










with app.app_context():
    db.create_all()

# ---------------- Decorators ----------------
def role_required(required_role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") != required_role:
                return jsonify({"error": f"{required_role.capitalize()}s only"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

admin_required = role_required("admin")
doctor_required = role_required("doctor")
patient_required = role_required("patient")

# ---------------- Helpers ----------------
def send_txn(contract_function, tx_params_override=None):
    if PRIVATE_KEY is None:
        raise RuntimeError("Server PRIVATE_KEY not set in environment.")
    tx = contract_function.build_transaction({
        'from': SERVER_ADDRESS,
        'nonce': w3.eth.get_transaction_count(SERVER_ADDRESS),
        'gas': 500000,
        'gasPrice': w3.to_wei('20', 'gwei'),
        **(tx_params_override or {})
    })
    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt

def upload_to_ipfs(filepath):
    client = ipfshttpclient.connect()
    res = client.add(filepath)
    return res['Hash']

# ---------------- Routes ----------------
@app.route('/')
def home():
    return jsonify({"message": "MedHelp API running!"})

# ---------------- Auth Routes ----------------
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route("/register", methods=["POST"])
def register():
    try:
        role = request.form.get("role")
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        # Basic validation
        if not all([role, name, email, password]):
            return jsonify({"error": "Please provide all required fields"}), 400

        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        # ------------------ PATIENT REGISTRATION ------------------
        if role == "patient":
            # Check if patient already exists
            if Patient.query.filter_by(email=email).first():
                return jsonify({"error": "Email already registered"}), 400

            age = request.form.get("age")
            phone = request.form.get("phone")
            address = request.form.get("address")

            new_patient = Patient(
                name=name,
                email=email,
                password=hashed_password,
                age=int(age) if age else None,
                phone=phone,
                address=address,
                wallet_address=None,
                wallet=0.0
            )

            db.session.add(new_patient)
            db.session.commit()

            return jsonify({"success": True, "message": "Patient registered successfully!"}), 201

        # ------------------ DOCTOR REGISTRATION ------------------
        elif role == "doctor":
            # Check if doctor applicant already exists
            if DoctorApplicant.query.filter_by(email=email).first():
                return jsonify({"error": "Email already registered"}), 400

            specialization = request.form.get("specialization", "General")
            wallet_address = request.form.get("wallet_address")

            # Handle certification file upload
            cert_file = None
            file = request.files.get("certification")
            if file:
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                cert_file = secure_filename(file.filename)
                file.save(os.path.join(UPLOAD_FOLDER, cert_file))

            new_doc_applicant = DoctorApplicant(
                name=name,
                email=email,
                password=hashed_password,
                specialization=specialization,
                certification_file=cert_file,
                wallet_address=wallet_address,
                status="pending",
                submitted_at=datetime.utcnow()
            )

            db.session.add(new_doc_applicant)
            db.session.commit()

            return jsonify({"success": True, "message": "Doctor registration submitted for approval!"}), 201

        else:
            return jsonify({"error": "Invalid role"}), 400

    except Exception as e:
        print("Registration Error:", e)
        db.session.rollback()  # rollback on error
        return jsonify({"error": str(e)}), 500


@app.route("/test", methods=["GET"])
def test():
    return jsonify({"message": "Backend connected successfully!"})


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    if role == 'patient':
        user = Patient.query.filter_by(email=email).first()
    elif role == 'doctor':
        user = Doctor.query.filter_by(email=email).first()
    else:
        return jsonify({'error': 'Invalid role'}), 400

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.password != password:
        return jsonify({'error': 'Invalid credentials'}), 401

    return jsonify({'message': 'Login successful', 'role': role}), 200

# ---------------- Admin Routes ----------------
@app.route('/admin/dashboard', methods=['GET'])
@admin_required
def admin_dashboard():
    pending_count = DoctorApplicant.query.filter_by(status='pending').count()
    approved_count = Doctor.query.count()
    return jsonify({"pending_doctors": pending_count, "approved_doctors": approved_count}), 200

@app.route('/admin/approve_doctor/<int:appl_id>', methods=['POST'])
@admin_required
def approve_doctor(appl_id):
    applicant = DoctorApplicant.query.get_or_404(appl_id)
    if applicant.status != 'pending':
        return jsonify({"error": "Application already processed"}), 400
    applicant.status = 'approved'
    new_doctor = Doctor(
        name=applicant.name,
        email=applicant.email,
        password=applicant.password,
        specialization=applicant.specialization,
        wallet_address=applicant.wallet_address
    )
    db.session.add(new_doctor)
    db.session.commit()
    return jsonify({"success": True, "message": f"Doctor {new_doctor.name} approved"}), 200

# ---------------- Patient Routes ----------------
@app.route('/patient/upload_record', methods=['POST'])
@patient_required
def upload_record():
    patient_id = get_jwt_identity()['id']
    file = request.files.get('file')
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        file.save(tmp.name)
        ipfs_hash = upload_to_ipfs(tmp.name)
    return jsonify({"success": True, "ipfs_hash": ipfs_hash}), 200

@app.route('/patient/grant_access', methods=['POST'])
@patient_required
def grant_access():
    patient_id = get_jwt_identity()['id']
    data = request.get_json()
    doctor_wallet = data.get('doctor_wallet')
    if not doctor_wallet:
        return jsonify({"error": "doctor_wallet required"}), 400
    new_consent = Consent(patient_id=patient_id, doctor_wallet=doctor_wallet)
    db.session.add(new_consent)
    db.session.commit()
    return jsonify({"success": True, "message": "Access granted"}), 200

@app.route('/patient/revoke_access', methods=['POST'])
@patient_required
def revoke_access():
    patient_id = get_jwt_identity()['id']
    data = request.get_json()
    doctor_wallet = data.get('doctor_wallet')
    consent = Consent.query.filter_by(patient_id=patient_id, doctor_wallet=doctor_wallet, active=True).first()
    if not consent:
        return jsonify({"error": "No active consent found"}), 404
    consent.active = False
    db.session.commit()
    return jsonify({"success": True, "message": "Access revoked"}), 200

@app.route('/patient/pay_doctor', methods=['POST'])
@patient_required
def pay_doctor():
    patient_id = get_jwt_identity()['id']
    data = request.get_json()
    doctor_id = data.get('doctor_id')
    amount = data.get('amount')
    if not all([doctor_id, amount]):
        return jsonify({"error": "doctor_id and amount required"}), 400
    doctor = Doctor.query.get_or_404(doctor_id)
    patient = Patient.query.get(patient_id)
    if patient.wallet < amount:
        return jsonify({"error": "Insufficient funds"}), 400
    patient.wallet -= amount
    doctor.d_wallet += amount
    txn = Transaction(amount=amount, payer_patient=patient, payee_doctor=doctor)
    db.session.add(txn)
    db.session.commit()
    return jsonify({"success": True, "message": f"Paid {amount} to Dr. {doctor.name}"}), 200

# ---------------- Doctor Routes ----------------
@app.route('/doctor/get_patient_records/<int:patient_id>', methods=['GET'])
@doctor_required
def get_patient_records(patient_id):
    doctor_id = get_jwt_identity()['id']
    doctor = Doctor.query.get(doctor_id)
    patient = Patient.query.get_or_404(patient_id)
    consent = Consent.query.filter_by(patient_id=patient_id, doctor_wallet=doctor.wallet_address, active=True).first()
    if not consent:
        return jsonify({"error": "Access denied"}), 403
    return jsonify({"success": True, "records": f"Records for patient {patient.name}"}), 200

# ---------------- Run ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)

