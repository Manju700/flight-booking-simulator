from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
import json, os, random, string, datetime
from io import BytesIO
from flask import send_file
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PIL import Image
from reportlab.lib.utils import ImageReader
import datetime
from models import db, Flight, Booking, User



app = Flask(__name__)
app.secret_key = "super-secret-key"

# SQLAlchemy configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
FLIGHTS_FILE = os.path.join(DATA_DIR, "flights.json")
BOOKINGS_FILE = os.path.join(DATA_DIR, "bookings.json")
ADMIN_PASS = os.environ.get("FRS_ADMIN_PASS", "admin123")

# ------------------ Database Utilities ------------------
def find_flight(fid):
    """Find a flight by ID"""
    return db.session.get(Flight, fid)

def find_booking(pnr):
    """Find a booking by PNR"""
    return db.session.get(Booking, pnr)

def generate_pnr(prefix="IN"):
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}-{code}"

@app.template_filter("date_in")
def date_in(value, format="%d-%m-%Y"):
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d").strftime(format)
    except:
        return value

# ------------------ Routes ------------------
@app.route("/")
def home():
    flights = Flight.query.all()
    flights_data = [f.to_dict() for f in flights]
    origins = sorted(set([f.origin for f in flights]))
    destinations = sorted(set([f.destination for f in flights]))
    return render_template("home.html", flights=flights_data,
                           origins=origins, destinations=destinations)


@app.context_processor
def inject_now():
    return {'now': datetime.datetime.utcnow()}

@app.route("/search")
def search():
    origin = request.args.get("origin", "").upper()
    destination = request.args.get("destination", "").upper()
    date = request.args.get("date", "")
    max_price = request.args.get("max_price", "")

    # Build query filters
    query = Flight.query
    
    if origin:
        query = query.filter(Flight.origin == origin)
    if destination:
        query = query.filter(Flight.destination == destination)
    if date:
        query = query.filter(Flight.date == date)
    if max_price:
        query = query.filter(Flight.price <= int(max_price))
    
    results = query.all()
    results_data = [f.to_dict() for f in results]
    
    # Get all flights for dropdown options
    all_flights = Flight.query.all()
    origins = sorted(set([f.origin for f in all_flights]))
    destinations = sorted(set([f.destination for f in all_flights]))

    return render_template(
        "search.html",
        results=results_data,
        q={"origin": origin, "destination": destination, "date": date, "max_price": max_price},
        origins=origins,
        destinations=destinations
    )

@app.route("/flight/<fid>")
def flight_details(fid):
    flight = find_flight(fid)
    if not flight:
        flash("Flight not found", "danger")
        return redirect(url_for("home"))

    flight_data = flight.to_dict()
    return render_template(
        "flight.html",
        flight=flight_data,
        booked=flight.get_booked_seats()
    )


@app.route("/book", methods=["POST"])
def book():
    fid = request.form.get("flight_id")
    fullname = request.form.get("fullname")
    email = request.form.get("email")
    phone = request.form.get("phone")
    seats = request.form.getlist("seats")

    if not seats:
        flash("Please select at least one seat.", "warning")
        return redirect(url_for("flight_details", fid=fid))

    # Find flight
    flight = find_flight(fid)
    if not flight:
        flash("Flight not found", "danger")
        return redirect(url_for("home"))

    try:
        # Start database transaction
        # Validate seat availability
        booked_seats = flight.get_booked_seats()
        for s in seats:
            if s in booked_seats:
                flash(f"Seat {s} already booked!", "danger")
                return redirect(url_for("flight_details", fid=fid))

        # Reserve seats now (mark as booked to avoid race conditions)
        for seat in seats:
            flight.add_booked_seat(seat)
        
        # Generate unique PNR
        pnr = generate_pnr(fid)
        while find_booking(pnr):  # Ensure PNR is unique
            pnr = generate_pnr(fid)

        # Calculate amount using dynamic pricing
        dynamic_price = flight.calculate_dynamic_price()
        
        # Create booking with PENDING status
        booking = Booking(
            pnr=pnr,
            flight_id=fid,
            fullname=fullname,
            email=email,
            phone=phone,
            amount=dynamic_price * len(seats),
            status="PENDING",
            created_at=datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
        )
        booking.set_seats(seats)
        
        db.session.add(booking)
        db.session.commit()

        # Redirect to payment simulation page
        return redirect(url_for("payment", pnr=pnr))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Booking failed: {str(e)}", "danger")
        return redirect(url_for("flight_details", fid=fid))

@app.route("/booking/<pnr>")
def booking_details(pnr):
    booking = find_booking(pnr)
    if not booking:
        flash("Booking not found", "danger")
        return redirect(url_for("home"))

    flight = find_flight(booking.flight_id)
    
    # Convert to dictionary format for template compatibility
    booking_data = booking.to_dict()
    flight_data = flight.to_dict() if flight else None

    # show modal if redirected after payment
    show_modal = True if request.args.get("confirmed") == "1" else False
    return render_template("booking.html", booking=booking_data, flight=flight_data, show_modal=show_modal)

@app.route("/booking_search")
def booking_search():
    pnr = request.args.get("pnr", "").strip()
    if not pnr:
        flash("Enter a PNR to search.", "warning")
        return redirect(url_for("home"))
    
    booking = find_booking(pnr)
    if not booking:
        flash("PNR not found.", "danger")
        return redirect(url_for("home"))
    
    return redirect(url_for("booking_details", pnr=pnr))

@app.route("/ticket/<pnr>/download")
def download_ticket(pnr):
    booking = find_booking(pnr)
    if not booking:
        flash("Booking not found.", "danger")
        return redirect(url_for("home"))
    
    flight = find_flight(booking.flight_id)
    flight_data = flight.to_dict() if flight else {}

    # generate QR (PNG in memory)
    qr_img = qrcode.make(booking.pnr)
    qr_io = BytesIO()
    qr_img.save(qr_io, format="PNG")
    qr_io.seek(0)

    # create PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    c.setFont("Helvetica-Bold", 20)
    c.drawString(40, h - 80, "FlightCraft Studio ✈️ — E-Ticket")
    c.setFont("Helvetica", 12)
    c.drawString(40, h - 120, f"PNR: {booking.pnr}")
    c.drawString(40, h - 140, f"Passenger: {booking.fullname}")
    c.drawString(40, h - 160, f"Phone: {booking.phone}")
    c.drawString(40, h - 180, f"Flight: {flight_data.get('airline','')} ({flight_data.get('id','')})")
    c.drawString(40, h - 200, f"Route: {flight_data.get('origin','')} → {flight_data.get('destination','')}")
    c.drawString(40, h - 220, f"Date/Time: {flight_data.get('date','')} {flight_data.get('dep_time','')}-{flight_data.get('arr_time','')}")
    c.drawString(40, h - 240, f"Seats: {', '.join(booking.get_seats())}")
    # place QR
    img = ImageReader(qr_io)
    c.drawImage(img, w - 180, h - 260, width=120, height=120)
    c.showPage()
    c.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f"ticket_{pnr}.pdf", mimetype="application/pdf")

@app.route("/booking/<pnr>/receipt.json")
def download_json_receipt(pnr):
    """Generate and return booking receipt in JSON format"""
    booking = find_booking(pnr)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    
    flight = find_flight(booking.flight_id)
    if not flight:
        return jsonify({"error": "Flight not found"}), 404
    
    # Calculate dynamic pricing information
    dynamic_price = flight.calculate_dynamic_price()
    occupancy_rate = flight.get_occupancy_rate()
    days_until_departure = flight.get_days_until_departure()
    
    # Create comprehensive receipt data
    receipt_data = {
        "receipt_info": {
            "type": "flight_booking_receipt",
            "format_version": "1.0",
            "generated_at": datetime.datetime.now().isoformat(),
            "system": "FlightCraft Studio ✈️"
        },
        "booking_details": {
            "pnr": booking.pnr,
            "status": booking.status,
            "booking_date": booking.created_at if booking.created_at else None,
            "amount_paid": booking.amount,
            "payment_status": "COMPLETED" if booking.status == "CONFIRMED" else "PENDING",
            "seats_booked": booking.get_seats(),
            "total_passengers": len(booking.get_seats())
        },
        "passenger_info": {
            "full_name": booking.fullname,
            "email": booking.email,
            "phone": booking.phone,
            "contact_method": "SMS and Email"
        },
        "flight_details": {
            "flight_id": flight.id,
            "airline": flight.airline,
            "aircraft_type": getattr(flight, 'aircraft_type', 'Not specified'),
            "route": {
                "origin": {
                    "code": flight.origin,
                    "name": flight.origin
                },
                "destination": {
                    "code": flight.destination,
                    "name": flight.destination
                }
            },
            "schedule": {
                "date": flight.date,
                "departure_time": flight.dep_time,
                "arrival_time": flight.arr_time,
                "duration": "Calculated based on times",
                "timezone": "IST (UTC+5:30)"
            },
            "status": flight.status
        },
        "pricing_info": {
            "base_price": flight.price,
            "dynamic_price": dynamic_price,
            "pricing_factors": {
                "occupancy_rate": round(occupancy_rate * 100, 1),
                "days_until_departure": days_until_departure,
                "demand_level": flight.get_price_trend(),
                "time_based_multiplier": "Applied based on departure time"
            },
            "total_amount": booking.amount,
            "per_seat_price": dynamic_price,
            "currency": "INR",
            "taxes_included": True
        },
        "seat_information": {
            "selected_seats": booking.get_seats(),
            "seat_type": "Economy",
            "seat_preferences": "Standard seating",
            "special_requests": "None"
        },
        "terms_and_conditions": {
            "cancellation_policy": "Cancellation allowed up to 24 hours before departure",
            "refund_policy": "Refunds subject to airline terms and conditions",
            "change_policy": "Changes allowed with fare difference",
            "baggage_policy": "Standard baggage allowance as per airline policy"
        },
        "contact_info": {
            "customer_support": {
                "phone": "+91-1800-123-4567",
                "email": "support@skybook.com",
                "website": "https://skybook.com/support"
            },
            "emergency_contact": {
                "phone": "+91-1800-911-911",
                "available": "24/7"
            }
        },
        "qr_data": {
            "pnr": booking.pnr,
            "verification_url": f"https://skybook.com/verify/{booking.pnr}",
            "mobile_checkin": f"https://skybook.com/checkin/{booking.pnr}"
        },
        "metadata": {
            "receipt_id": f"RCP-{booking.pnr}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
            "booking_reference": booking.pnr,
            "system_version": "2.0",
            "api_version": "1.0"
        }
    }
    
    # Set response headers for JSON download
    response = jsonify(receipt_data)
    response.headers['Content-Disposition'] = f'attachment; filename=receipt_{pnr}.json'
    response.headers['Content-Type'] = 'application/json'
    
    return response


@app.route("/admin", methods=["GET", "POST"])
def admin():
    key = request.form.get("key") or request.args.get("key")
    if key != ADMIN_PASS:
        return render_template("admin_login.html")

    # Get data from database
    flights = Flight.query.all()
    bookings = Booking.query.all()

    # Convert to dictionaries for template compatibility
    flights_data = [f.to_dict() for f in flights]
    bookings_data = [b.to_dict() for b in bookings]

    # Revenue calc
    total_rev = sum(b.amount for b in bookings)

    if request.method == "POST":
        action = request.form.get("action")
        fid = request.form.get("id")

        # 🟢 ADD FLIGHT
        if action == "add":
            try:
                # Check if flight already exists and remove it
                existing_flight = Flight.query.filter_by(id=fid.strip()).first()
                if existing_flight:
                    db.session.delete(existing_flight)
                
                # Create new flight
                amenities = [a.strip() for a in (request.form.get("amenities") or "").split(",") if a.strip()]
                
                new_flight = Flight(
                    id=fid.strip(),
                    airline=request.form.get("airline"),
                    origin=request.form.get("origin"),
                    destination=request.form.get("destination"),
                    date=request.form.get("date"),
                    dep_time=request.form.get("dep_time"),
                    arr_time=request.form.get("arr_time"),
                    price=int(request.form.get("price") or 0),
                    seat_rows=int(request.form.get("rows") or 12),
                    seat_cols=int(request.form.get("cols") or 6),
                    booked_seats=json.dumps([]),  # Empty list for new flights
                    status=request.form.get("status") or "On Time",
                    gate=request.form.get("gate") or "A1",
                    terminal=request.form.get("terminal") or "T1",
                    amenities=json.dumps(amenities)
                )
                
                db.session.add(new_flight)
                db.session.commit()
                flash(f"Flight {fid} added successfully!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Error adding flight: {str(e)}", "danger")

        # 🟡 EDIT FLIGHT
        elif action == "edit":
            try:
                flight = Flight.query.filter_by(id=fid).first()
                if flight:
                    # Update flight attributes
                    flight.airline = request.form.get("airline")
                    flight.origin = request.form.get("origin")
                    flight.destination = request.form.get("destination")
                    flight.date = request.form.get("date")
                    flight.dep_time = request.form.get("dep_time")
                    flight.arr_time = request.form.get("arr_time")
                    flight.price = int(request.form.get("price") or 0)
                    flight.status = request.form.get("status")
                    flight.gate = request.form.get("gate")
                    flight.terminal = request.form.get("terminal")
                    
                    # Update amenities as JSON
                    amenities = [a.strip() for a in (request.form.get("amenities") or "").split(",") if a.strip()]
                    flight.amenities = json.dumps(amenities)
                    
                    db.session.commit()
                    flash(f"Flight {fid} updated successfully!", "info")
                else:
                    flash(f"Flight {fid} not found!", "danger")
            except Exception as e:
                db.session.rollback()
                flash(f"Error updating flight: {str(e)}", "danger")

        # 🔴 REMOVE FLIGHT
        elif action == "remove":
            try:
                flight = Flight.query.filter_by(id=fid).first()
                if flight:
                    db.session.delete(flight)
                    db.session.commit()
                    flash(f"Flight {fid} removed successfully!", "danger")
                else:
                    flash(f"Flight {fid} not found!", "warning")
            except Exception as e:
                db.session.rollback()
                flash(f"Error removing flight: {str(e)}", "danger")

        return redirect(url_for("admin", key=key))

    return render_template("admin.html",
                           flights=flights_data,
                           bookings=bookings_data,
                           total_rev=total_rev,
                           key=ADMIN_PASS)

@app.route("/payment/<pnr>", methods=["GET", "POST"])
def payment(pnr):
    booking = find_booking(pnr)
    if not booking:
        flash("Booking not found.", "danger")
        return redirect(url_for("home"))

    if request.method == "POST":
        try:
            # Simulate payment success
            booking.status = "CONFIRMED"
            db.session.commit()

            flash(f"Payment successful! Booking confirmed. PNR: {pnr}", "success")
            # redirect to booking details and show modal
            return redirect(url_for("booking_details", pnr=pnr, confirmed=1))
        
        except Exception as e:
            db.session.rollback()
            flash(f"Payment failed: {str(e)}", "danger")
            return redirect(url_for("payment", pnr=pnr))

    # GET -> show mock payment page
    return render_template("payment.html", booking=booking.to_dict())

@app.route("/cancel_booking/<pnr>", methods=["POST"])
def cancel_booking(pnr):
    booking = find_booking(pnr)
    if not booking:
        flash("Booking not found.", "danger")
        return redirect(url_for("home"))
    
    if booking.status != "CONFIRMED":
        flash("Only confirmed bookings can be cancelled.", "warning")
        return redirect(url_for("booking_details", pnr=pnr))
    
    try:
        # Load flight and release seats
        flight = find_flight(booking.flight_id)
        
        if flight:
            # Remove booked seats from flight
            for seat in booking.get_seats():
                flight.remove_booked_seat(seat)
        
        # Update booking status to cancelled
        booking.status = "CANCELLED"
        db.session.commit()
        
        flash(f"Booking {pnr} has been cancelled successfully. Seats have been released.", "info")
        return redirect(url_for("booking_details", pnr=pnr))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Cancellation failed: {str(e)}", "danger")
        return redirect(url_for("booking_details", pnr=pnr))

@app.route("/booked_flights")
def booked_flights():
    # Get all bookings from database
    bookings = Booking.query.all()
    
    # Create a dictionary for quick flight lookup
    flights = Flight.query.all()
    flights_dict = {f.id: f.to_dict() for f in flights}
    
    # Combine booking data with flight details
    booked_flights_data = []
    for booking in bookings:
        flight = flights_dict.get(booking.flight_id)
        if flight:
            combined_data = {
                "booking": booking.to_dict(),
                "flight": flight
            }
            booked_flights_data.append(combined_data)
    
    return render_template("booked_flights.html", booked_flights=booked_flights_data)

@app.route("/api-demo")
def api_demo():
    """Display API demo page"""
    return render_template("api_demo.html")

# -------------- API Endpoints for Dynamic Pricing --------------

@app.route("/api/flight/<fid>/price")
def api_get_flight_price(fid):
    """API endpoint to get current dynamic price for a flight"""
    flight = find_flight(fid)
    if not flight:
        return jsonify({"error": "Flight not found"}), 404
    
    return jsonify({
        "flight_id": fid,
        "base_price": flight.price,
        "dynamic_price": flight.calculate_dynamic_price(),
        "price_trend": flight.get_price_trend(),
        "occupancy_rate": flight.get_occupancy_rate(),
        "days_until_departure": flight.get_days_until_departure(),
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route("/api/flights/prices")
def api_get_all_prices():
    """API endpoint to get dynamic prices for all flights"""
    flights = Flight.query.all()
    
    prices_data = []
    for flight in flights:
        prices_data.append({
            "flight_id": flight.id,
            "airline": flight.airline,
            "route": f"{flight.origin} → {flight.destination}",
            "date": flight.date,
            "base_price": flight.price,
            "dynamic_price": flight.calculate_dynamic_price(),
            "price_trend": flight.get_price_trend(),
            "occupancy_rate": round(flight.get_occupancy_rate(), 2)
        })
    
    return jsonify({
        "flights": prices_data,
        "timestamp": datetime.datetime.now().isoformat(),
        "total_flights": len(prices_data)
    })

@app.route("/api/theme", methods=["POST"])
def api_set_theme():
    """API endpoint to save user theme preference"""
    try:
        data = request.get_json()
        if not data or 'theme' not in data:
            return jsonify({"error": "Invalid request. Theme required."}), 400
        
        theme = data['theme']
        if theme not in ['dark', 'light']:
            return jsonify({"error": "Invalid theme. Must be 'dark' or 'light'."}), 400
        
        # For now, just return success (could save to session/database if needed)
        return jsonify({
            "success": True,
            "theme": theme,
            "message": f"Theme set to {theme}",
            "timestamp": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": "Failed to save theme preference"}), 500

@app.route("/api/search/dynamic")
def api_dynamic_search():
    """API endpoint for flight search with dynamic pricing"""
    origin = request.args.get("origin", "").upper()
    destination = request.args.get("destination", "").upper()
    date = request.args.get("date", "")
    max_price = request.args.get("max_price", "")

    # Build query filters
    query = Flight.query
    
    if origin:
        query = query.filter(Flight.origin == origin)
    if destination:
        query = query.filter(Flight.destination == destination)
    if date:
        query = query.filter(Flight.date == date)
    
    results = query.all()
    
    # Filter by dynamic price if max_price is specified
    filtered_results = []
    for flight in results:
        dynamic_price = flight.calculate_dynamic_price()
        if not max_price or dynamic_price <= int(max_price):
            flight_data = flight.to_dict()
            filtered_results.append(flight_data)
    
    return jsonify({
        "flights": filtered_results,
        "search_params": {
            "origin": origin,
            "destination": destination,
            "date": date,
            "max_price": max_price
        },
        "timestamp": datetime.datetime.now().isoformat(),
        "total_results": len(filtered_results)
    })

@app.route("/api/pricing/analysis")
def api_pricing_analysis():
    """API endpoint for detailed pricing analysis and trends"""
    flights = Flight.query.all()
    
    analysis_data = []
    price_trends = {"high": 0, "moderate": 0, "stable": 0, "low": 0}
    avg_price_change = 0
    
    for flight in flights:
        dynamic_price = flight.calculate_dynamic_price()
        pricing_factors = flight.get_pricing_factors()
        trend = flight.get_price_trend()
        price_change = ((dynamic_price - flight.price) / flight.price) * 100
        
        flight_analysis = {
            "flight_id": flight.id,
            "airline": flight.airline,
            "route": f"{flight.origin} → {flight.destination}",
            "base_price": flight.price,
            "dynamic_price": dynamic_price,
            "price_change_percent": round(price_change, 1),
            "trend": trend,
            "factors": {
                "occupancy": f"{pricing_factors['occupancy_rate']}% booked",
                "timing": f"{pricing_factors['days_until_departure']} days until departure",
                "peak_hours": pricing_factors['peak_hours'],
                "multipliers": {
                    "occupancy_factor": pricing_factors['occupancy_factor'],
                    "time_factor": pricing_factors['time_factor'],
                    "peak_hour_factor": pricing_factors['peak_hour_factor']
                }
            }
        }
        
        analysis_data.append(flight_analysis)
        price_trends[trend] += 1
        avg_price_change += price_change
    
    avg_price_change = round(avg_price_change / len(flights), 1) if flights else 0
    
    return jsonify({
        "flights": analysis_data,
        "market_summary": {
            "total_flights": len(flights),
            "average_price_change": f"{avg_price_change}%",
            "trend_distribution": price_trends,
            "market_status": "high_demand" if price_trends["high"] > price_trends["low"] else "stable_market"
        },
        "timestamp": datetime.datetime.now().isoformat()
    })

# ==================== REST API ENDPOINTS ====================
# Comprehensive REST API for frontend integration and external consumption

@app.route("/api/flights", methods=["GET"])
def api_get_flights():
    """API: Get all flights with optional filtering"""
    try:
        # Query parameters
        origin = request.args.get("origin", "").upper()
        destination = request.args.get("destination", "").upper()
        date = request.args.get("date", "")
        airline = request.args.get("airline", "")
        max_price = request.args.get("max_price", "")
        min_price = request.args.get("min_price", "")
        status = request.args.get("status", "")
        sort_by = request.args.get("sort_by", "price")  # price, date, departure_time
        order = request.args.get("order", "asc")  # asc, desc
        include_dynamic_pricing = request.args.get("dynamic_pricing", "true").lower() == "true"

        # Build query
        query = Flight.query
        
        if origin:
            query = query.filter(Flight.origin == origin)
        if destination:
            query = query.filter(Flight.destination == destination)
        if date:
            query = query.filter(Flight.date == date)
        if airline:
            query = query.filter(Flight.airline.ilike(f"%{airline}%"))
        if status:
            query = query.filter(Flight.status.ilike(f"%{status}%"))

        # Execute query
        flights = query.all()
        
        # Process results
        results = []
        for flight in flights:
            flight_data = flight.to_dict()
            
            # Apply price filtering after dynamic price calculation
            current_price = flight_data['dynamic_price'] if include_dynamic_pricing else flight_data['price']
            
            if min_price and current_price < int(min_price):
                continue
            if max_price and current_price > int(max_price):
                continue
                
            results.append(flight_data)

        # Sorting
        if sort_by == "price":
            results.sort(key=lambda x: x['dynamic_price'] if include_dynamic_pricing else x['price'], 
                        reverse=(order == "desc"))
        elif sort_by == "date":
            results.sort(key=lambda x: x['date'], reverse=(order == "desc"))
        elif sort_by == "departure_time":
            results.sort(key=lambda x: x['dep_time'], reverse=(order == "desc"))

        return jsonify({
            "success": True,
            "flights": results,
            "meta": {
                "total_results": len(results),
                "filters_applied": {
                    "origin": origin,
                    "destination": destination,
                    "date": date,
                    "airline": airline,
                    "status": status,
                    "max_price": max_price,
                    "min_price": min_price
                },
                "sort_by": sort_by,
                "order": order,
                "dynamic_pricing_enabled": include_dynamic_pricing,
                "timestamp": datetime.datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/flights/<flight_id>", methods=["GET"])
def api_get_flight(flight_id):
    """API: Get specific flight by ID"""
    try:
        flight = find_flight(flight_id)
        if not flight:
            return jsonify({"success": False, "error": "Flight not found"}), 404
        
        return jsonify({
            "success": True,
            "flight": flight.to_dict(),
            "meta": {
                "timestamp": datetime.datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/flights/<flight_id>/seats", methods=["GET"])
def api_get_flight_seats(flight_id):
    """API: Get seat availability for specific flight"""
    try:
        flight = find_flight(flight_id)
        if not flight:
            return jsonify({"success": False, "error": "Flight not found"}), 404
        
        booked_seats = flight.get_booked_seats()
        total_seats = flight.seat_rows * flight.seat_cols
        available_seats = total_seats - len(booked_seats)
        
        # Generate seat map
        seat_map = []
        for row in range(1, flight.seat_rows + 1):
            for col_idx in range(flight.seat_cols):
                col_letter = chr(65 + col_idx)  # A, B, C, D, E, F
                seat_code = f"{row}{col_letter}"
                seat_map.append({
                    "seat": seat_code,
                    "row": row,
                    "column": col_letter,
                    "available": seat_code not in booked_seats
                })
        
        return jsonify({
            "success": True,
            "flight_id": flight_id,
            "seats": {
                "total": total_seats,
                "booked": len(booked_seats),
                "available": available_seats,
                "occupancy_rate": round(flight.get_occupancy_rate(), 2),
                "booked_seats": booked_seats,
                "seat_map": seat_map
            },
            "meta": {
                "timestamp": datetime.datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/bookings", methods=["GET"])
def api_get_bookings():
    """API: Get all bookings with optional filtering"""
    try:
        # Query parameters
        status = request.args.get("status", "")
        flight_id = request.args.get("flight_id", "")
        email = request.args.get("email", "")
        date_from = request.args.get("date_from", "")
        date_to = request.args.get("date_to", "")
        sort_by = request.args.get("sort_by", "created_at")
        order = request.args.get("order", "desc")

        # Build query
        query = Booking.query
        
        if status:
            query = query.filter(Booking.status.ilike(f"%{status}%"))
        if flight_id:
            query = query.filter(Booking.flight_id == flight_id)
        if email:
            query = query.filter(Booking.email.ilike(f"%{email}%"))

        bookings = query.all()
        
        # Process results with flight details
        results = []
        for booking in bookings:
            booking_data = booking.to_dict()
            
            # Add flight details
            flight = find_flight(booking.flight_id)
            if flight:
                booking_data['flight_details'] = {
                    'airline': flight.airline,
                    'origin': flight.origin,
                    'destination': flight.destination,
                    'date': flight.date,
                    'dep_time': flight.dep_time,
                    'arr_time': flight.arr_time,
                    'status': flight.status,
                    'gate': flight.gate,
                    'terminal': flight.terminal
                }
            
            results.append(booking_data)

        # Sort results
        if sort_by == "created_at":
            results.sort(key=lambda x: x['created_at'], reverse=(order == "desc"))
        elif sort_by == "amount":
            results.sort(key=lambda x: x['amount'], reverse=(order == "desc"))
        elif sort_by == "status":
            results.sort(key=lambda x: x['status'], reverse=(order == "desc"))

        return jsonify({
            "success": True,
            "bookings": results,
            "meta": {
                "total_results": len(results),
                "filters_applied": {
                    "status": status,
                    "flight_id": flight_id,
                    "email": email,
                    "date_from": date_from,
                    "date_to": date_to
                },
                "sort_by": sort_by,
                "order": order,
                "timestamp": datetime.datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/bookings/<pnr>", methods=["GET"])
def api_get_booking(pnr):
    """API: Get specific booking by PNR"""
    try:
        booking = find_booking(pnr)
        if not booking:
            return jsonify({"success": False, "error": "Booking not found"}), 404
        
        booking_data = booking.to_dict()
        
        # Add flight details
        flight = find_flight(booking.flight_id)
        if flight:
            booking_data['flight_details'] = flight.to_dict()
        
        return jsonify({
            "success": True,
            "booking": booking_data,
            "meta": {
                "timestamp": datetime.datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/bookings", methods=["POST"])
def api_create_booking():
    """API: Create new booking"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['flight_id', 'fullname', 'email', 'phone', 'seats']
        for field in required_fields:
            if field not in data:
                return jsonify({"success": False, "error": f"Missing required field: {field}"}), 400

        flight = find_flight(data['flight_id'])
        if not flight:
            return jsonify({"success": False, "error": "Flight not found"}), 404

        # Validate seat availability
        booked_seats = flight.get_booked_seats()
        requested_seats = data['seats']
        
        for seat in requested_seats:
            if seat in booked_seats:
                return jsonify({"success": False, "error": f"Seat {seat} is already booked"}), 400

        # Calculate amount (use dynamic pricing if not provided)
        amount = data.get('amount', flight.calculate_dynamic_price() * len(requested_seats))
        
        # Generate PNR
        pnr = generate_pnr(flight.origin[:2])
        while find_booking(pnr):  # Ensure uniqueness
            pnr = generate_pnr(flight.origin[:2])

        # Create booking
        booking = Booking(
            pnr=pnr,
            flight_id=data['flight_id'],
            fullname=data['fullname'],
            email=data['email'],
            phone=data['phone'],
            seats=json.dumps(requested_seats),
            amount=amount,
            status=data.get('status', 'PENDING'),
            created_at=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

        # Update flight seats
        for seat in requested_seats:
            flight.add_booked_seat(seat)

        db.session.add(booking)
        db.session.commit()

        return jsonify({
            "success": True,
            "booking": booking.to_dict(),
            "message": "Booking created successfully",
            "meta": {
                "timestamp": datetime.datetime.now().isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/bookings/<pnr>", methods=["PUT"])
def api_update_booking(pnr):
    """API: Update booking status or details"""
    try:
        booking = find_booking(pnr)
        if not booking:
            return jsonify({"success": False, "error": "Booking not found"}), 404

        data = request.get_json()
        
        # Update allowed fields
        if 'status' in data:
            old_status = booking.status
            booking.status = data['status']
            
            # Handle seat management for status changes
            if old_status == 'PENDING' and data['status'] == 'CANCELLED':
                # Release seats
                flight = find_flight(booking.flight_id)
                if flight:
                    for seat in booking.get_seats():
                        flight.remove_booked_seat(seat)
        
        if 'fullname' in data:
            booking.fullname = data['fullname']
        if 'email' in data:
            booking.email = data['email']
        if 'phone' in data:
            booking.phone = data['phone']

        db.session.commit()

        return jsonify({
            "success": True,
            "booking": booking.to_dict(),
            "message": "Booking updated successfully",
            "meta": {
                "timestamp": datetime.datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/bookings/<pnr>", methods=["DELETE"])
def api_cancel_booking(pnr):
    """API: Cancel booking (alternative to PUT with status=CANCELLED)"""
    try:
        booking = find_booking(pnr)
        if not booking:
            return jsonify({"success": False, "error": "Booking not found"}), 404

        if booking.status == 'CANCELLED':
            return jsonify({"success": False, "error": "Booking already cancelled"}), 400

        # Update status and release seats
        booking.status = 'CANCELLED'
        
        flight = find_flight(booking.flight_id)
        if flight:
            for seat in booking.get_seats():
                flight.remove_booked_seat(seat)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Booking cancelled successfully",
            "booking": booking.to_dict(),
            "meta": {
                "timestamp": datetime.datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/search", methods=["GET"])
def api_flight_search():
    """API: Enhanced flight search with comprehensive filtering"""
    return api_get_flights()  # Reuse the flights endpoint with filtering

@app.route("/api/airports", methods=["GET"])
def api_get_airports():
    """API: Get list of available airports/cities from flights"""
    try:
        flights = Flight.query.all()
        
        origins = set()
        destinations = set()
        
        for flight in flights:
            origins.add(flight.origin)
            destinations.add(flight.destination)
        
        airports = list(origins.union(destinations))
        
        return jsonify({
            "success": True,
            "airports": sorted(airports),
            "origins": sorted(list(origins)),
            "destinations": sorted(list(destinations)),
            "meta": {
                "total_airports": len(airports),
                "timestamp": datetime.datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/airlines", methods=["GET"])
def api_get_airlines():
    """API: Get list of available airlines"""
    try:
        flights = Flight.query.all()
        airlines = list(set(flight.airline for flight in flights))
        
        airline_stats = {}
        for airline in airlines:
            airline_flights = [f for f in flights if f.airline == airline]
            airline_stats[airline] = {
                "total_flights": len(airline_flights),
                "routes": len(set(f"{f.origin}-{f.destination}" for f in airline_flights)),
                "avg_price": round(sum(f.price for f in airline_flights) / len(airline_flights), 2)
            }
        
        return jsonify({
            "success": True,
            "airlines": sorted(airlines),
            "airline_stats": airline_stats,
            "meta": {
                "total_airlines": len(airlines),
                "timestamp": datetime.datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/stats", methods=["GET"])
def api_get_stats():
    """API: Get system statistics"""
    try:
        flights = Flight.query.all()
        bookings = Booking.query.all()
        
        # Flight stats
        total_flights = len(flights)
        total_routes = len(set(f"{f.origin}-{f.destination}" for f in flights))
        avg_price = round(sum(f.price for f in flights) / total_flights, 2) if total_flights > 0 else 0
        
        # Booking stats
        total_bookings = len(bookings)
        confirmed_bookings = len([b for b in bookings if b.status == 'CONFIRMED'])
        pending_bookings = len([b for b in bookings if b.status == 'PENDING'])
        cancelled_bookings = len([b for b in bookings if b.status == 'CANCELLED'])
        
        total_revenue = sum(b.amount for b in bookings if b.status == 'CONFIRMED')
        
        # Occupancy stats
        total_seats = sum(f.seat_rows * f.seat_cols for f in flights)
        total_booked_seats = sum(len(f.get_booked_seats()) for f in flights)
        overall_occupancy = round((total_booked_seats / total_seats) * 100, 2) if total_seats > 0 else 0
        
        return jsonify({
            "success": True,
            "stats": {
                "flights": {
                    "total": total_flights,
                    "total_routes": total_routes,
                    "avg_price": avg_price,
                    "total_seats": total_seats,
                    "booked_seats": total_booked_seats,
                    "overall_occupancy_percent": overall_occupancy
                },
                "bookings": {
                    "total": total_bookings,
                    "confirmed": confirmed_bookings,
                    "pending": pending_bookings,
                    "cancelled": cancelled_bookings,
                    "total_revenue": total_revenue
                }
            },
            "meta": {
                "timestamp": datetime.datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== API DOCUMENTATION ENDPOINT ====================

@app.route("/api", methods=["GET"])
def api_documentation():
    """API: Documentation and available endpoints"""
    return jsonify({
        "message": "FlightCraft Studio ✈️ REST API",
        "version": "1.0.0",
        "endpoints": {
            "flights": {
                "GET /api/flights": "List all flights with filtering options",
                "GET /api/flights/<id>": "Get specific flight details",
                "GET /api/flights/<id>/seats": "Get seat availability for flight"
            },
            "bookings": {
                "GET /api/bookings": "List all bookings with filtering options",
                "GET /api/bookings/<pnr>": "Get specific booking details",
                "POST /api/bookings": "Create new booking",
                "PUT /api/bookings/<pnr>": "Update booking",
                "DELETE /api/bookings/<pnr>": "Cancel booking"
            },
            "search": {
                "GET /api/search": "Search flights (alias for /api/flights)",
                "GET /api/search/dynamic": "Search flights with dynamic pricing"
            },
            "pricing": {
                "GET /api/flight/<id>/price": "Get dynamic price for specific flight",
                "GET /api/flights/prices": "Get dynamic prices for all flights"
            },
            "utilities": {
                "GET /api/airports": "List available airports/cities",
                "GET /api/airlines": "List available airlines with stats",
                "GET /api/stats": "System statistics and overview"
            }
        },
        "query_parameters": {
            "flights": ["origin", "destination", "date", "airline", "max_price", "min_price", "status", "sort_by", "order", "dynamic_pricing"],
            "bookings": ["status", "flight_id", "email", "date_from", "date_to", "sort_by", "order"]
        },
        "response_format": {
            "success": "boolean - indicates operation success",
            "data": "object/array - main response data",
            "meta": "object - metadata including timestamp and query info",
            "error": "string - error message (only when success=false)"
        },
        "meta": {
            "timestamp": datetime.datetime.now().isoformat(),
            "total_endpoints": 16
        }
    })

if __name__ == "__main__":
    app.run(debug=True)
