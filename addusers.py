# Add users to Firestore (run this code separately to add users)
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

users = [
    {'email': 'pastorpaul@gmail.com', 'password': 'password123', 'phone': '+19999999999'},
    {'email': 'venkyboma@gmail.com', 'password': 'password223', 'phone': '+18888888888'},
    {'email': 'prabha@gmail.com', 'password': 'password123', 'phone': '+17777777777'}
]

for user in users:
    db.collection('users').add(user)

print("Users added successfully!")
