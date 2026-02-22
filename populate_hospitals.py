#!/usr/bin/env python
"""
Populate Hospital database with 50 sample hospitals (without location data)
Run: python manage.py shell < populate_hospitals.py
Or: python populate_hospitals.py
"""

import os
import django
from random import uniform, choice

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "parkinson.settings")
django.setup()

from app.models import Hospital

# Sample hospitals without location-sensitive data
hospitals_data = [
    {"name": "National Medical Center", "specialization": "Neurology, Parkinson Research", "rating": 4.8},
    {"name": "Advanced Neurological Institute", "specialization": "Neurology, Movement Disorders", "rating": 4.7},
    {"name": "Parkinson Excellence Hospital", "specialization": "Neurology, Movement Disorders, Parkinson Care", "rating": 4.9},
    {"name": "Central Medical Hospital", "specialization": "General Medicine, Neurology", "rating": 4.5},
    {"name": "Neurology Center of Excellence", "specialization": "Neurology, Clinical Research", "rating": 4.8},
    {"name": "Research Medical Institute", "specialization": "Medical Research, Neurology", "rating": 4.6},
    {"name": "Movement Disorder Clinic", "specialization": "Movement Disorders, Parkinson Research", "rating": 4.7},
    {"name": "Premier Neurological Hospital", "specialization": "Neurology, Neurosurgery, Movement Disorders", "rating": 4.8},
    {"name": "Specialized Parkinson Center", "specialization": "Parkinson Disease, Neurology", "rating": 4.9},
    {"name": "Clinical Neurology Institute", "specialization": "Neurology, Clinical Trials", "rating": 4.6},
    {"name": "Advanced Neuroscience Hospital", "specialization": "Neuroscience, Movement Disorders", "rating": 4.7},
    {"name": "Brain Health Medical Center", "specialization": "Neurology, Brain Health", "rating": 4.5},
    {"name": "Movement Disorders Specialists", "specialization": "Movement Disorders, Parkinson Care", "rating": 4.8},
    {"name": "Neurology Research Hospital", "specialization": "Neurology, Clinical Research", "rating": 4.6},
    {"name": "Parkinson Research Center", "specialization": "Parkinson Research, Neurology", "rating": 4.9},
    {"name": "Medical Excellence Hospital", "specialization": "General Medicine, Neurology", "rating": 4.5},
    {"name": "Neurological Excellence Clinic", "specialization": "Neurology, Movement Disorders", "rating": 4.7},
    {"name": "Advanced Treatment Center", "specialization": "Advanced Treatment, Neurology", "rating": 4.6},
    {"name": "Brain Research Institute", "specialization": "Brain Research, Neurology", "rating": 4.8},
    {"name": "Specialists in Movement Disorders", "specialization": "Movement Disorders, Physical Therapy", "rating": 4.5},
    {"name": "National Parkinson Center", "specialization": "Parkinson Disease, Neurology", "rating": 4.9},
    {"name": "Comprehensive Medical Center", "specialization": "General Medicine, Neurology", "rating": 4.6},
    {"name": "Neurological Care Hospital", "specialization": "Neurology, Patient Care", "rating": 4.7},
    {"name": "Clinical Neuroscience Center", "specialization": "Neuroscience, Clinical Services", "rating": 4.5},
    {"name": "Parkinson Excellence Institute", "specialization": "Parkinson Disease, Advanced Treatment", "rating": 4.8},
    {"name": "Movement Medicine Hospital", "specialization": "Movement Medicine, Neurology", "rating": 4.6},
    {"name": "Leading Neurology Center", "specialization": "Neurology, Specialist Services", "rating": 4.7},
    {"name": "Advanced Care Hospital", "specialization": "Advanced Care, Neurology", "rating": 4.5},
    {"name": "Research Excellence Institute", "specialization": "Clinical Research, Neurology", "rating": 4.9},
    {"name": "National Health Center", "specialization": "General Medicine, Neurology", "rating": 4.6},
    {"name": "Precision Medicine Center", "specialization": "Precision Medicine, Neurology", "rating": 4.8},
    {"name": "Neurology Specialist Hospital", "specialization": "Neurology, Specialist Doctors", "rating": 4.7},
    {"name": "Brain Care Center", "specialization": "Brain Care, Neurology", "rating": 4.5},
    {"name": "Parkinson Motor Disorders Clinic", "specialization": "Motor Disorders, Parkinson Disease", "rating": 4.6},
    {"name": "Central Neurology Hospital", "specialization": "Neurology, Central Services", "rating": 4.8},
    {"name": "Medical Innovation Hospital", "specialization": "Medical Innovation, Neurology", "rating": 4.9},
    {"name": "Neurological Treatment Center", "specialization": "Neurological Treatment, Advanced Care", "rating": 4.7},
    {"name": "Elite Health Hospital", "specialization": "Elite Health Services, Neurology", "rating": 4.5},
    {"name": "Advanced Neurology Clinic", "specialization": "Neurology, Advanced Treatment", "rating": 4.6},
    {"name": "Parkinson Care Specialist Center", "specialization": "Parkinson Care, Neurology", "rating": 4.8},
    {"name": "Comprehensive Neurology Hospital", "specialization": "Comprehensive Neurology, Movement Disorders", "rating": 4.7},
    {"name": "National Neuroscience Institute", "specialization": "Neuroscience, Research", "rating": 4.5},
    {"name": "Leading Health Hospital", "specialization": "Leading Health Services, Neurology", "rating": 4.9},
    {"name": "Advanced Medical Hospital", "specialization": "Advanced Medical Services, Neurology", "rating": 4.6},
    {"name": "Parkinson Excellence Clinic", "specialization": "Parkinson Disease, Excellence Care", "rating": 4.8},
    {"name": "Movement Specialist Hospital", "specialization": "Movement Specialists, Neurology", "rating": 4.7},
    {"name": "Clinical Excellence Center", "specialization": "Clinical Excellence, Neurology", "rating": 4.5},
    {"name": "Neurological Institute", "specialization": "Neurology, Institute Services", "rating": 4.6},
    {"name": "Health Excellence Hospital", "specialization": "Health Excellence, Neurology", "rating": 4.8},
]

def populate_hospitals():
    """Populate the database with hospital data."""
    if Hospital.objects.exists():
        print("✓ Hospitals already exist in database. Skipping...")
        return
    
    print("Populating hospitals...")
    
    hospitals_created = []
    for hospital_data in hospitals_data:
        hospital = Hospital.objects.create(
            name=hospital_data['name'],
            address="Medical Complex, Healthcare District",
            city="Metro Center",
            state="Central Region",
            lat=round(uniform(28.5, 28.8), 4),
            lon=round(uniform(77.0, 77.3), 4),
            phone=f"+91 {9000 + len(hospitals_created)}{choice(range(1000, 9999))}",
            email=f"contact@{hospital_data['name'].lower().replace(' ', '')}.com",
            specialization=hospital_data['specialization'],
            rating=hospital_data['rating']
        )
        hospitals_created.append(hospital.name)
    
    print(f"✓ Successfully created {len(hospitals_created)} hospitals!")
    print(f"Total hospitals in database: {Hospital.objects.count()}")

if __name__ == "__main__":
    populate_hospitals()
