"""
API Tests for REST Endpoints
"""

import pytest
import json
from playwright.config import BASE_URL

@pytest.mark.api
@pytest.mark.smoke
def test_api_root_endpoint(api_client, api_headers):
    """Test API root endpoint"""
    response = api_client.get(f"{BASE_URL}/api", headers=api_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data or "endpoints" in data or "version" in data

@pytest.mark.api
def test_api_flights_endpoint(api_client, api_headers):
    """Test flights API endpoint"""
    response = api_client.get(f"{BASE_URL}/api/flights", headers=api_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert data["success"] is True
    assert "flights" in data or "data" in data

@pytest.mark.api
def test_api_flights_filtering(api_client, api_headers):
    """Test flights API with filtering"""
    params = {
        "origin": "DEL",
        "destination": "BOM"
    }
    
    response = api_client.get(f"{BASE_URL}/api/flights", params=params, headers=api_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert data["success"] is True
    
    # Check if filtering was applied
    if "meta" in data:
        assert "filters_applied" in data["meta"]

@pytest.mark.api
def test_api_specific_flight(api_client, api_headers):
    """Test specific flight API endpoint"""
    # First get list of flights to find a valid flight ID
    flights_response = api_client.get(f"{BASE_URL}/api/flights", headers=api_headers)
    assert flights_response.status_code == 200
    
    flights_data = flights_response.json()
    if "flights" in flights_data and flights_data["flights"]:
        flight_id = flights_data["flights"][0]["id"]
        
        # Test specific flight endpoint
        response = api_client.get(f"{BASE_URL}/api/flights/{flight_id}", headers=api_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "flight" in data or "data" in data

@pytest.mark.api
def test_api_flight_seats(api_client, api_headers):
    """Test flight seats API endpoint"""
    # Get a flight ID first
    flights_response = api_client.get(f"{BASE_URL}/api/flights", headers=api_headers)
    assert flights_response.status_code == 200
    
    flights_data = flights_response.json()
    if "flights" in flights_data and flights_data["flights"]:
        flight_id = flights_data["flights"][0]["id"]
        
        # Test seats endpoint
        response = api_client.get(f"{BASE_URL}/api/flights/{flight_id}/seats", headers=api_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "seats" in data or "seat_map" in data

@pytest.mark.api
def test_api_bookings_endpoint(api_client, api_headers):
    """Test bookings API endpoint"""
    response = api_client.get(f"{BASE_URL}/api/bookings", headers=api_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert data["success"] is True
    assert "bookings" in data or "data" in data

@pytest.mark.api
def test_api_search_endpoint(api_client, api_headers):
    """Test search API endpoint"""
    params = {
        "origin": "DEL",
        "destination": "BOM",
        "date": "2024-12-25"
    }
    
    response = api_client.get(f"{BASE_URL}/api/search", params=params, headers=api_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert data["success"] is True

@pytest.mark.api
def test_api_airports_endpoint(api_client, api_headers):
    """Test airports API endpoint"""
    response = api_client.get(f"{BASE_URL}/api/airports", headers=api_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert data["success"] is True
    assert "airports" in data or "data" in data

@pytest.mark.api
def test_api_airlines_endpoint(api_client, api_headers):
    """Test airlines API endpoint"""
    response = api_client.get(f"{BASE_URL}/api/airlines", headers=api_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert data["success"] is True
    assert "airlines" in data or "data" in data

@pytest.mark.api
def test_api_stats_endpoint(api_client, api_headers):
    """Test statistics API endpoint"""
    response = api_client.get(f"{BASE_URL}/api/stats", headers=api_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert data["success"] is True
    assert "stats" in data or "data" in data

@pytest.mark.api
def test_api_booking_creation(api_client, api_headers, sample_passenger):
    """Test booking creation API"""
    # First get a flight to book
    flights_response = api_client.get(f"{BASE_URL}/api/flights", headers=api_headers)
    assert flights_response.status_code == 200
    
    flights_data = flights_response.json()
    if "flights" in flights_data and flights_data["flights"]:
        flight_id = flights_data["flights"][0]["id"]
        
        # Create booking payload
        booking_data = {
            "flight_id": flight_id,
            "passenger_name": sample_passenger["name"],
            "passenger_email": sample_passenger["email"],
            "passenger_phone": sample_passenger["phone"],
            "seat_number": "1A"
        }
        
        # Test booking creation
        response = api_client.post(
            f"{BASE_URL}/api/bookings", 
            json=booking_data, 
            headers=api_headers
        )
        
        # Should either succeed or give validation error
        assert response.status_code in [200, 201, 400, 422]
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert "success" in data
            assert "pnr" in data or "booking" in data

@pytest.mark.api
def test_api_error_handling(api_client, api_headers):
    """Test API error handling"""
    # Test non-existent flight
    response = api_client.get(f"{BASE_URL}/api/flights/NONEXISTENT", headers=api_headers)
    assert response.status_code == 404
    
    data = response.json()
    assert "success" in data
    assert data["success"] is False
    assert "error" in data or "message" in data

@pytest.mark.api
def test_api_content_type(api_client):
    """Test API returns JSON content type"""
    response = api_client.get(f"{BASE_URL}/api/flights")
    
    assert response.status_code == 200
    assert "application/json" in response.headers.get("Content-Type", "")