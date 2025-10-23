#!/usr/bin/env python3
"""
Migration script to convert JSON data to SQLite database
Run this script once to migrate from flights.json and bookings.json to database.db
"""

import json
import os
from datetime import datetime
from flask import Flask
from models import db, Flight, Booking, User

# Create a minimal Flask app for database operations
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

def load_json(filename, default):
    """Load JSON data from file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load {filename}: {e}")
        return default

def migrate_flights():
    """Migrate flights from JSON to database"""
    print("Migrating flights...")
    
    flights_data = load_json('flights.json', {"flights": []})
    flights = flights_data.get('flights', [])
    
    migrated_count = 0
    for flight_data in flights:
        # Check if flight already exists
        existing_flight = Flight.query.get(flight_data['id'])
        if existing_flight:
            print(f"Flight {flight_data['id']} already exists, skipping...")
            continue
        
        # Create new flight
        flight = Flight(
            id=flight_data['id'],
            airline=flight_data.get('airline', ''),
            origin=flight_data.get('origin', ''),
            destination=flight_data.get('destination', ''),
            date=flight_data.get('date', ''),
            dep_time=flight_data.get('dep_time', ''),
            arr_time=flight_data.get('arr_time', ''),
            price=flight_data.get('price', 0),
            status=flight_data.get('status', 'On Time'),
            gate=flight_data.get('gate', 'A1'),
            terminal=flight_data.get('terminal', 'T1'),
            seat_rows=flight_data.get('seats', {}).get('rows', 12),
            seat_cols=flight_data.get('seats', {}).get('cols', 6),
        )
        
        # Set booked seats and amenities
        booked_seats = flight_data.get('seats', {}).get('booked', [])
        flight.set_booked_seats(booked_seats)
        
        amenities = flight_data.get('amenities', [])
        flight.set_amenities(amenities)
        
        db.session.add(flight)
        migrated_count += 1
        print(f"Added flight: {flight.id} - {flight.airline}")
    
    db.session.commit()
    print(f"Flights migration complete: {migrated_count} flights migrated.")
    return migrated_count

def migrate_bookings():
    """Migrate bookings from JSON to database"""
    print("Migrating bookings...")
    
    bookings_data = load_json('bookings.json', {"bookings": []})
    bookings = bookings_data.get('bookings', [])
    
    migrated_count = 0
    for booking_data in bookings:
        # Check if booking already exists
        existing_booking = Booking.query.get(booking_data['pnr'])
        if existing_booking:
            print(f"Booking {booking_data['pnr']} already exists, skipping...")
            continue
        
        # Create new booking
        booking = Booking(
            pnr=booking_data['pnr'],
            flight_id=booking_data.get('flight_id', ''),
            fullname=booking_data.get('fullname', ''),
            email=booking_data.get('email', ''),
            phone=booking_data.get('phone', ''),
            amount=booking_data.get('amount', 0),
            status=booking_data.get('status', 'PENDING'),
            created_at=booking_data.get('created_at', '')
        )
        
        # Set seats
        seats = booking_data.get('seats', [])
        booking.set_seats(seats)
        
        db.session.add(booking)
        migrated_count += 1
        print(f"Added booking: {booking.pnr} - {booking.fullname}")
    
    db.session.commit()
    print(f"Bookings migration complete: {migrated_count} bookings migrated.")
    return migrated_count

def create_admin_user():
    """Create default admin user"""
    print("Creating admin user...")
    
    # Check if admin user already exists
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print("Admin user already exists, skipping...")
        return
    
    # Create admin user
    admin_user = User(
        username='admin',
        password='admin123',  # In production, this should be hashed
        role='admin'
    )
    
    db.session.add(admin_user)
    db.session.commit()
    print("Admin user created: username=admin, password=admin123")

def main():
    """Main migration function"""
    print("Starting JSON to Database migration...")
    print("=" * 50)
    
    with app.app_context():
        # Create all database tables
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully.")
        
        # Migrate data
        flights_migrated = migrate_flights()
        bookings_migrated = migrate_bookings()
        create_admin_user()
        
        print("=" * 50)
        print("Data migration complete!")
        print(f"Summary:")
        print(f"  - Flights migrated: {flights_migrated}")
        print(f"  - Bookings migrated: {bookings_migrated}")
        print(f"  - Database file created: database.db")
        print(f"  - Admin user created: admin/admin123")

if __name__ == '__main__':
    main()