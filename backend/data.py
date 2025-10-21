from app import db, User

# Get all users
users = User.query.all()
for u in users:
    print(u.name, u.email, u.role)
