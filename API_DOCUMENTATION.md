# Flight Reservation System REST API Documentation

## Overview
This document provides comprehensive documentation for the Flight Reservation System REST API endpoints. The API provides JSON responses for all operations including flight search, booking management, pricing, and system utilities.

**Base URL:** `http://127.0.0.1:5000`  
**API Version:** 1.0.0  
**Response Format:** JSON

## Common Response Structure
```json
{
  "success": true/false,
  "data": {...},  // Main response data
  "meta": {       // Metadata
    "timestamp": "ISO-8601 datetime",
    "total_results": number,
    "filters_applied": {...}
  },
  "error": "string"  // Only present when success=false
}
```

## Authentication
Currently, no authentication is required for API endpoints. In a production environment, implement API keys or OAuth2.

---

## Flight APIs

### 1. Get All Flights
**Endpoint:** `GET /api/flights`  
**Description:** Retrieve all flights with optional filtering and sorting

**Query Parameters:**
- `origin` (string): Filter by departure airport code (e.g., "DEL")
- `destination` (string): Filter by arrival airport code (e.g., "BOM")
- `date` (string): Filter by flight date (YYYY-MM-DD format)
- `airline` (string): Filter by airline name (partial match)
- `max_price` (integer): Maximum price filter (applies to dynamic price if enabled)
- `min_price` (integer): Minimum price filter
- `status` (string): Filter by flight status (e.g., "On Time", "Delayed")
- `sort_by` (string): Sort field - "price", "date", "departure_time" (default: "price")
- `order` (string): Sort order - "asc" or "desc" (default: "asc")
- `dynamic_pricing` (boolean): Enable dynamic pricing calculations (default: "true")

**Example Request:**
```
GET /api/flights?origin=DEL&destination=BOM&dynamic_pricing=true&sort_by=price&order=asc
```

**Example Response:**
```json
{
  "success": true,
  "flights": [
    {
      "id": "AI101",
      "airline": "Air India",
      "origin": "DEL",
      "destination": "BOM",
      "date": "2025-09-08",
      "dep_time": "09:00",
      "arr_time": "11:15",
      "price": 5800,
      "dynamic_price": 12850,
      "price_trend": "high",
      "occupancy_rate": 0.23,
      "days_until_departure": 0,
      "status": "On Time",
      "gate": "A2",
      "terminal": "T3",
      "seats": {
        "rows": 15,
        "cols": 6,
        "booked": ["1A", "1B", "1C", ...]
      },
      "amenities": ["1 Cabin Bag", "Meal Included"]
    }
  ],
  "meta": {
    "total_results": 2,
    "filters_applied": {
      "origin": "DEL",
      "destination": "BOM"
    },
    "sort_by": "price",
    "order": "asc",
    "dynamic_pricing_enabled": true,
    "timestamp": "2025-10-22T20:23:41.663194"
  }
}
```

### 2. Get Specific Flight
**Endpoint:** `GET /api/flights/{flight_id}`  
**Description:** Get detailed information about a specific flight

**Path Parameters:**
- `flight_id` (string): Unique flight identifier

**Example Request:**
```
GET /api/flights/AI101
```

### 3. Get Flight Seat Availability
**Endpoint:** `GET /api/flights/{flight_id}/seats`  
**Description:** Get comprehensive seat availability and seat map for a specific flight

**Example Response:**
```json
{
  "success": true,
  "flight_id": "AI101",
  "seats": {
    "total": 90,
    "booked": 21,
    "available": 69,
    "occupancy_rate": 0.23,
    "booked_seats": ["1A", "1B", "1C", ...],
    "seat_map": [
      {
        "seat": "1A",
        "row": 1,
        "column": "A",
        "available": false
      },
      {
        "seat": "1B",
        "row": 1,
        "column": "B",
        "available": false
      }
    ]
  }
}
```

---

## Booking APIs

### 4. Get All Bookings
**Endpoint:** `GET /api/bookings`  
**Description:** Retrieve all bookings with optional filtering

**Query Parameters:**
- `status` (string): Filter by booking status ("CONFIRMED", "PENDING", "CANCELLED")
- `flight_id` (string): Filter by specific flight ID
- `email` (string): Filter by customer email (partial match)
- `date_from` (string): Filter bookings from this date
- `date_to` (string): Filter bookings until this date
- `sort_by` (string): Sort field - "created_at", "amount", "status" (default: "created_at")
- `order` (string): Sort order - "asc" or "desc" (default: "desc")

### 5. Get Specific Booking
**Endpoint:** `GET /api/bookings/{pnr}`  
**Description:** Get detailed booking information including flight details

**Example Response:**
```json
{
  "success": true,
  "booking": {
    "pnr": "AI101-CARC",
    "flight_id": "AI101",
    "fullname": "Adithya",
    "email": "mp4248728@gmail.com",
    "phone": "7353787686",
    "seats": ["1E"],
    "amount": 12850,
    "status": "CONFIRMED",
    "created_at": "22-10-2025 20:04",
    "flight_details": {
      "airline": "Air India",
      "origin": "DEL",
      "destination": "BOM",
      "date": "2025-09-08",
      "dep_time": "09:00",
      "arr_time": "11:15",
      "gate": "A2",
      "terminal": "T3",
      "status": "On Time"
    }
  }
}
```

### 6. Create New Booking
**Endpoint:** `POST /api/bookings`  
**Description:** Create a new flight booking

**Request Body:**
```json
{
  "flight_id": "AI101",
  "fullname": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+91-9876543210",
  "seats": ["5A", "5B"],
  "status": "PENDING"  // optional, defaults to "PENDING"
}
```

**Response:** Returns created booking details with generated PNR and calculated amount.

### 7. Update Booking
**Endpoint:** `PUT /api/bookings/{pnr}`  
**Description:** Update booking details or status

**Request Body:**
```json
{
  "status": "CONFIRMED",
  "fullname": "Updated Name",
  "email": "new.email@example.com",
  "phone": "+91-9999999999"
}
```

### 8. Cancel Booking
**Endpoint:** `DELETE /api/bookings/{pnr}`  
**Description:** Cancel a booking and release seats

**Response:** Returns confirmation of cancellation with updated booking status.

---

## Search APIs

### 9. Search Flights
**Endpoint:** `GET /api/search`  
**Description:** Enhanced flight search (alias for /api/flights with comprehensive filtering)

### 10. Dynamic Search
**Endpoint:** `GET /api/search/dynamic`  
**Description:** Legacy dynamic search endpoint with pricing calculations

---

## Pricing APIs

### 11. Get Flight Price
**Endpoint:** `GET /api/flight/{flight_id}/price`  
**Description:** Get current dynamic pricing information for a specific flight

**Example Response:**
```json
{
  "flight_id": "AI101",
  "base_price": 5800,
  "dynamic_price": 12850,
  "price_trend": "high",
  "occupancy_rate": 0.23,
  "days_until_departure": 0,
  "timestamp": "2025-10-22T20:23:37.493871"
}
```

### 12. Get All Flight Prices
**Endpoint:** `GET /api/flights/prices`  
**Description:** Get dynamic pricing for all flights

---

## Utility APIs

### 13. Get Airports
**Endpoint:** `GET /api/airports`  
**Description:** Get list of available airports/cities

**Example Response:**
```json
{
  "success": true,
  "airports": ["AMD", "BLR", "BOM", "CCU", "DEL", "GOI", "HYD", "MAA", "MAN", "PNQ"],
  "origins": ["AMD", "BLR", "BOM", "DEL", "MAA", "MAN", "PNQ"],
  "destinations": ["BOM", "CCU", "DEL", "GOI", "HYD", "MAA"],
  "meta": {
    "total_airports": 10,
    "timestamp": "2025-10-22T20:23:41.663194"
  }
}
```

### 14. Get Airlines
**Endpoint:** `GET /api/airlines`  
**Description:** Get list of available airlines with statistics

**Example Response:**
```json
{
  "success": true,
  "airlines": ["Air India", "Akasa Air", "IndiGo", "SpiceJet", "Vistara", "indigo"],
  "airline_stats": {
    "Air India": {
      "total_flights": 5,
      "routes": 4,
      "avg_price": 5520.0
    }
  }
}
```

### 15. Get System Statistics
**Endpoint:** `GET /api/stats`  
**Description:** Get comprehensive system statistics

**Example Response:**
```json
{
  "success": true,
  "stats": {
    "flights": {
      "total": 12,
      "total_routes": 11,
      "avg_price": 4640.83,
      "total_seats": 954,
      "booked_seats": 53,
      "overall_occupancy_percent": 5.56
    },
    "bookings": {
      "total": 13,
      "confirmed": 6,
      "pending": 5,
      "cancelled": 2,
      "total_revenue": 80650
    }
  }
}
```

---

## API Documentation Endpoint

### 16. Get API Documentation
**Endpoint:** `GET /api`  
**Description:** Get comprehensive API documentation and endpoint listing

---

## Error Handling

### HTTP Status Codes
- `200` - Success
- `201` - Created (for POST requests)
- `400` - Bad Request (validation errors)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error

### Error Response Format
```json
{
  "success": false,
  "error": "Detailed error message",
  "meta": {
    "timestamp": "2025-10-22T20:23:41.663194"
  }
}
```

## Usage Examples

### JavaScript/Frontend Integration
```javascript
// Initialize API client
const api = new FlightReservationAPI('http://127.0.0.1:5000');

// Search flights
const flights = await api.getFlights({
  origin: 'DEL',
  destination: 'BOM',
  dynamic_pricing: 'true'
});

// Create booking
const booking = await api.createBooking({
  flight_id: 'AI101',
  fullname: 'John Doe',
  email: 'john@example.com',
  phone: '+91-9876543210',
  seats: ['5A', '5B']
});

// Get booking details
const bookingDetails = await api.getBooking('AI101-CARC');
```

### cURL Examples
```bash
# Get all flights
curl -X GET "http://127.0.0.1:5000/api/flights"

# Search flights with filters
curl -X GET "http://127.0.0.1:5000/api/flights?origin=DEL&destination=BOM&dynamic_pricing=true"

# Get flight details
curl -X GET "http://127.0.0.1:5000/api/flights/AI101"

# Create booking
curl -X POST "http://127.0.0.1:5000/api/bookings" \
  -H "Content-Type: application/json" \
  -d '{
    "flight_id": "AI101",
    "fullname": "John Doe",
    "email": "john@example.com",
    "phone": "+91-9876543210",
    "seats": ["5A", "5B"]
  }'

# Update booking status
curl -X PUT "http://127.0.0.1:5000/api/bookings/AI101-CARC" \
  -H "Content-Type: application/json" \
  -d '{"status": "CONFIRMED"}'

# Cancel booking
curl -X DELETE "http://127.0.0.1:5000/api/bookings/AI101-CARC"
```

## Rate Limiting & Best Practices

1. **Pagination**: For large datasets, consider implementing pagination parameters (`page`, `limit`)
2. **Caching**: Implement caching for frequently accessed data like flight lists
3. **Validation**: Always validate input parameters and provide meaningful error messages
4. **Security**: In production, implement proper authentication and rate limiting
5. **Monitoring**: Log API usage and monitor for unusual patterns

## Integration with Frontend

The REST API is fully integrated with the existing Flask web application:
- All existing HTML routes continue to work
- New `/api-demo` page provides interactive API testing interface
- JavaScript client library (`api-examples.js`) demonstrates usage patterns
- APIs support both manual testing and programmatic access

This API layer enables:
- Mobile app development
- Third-party integrations
- Modern frontend frameworks (React, Vue, Angular)
- Microservices architecture migration
- API-first development approach

---

*This documentation is automatically generated from the API endpoints. For the most up-to-date information, access the live documentation at `/api`.*