from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import math

db = SQLAlchemy()

class Flight(db.Model):
    __tablename__ = 'flights'
    
    id = db.Column(db.String(50), primary_key=True)
    airline = db.Column(db.String(100), nullable=False)
    origin = db.Column(db.String(10), nullable=False)
    destination = db.Column(db.String(10), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    dep_time = db.Column(db.String(10), nullable=False)
    arr_time = db.Column(db.String(10), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='On Time')
    gate = db.Column(db.String(10), default='A1')
    terminal = db.Column(db.String(10), default='T1')
    
    # Seat configuration
    seat_rows = db.Column(db.Integer, default=12)
    seat_cols = db.Column(db.Integer, default=6)
    booked_seats = db.Column(db.Text)  # JSON string to store list of booked seats
    
    # Amenities as JSON string
    amenities = db.Column(db.Text)  # JSON string to store list of amenities
    
    # Relationship with bookings
    bookings = db.relationship('Booking', backref='flight_details', lazy=True)
    
    def __init__(self, **kwargs):
        super(Flight, self).__init__(**kwargs)
        if self.booked_seats is None:
            self.booked_seats = json.dumps([])
        if self.amenities is None:
            self.amenities = json.dumps([])
    
    def get_booked_seats(self):
        """Return booked seats as a Python list"""
        if self.booked_seats:
            return json.loads(self.booked_seats)
        return []
    
    def set_booked_seats(self, seats_list):
        """Set booked seats from a Python list"""
        self.booked_seats = json.dumps(seats_list)
    
    def get_amenities(self):
        """Return amenities as a Python list"""
        if self.amenities:
            return json.loads(self.amenities)
        return []
    
    def set_amenities(self, amenities_list):
        """Set amenities from a Python list"""
        self.amenities = json.dumps(amenities_list)
    
    def add_booked_seat(self, seat):
        """Add a single seat to booked seats"""
        booked = self.get_booked_seats()
        if seat not in booked:
            booked.append(seat)
            self.set_booked_seats(booked)
    
    def remove_booked_seat(self, seat):
        """Remove a single seat from booked seats"""
        booked = self.get_booked_seats()
        if seat in booked:
            booked.remove(seat)
            self.set_booked_seats(booked)
    
    def get_occupancy_rate(self):
        """Calculate flight occupancy rate (0.0 to 1.0)"""
        total_seats = self.seat_rows * self.seat_cols
        booked_count = len(self.get_booked_seats())
        return booked_count / total_seats if total_seats > 0 else 0.0
    

    def get_days_until_departure(self):
        """Calculate days until departure from current date"""
        try:
            flight_date = datetime.strptime(self.date, '%Y-%m-%d')
            current_date = datetime.now()
            days_diff = (flight_date - current_date).days
            return max(0, days_diff)  # Return 0 if flight is today or past
        except:
            return 30  # Default to 30 days if date parsing fails
    
    def calculate_dynamic_price(self):
        """Calculate dynamic price based on demand, availability, time, and market factors"""
        base_price = self.price
        
        # Factor 1: Occupancy-based pricing (demand)
        # Higher occupancy = higher price (up to 60% increase for high demand)
        occupancy_rate = self.get_occupancy_rate()
        if occupancy_rate >= 0.8:  # 80%+ occupied - very high demand
            occupancy_multiplier = 1.6  
        elif occupancy_rate >= 0.6:  # 60-80% occupied - high demand
            occupancy_multiplier = 1.4
        elif occupancy_rate >= 0.4:  # 40-60% occupied - moderate demand
            occupancy_multiplier = 1.2
        elif occupancy_rate >= 0.2:  # 20-40% occupied - low demand
            occupancy_multiplier = 1.1
        else:  # <20% occupied - very low demand (discounts)
            occupancy_multiplier = 0.95
        
        # Factor 2: Time-based pricing (urgency)
        # Prices increase as departure approaches
        days_until_departure = self.get_days_until_departure()
        
        if days_until_departure >= 45:
            time_multiplier = 0.75  # Super early bird discount
        elif days_until_departure >= 30:
            time_multiplier = 0.8   # Early bird discount
        elif days_until_departure >= 21:
            time_multiplier = 0.9   # Advance booking discount
        elif days_until_departure >= 14:
            time_multiplier = 1.0   # Base price
        elif days_until_departure >= 7:
            time_multiplier = 1.25  # 25% increase
        elif days_until_departure >= 3:
            time_multiplier = 1.5   # 50% increase
        elif days_until_departure >= 1:
            time_multiplier = 1.75  # 75% increase
        else:
            time_multiplier = 2.0   # 100% increase (same day/last minute)
        
        # Factor 3: Peak hour pricing
        # Morning rush (6-9 AM) and evening rush (6-9 PM) flights
        try:
            dep_hour = int(self.dep_time.split(':')[0])
            if (6 <= dep_hour <= 9) or (18 <= dep_hour <= 21):
                peak_multiplier = 1.15  # 15% increase for peak hours
            elif (22 <= dep_hour <= 5):  # Red-eye flights
                peak_multiplier = 0.9   # 10% discount for inconvenient hours
            else:
                peak_multiplier = 1.0
        except:
            peak_multiplier = 1.0
        
        # Factor 4: Day of week pricing (weekends vs weekdays)
        try:
            flight_date = datetime.strptime(self.date, '%Y-%m-%d')
            day_of_week = flight_date.weekday()  # 0=Monday, 6=Sunday
            if day_of_week >= 5:  # Weekend (Saturday/Sunday)
                weekend_multiplier = 1.1
            elif day_of_week == 4:  # Friday
                weekend_multiplier = 1.05
            else:  # Monday-Thursday
                weekend_multiplier = 1.0
        except:
            weekend_multiplier = 1.0
            
        # Factor 5: Route popularity (premium routes cost more)
        premium_routes = ['DEL-BOM', 'BOM-DEL', 'BLR-DEL', 'DEL-BLR']
        route_key = f"{self.origin}-{self.destination}"
        if route_key in premium_routes:
            route_multiplier = 1.1
        else:
            route_multiplier = 1.0
        
        # Calculate final dynamic price
        dynamic_price = (base_price * occupancy_multiplier * time_multiplier * 
                        peak_multiplier * weekend_multiplier * route_multiplier)
        
        # Add some randomness for market fluctuation (±3%)
        import random
        market_fluctuation = random.uniform(0.97, 1.03)
        dynamic_price *= market_fluctuation
        
        # Round to nearest 50 for cleaner pricing
        dynamic_price = math.ceil(dynamic_price / 50) * 50
        
        # Ensure minimum price (never go below 70% of base price)
        min_price = int(base_price * 0.7)
        dynamic_price = max(min_price, int(dynamic_price))
        
        return dynamic_price
    
    def get_price_trend(self):
        """Get price trend indication for display"""
        base_price = self.price
        dynamic_price = self.calculate_dynamic_price()
        
        change_percent = ((dynamic_price - base_price) / base_price) * 100
        
        if change_percent > 30:
            return "high"        # High demand - 30%+ price increase
        elif change_percent > 10:
            return "moderate"    # Rising prices - 10-30% increase
        elif change_percent > -5:
            return "stable"      # Stable prices - ±5% change
        else:
            return "low"         # Great deals - more than 5% discount
    
    def get_pricing_factors(self):
        """Get detailed breakdown of pricing factors for analysis"""
        occupancy_rate = self.get_occupancy_rate()
        days_until_departure = self.get_days_until_departure()
        
        # Calculate individual multipliers
        if occupancy_rate >= 0.8:
            occupancy_multiplier = 1.6
        elif occupancy_rate >= 0.6:
            occupancy_multiplier = 1.4
        elif occupancy_rate >= 0.4:
            occupancy_multiplier = 1.2
        elif occupancy_rate >= 0.2:
            occupancy_multiplier = 1.1
        else:
            occupancy_multiplier = 0.95
            
        if days_until_departure >= 45:
            time_multiplier = 0.75
        elif days_until_departure >= 30:
            time_multiplier = 0.8
        elif days_until_departure >= 21:
            time_multiplier = 0.9
        elif days_until_departure >= 14:
            time_multiplier = 1.0
        elif days_until_departure >= 7:
            time_multiplier = 1.25
        elif days_until_departure >= 3:
            time_multiplier = 1.5
        elif days_until_departure >= 1:
            time_multiplier = 1.75
        else:
            time_multiplier = 2.0
            
        try:
            dep_hour = int(self.dep_time.split(':')[0])
            if (6 <= dep_hour <= 9) or (18 <= dep_hour <= 21):
                peak_multiplier = 1.15
            elif (22 <= dep_hour <= 5):
                peak_multiplier = 0.9
            else:
                peak_multiplier = 1.0
        except:
            peak_multiplier = 1.0
            
        return {
            "occupancy_factor": round(occupancy_multiplier, 2),
            "time_factor": round(time_multiplier, 2),
            "peak_hour_factor": round(peak_multiplier, 2),
            "occupancy_rate": round(occupancy_rate * 100, 1),
            "days_until_departure": days_until_departure,
            "peak_hours": (6 <= int(self.dep_time.split(':')[0]) <= 9) or (18 <= int(self.dep_time.split(':')[0]) <= 21) if ':' in self.dep_time else False
        }
    
    def to_dict(self):
        """Convert flight to dictionary (similar to JSON structure)"""
        dynamic_price = self.calculate_dynamic_price()
        pricing_factors = self.get_pricing_factors()
        
        return {
            'id': self.id,
            'airline': self.airline,
            'origin': self.origin,
            'destination': self.destination,
            'date': self.date,
            'dep_time': self.dep_time,
            'arr_time': self.arr_time,
            'price': self.price,
            'dynamic_price': dynamic_price,
            'price_trend': self.get_price_trend(),
            'price_change_percent': round(((dynamic_price - self.price) / self.price) * 100, 1),
            'occupancy_rate': round(self.get_occupancy_rate(), 2),
            'days_until_departure': self.get_days_until_departure(),
            'pricing_factors': pricing_factors,
            'status': self.status,
            'gate': self.gate,
            'terminal': self.terminal,
            'seats': {
                'rows': self.seat_rows,
                'cols': self.seat_cols,
                'booked': self.get_booked_seats()
            },
            'amenities': self.get_amenities()
        }


class Booking(db.Model):
    __tablename__ = 'bookings'
    
    pnr = db.Column(db.String(50), primary_key=True)
    flight_id = db.Column(db.String(50), db.ForeignKey('flights.id'), nullable=False)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    seats = db.Column(db.Text, nullable=False)  # JSON string to store list of seats
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='PENDING')
    created_at = db.Column(db.String(50), nullable=False)
    
    def __init__(self, **kwargs):
        super(Booking, self).__init__(**kwargs)
        if isinstance(self.seats, list):
            self.seats = json.dumps(self.seats)
    
    def get_seats(self):
        """Return seats as a Python list"""
        if self.seats:
            return json.loads(self.seats)
        return []
    
    def set_seats(self, seats_list):
        """Set seats from a Python list"""
        self.seats = json.dumps(seats_list)
    
    def to_dict(self):
        """Convert booking to dictionary (similar to JSON structure)"""
        return {
            'pnr': self.pnr,
            'flight_id': self.flight_id,
            'fullname': self.fullname,
            'email': self.email,
            'phone': self.phone,
            'seats': self.get_seats(),
            'amount': self.amount,
            'status': self.status,
            'created_at': self.created_at
        }


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='admin')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }