from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean
from ..database.db import Base
from datetime import datetime
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    clerk_id = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    avatar_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    symptom_reports = relationship("SymptomReport", back_populates="user")
    bookings = relationship("Booking", back_populates="user")


class SymptomReport(Base):
    __tablename__ = "symptom_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    symptoms_raw = Column(Text)
    triage_result = Column(Text)
    severity = Column(String)
    recommended_specialty = Column(String)
    user_latitude = Column(Float)
    user_longitude = Column(Float)
    user_language = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="symptom_reports")
    bookings = relationship("Booking", back_populates="symptom_report")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    symptom_report_id = Column(Integer, ForeignKey("symptom_reports.id"), nullable=True)

    hospital_place_id = Column(String)
    hospital_name = Column(String)
    hospital_address = Column(String)
    hospital_phone = Column(String)

    patient_name = Column(String)
    patient_age = Column(Integer)
    patient_gender = Column(String)
    patient_blood_type = Column(String)
    patient_allergies = Column(Text)
    emergency_contact_name = Column(String)
    emergency_contact_phone = Column(String)
    emergency_contact_email = Column(String)

    appointment_time = Column(DateTime)
    status = Column(String, default="pending")
    ambulance_requested = Column(Boolean, default=False)
    notes = Column(Text)
    estimated_cost_usd = Column(Integer)

    family_report_sent = Column(Boolean, default=False)
    family_report_text = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="bookings")
    symptom_report = relationship("SymptomReport", back_populates="bookings")
