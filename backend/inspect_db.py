from app import app, db
from db.models import Appointment, Doctor, Patient, DoctorApplicant

with app.app_context():
    print("\n--- Doctors ---")
    for d in Doctor.query.all():
        print(d.doc_id, d.name, d.email, d.specialization)

    print("\n--- Patients ---")
    for p in Patient.query.all():
        print(p.p_id, p.name, p.email)

    print("\n--- Doctor Applicants ---")
    for da in DoctorApplicant.query.all():
        print(da.appl_id, da.name, da.status)

    print("\n--- Appointments ---")
    for a in Appointment.query.all():
        print(a.ap_id, a.date_t, a.status)

    print("\n✅ Data fetched successfully!")
