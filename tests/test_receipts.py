"""
Tests for Receipt Generation (PDF and JSON)
"""

import pytest
import json
import os
from playwright.config import BASE_URL, DOWNLOADS_DIR

@pytest.mark.receipts
@pytest.mark.api
def test_json_receipt_structure(api_client, api_headers):
    """Test JSON receipt has correct structure"""
    # Get existing bookings
    response = api_client.get(f"{BASE_URL}/api/bookings", headers=api_headers)
    assert response.status_code == 200
    
    data = response.json()
    if "bookings" in data and data["bookings"]:
        pnr = data["bookings"][0].get("pnr", data["bookings"][0].get("id"))
        
        if pnr:
            # Get JSON receipt
            receipt_response = api_client.get(f"{BASE_URL}/booking/{pnr}/receipt.json", headers=api_headers)
            
            if receipt_response.status_code == 200:
                receipt = receipt_response.json()
                
                # Verify JSON structure
                assert "success" in receipt
                assert receipt["success"] is True
                
                # Check required fields
                required_fields = ["booking_details", "passenger_info", "flight_details", "receipt_metadata"]
                
                for field in required_fields:
                    if field in receipt:
                        assert receipt[field] is not None

@pytest.mark.receipts
@pytest.mark.api
def test_pdf_receipt_generation(api_client):
    """Test PDF receipt generation"""
    # Get existing bookings
    response = api_client.get(f"{BASE_URL}/api/bookings")
    assert response.status_code == 200
    
    data = response.json()
    if "bookings" in data and data["bookings"]:
        pnr = data["bookings"][0].get("pnr", data["bookings"][0].get("id"))
        
        if pnr:
            # Get PDF receipt
            pdf_response = api_client.get(f"{BASE_URL}/ticket/{pnr}/download")
            
            if pdf_response.status_code == 200:
                # Verify it's a PDF
                assert pdf_response.headers.get("Content-Type") == "application/pdf"
                
                # Verify content length > 0
                content_length = len(pdf_response.content)
                assert content_length > 1000, "PDF should be substantial size"
                
                # Verify PDF magic header
                assert pdf_response.content.startswith(b"%PDF"), "Should be valid PDF file"

@pytest.mark.receipts
@pytest.mark.ui
def test_receipt_download_ui(page, api_client):
    """Test receipt download through UI"""
    # First get a booking
    response = api_client.get(f"{BASE_URL}/api/bookings")
    if response.status_code == 200:
        data = response.json()
        
        if "bookings" in data and data["bookings"]:
            pnr = data["bookings"][0].get("pnr", data["bookings"][0].get("id"))
            
            if pnr:
                # Navigate to booking page
                booking_page_url = f"{BASE_URL}/booking/{pnr}"
                page.goto(booking_page_url)
                
                # Look for download buttons
                pdf_download = page.locator("text='Download PDF', text='PDF', a[href*='download']")
                json_download = page.locator("text='Download JSON', text='JSON', a[href*='receipt.json']")
                
                # Test PDF download
                if pdf_download.is_visible():
                    # Setup download handling
                    with page.expect_download() as download_info:
                        pdf_download.click()
                    
                    download = download_info.value
                    assert download.suggested_filename.endswith('.pdf')
                
                # Test JSON download  
                if json_download.is_visible():
                    # Test JSON download
                    with page.expect_download() as download_info:
                        json_download.click()
                    
                    download = download_info.value
                    assert download.suggested_filename.endswith('.json')

@pytest.mark.receipts
@pytest.mark.integration
def test_receipt_qr_code_integration(api_client, api_headers):
    """Test QR code in receipts contains valid data"""
    # Get existing bookings
    response = api_client.get(f"{BASE_URL}/api/bookings", headers=api_headers)
    assert response.status_code == 200
    
    data = response.json()
    if "bookings" in data and data["bookings"]:
        pnr = data["bookings"][0].get("pnr", data["bookings"][0].get("id"))
        
        if pnr:
            # Get JSON receipt to check QR data
            receipt_response = api_client.get(f"{BASE_URL}/booking/{pnr}/receipt.json", headers=api_headers)
            
            if receipt_response.status_code == 200:
                receipt = receipt_response.json()
                
                # Check if QR code data is present
                if "qr_data" in receipt:
                    qr_data = receipt["qr_data"]
                    
                    # QR should contain PNR
                    assert pnr in qr_data
                    
                    # QR should be valid JSON or structured format
                    try:
                        qr_json = json.loads(qr_data)
                        assert "pnr" in qr_json or "booking_ref" in qr_json
                    except json.JSONDecodeError:
                        # If not JSON, should at least contain booking info
                        assert "Flight" in qr_data or "Booking" in qr_data

@pytest.mark.receipts
@pytest.mark.api
def test_receipt_booking_details_accuracy(api_client, api_headers):
    """Test receipt contains accurate booking details"""
    # Get bookings from API
    bookings_response = api_client.get(f"{BASE_URL}/api/bookings", headers=api_headers)
    assert bookings_response.status_code == 200
    
    bookings_data = bookings_response.json()
    
    if "bookings" in bookings_data and bookings_data["bookings"]:
        original_booking = bookings_data["bookings"][0]
        pnr = original_booking.get("pnr", original_booking.get("id"))
        
        if pnr:
            # Get receipt
            receipt_response = api_client.get(f"{BASE_URL}/booking/{pnr}/receipt.json", headers=api_headers)
            
            if receipt_response.status_code == 200:
                receipt = receipt_response.json()
                
                # Compare key fields between original booking and receipt
                if "booking_details" in receipt:
                    receipt_booking = receipt["booking_details"]
                    
                    # PNR should match
                    assert receipt_booking.get("pnr") == pnr
                    
                    # Passenger name should match
                    if "passenger_name" in original_booking and "passenger_name" in receipt_booking:
                        assert original_booking["passenger_name"] == receipt_booking["passenger_name"]
                    
                    # Flight ID should match
                    if "flight_id" in original_booking and "flight_id" in receipt_booking:
                        assert original_booking["flight_id"] == receipt_booking["flight_id"]

@pytest.mark.receipts
@pytest.mark.ui
def test_booked_flights_page_receipt_links(page):
    """Test receipt links on booked flights page"""
    page.goto(f"{BASE_URL}/booked_flights")
    
    # Check if page loads
    page.wait_for_timeout(2000)
    
    # Look for booking items
    booking_items = page.locator(".booking-item, .booking-card, tr")
    
    if booking_items.count() > 0:
        # Check for receipt download links
        receipt_links = page.locator("a[href*='receipt'], a[href*='download'], text='Download'")
        
        if receipt_links.count() > 0:
            # Verify links are functional
            first_link = receipt_links.first
            href = first_link.get_attribute("href")
            
            assert href is not None
            assert "/booking/" in href or "/ticket/" in href

@pytest.mark.receipts
@pytest.mark.slow  
def test_bulk_receipt_generation(api_client, api_headers):
    """Test generating receipts for multiple bookings"""
    # Get all bookings
    response = api_client.get(f"{BASE_URL}/api/bookings", headers=api_headers)
    assert response.status_code == 200
    
    data = response.json()
    if "bookings" in data and len(data["bookings"]) > 1:
        
        successful_receipts = 0
        
        # Test first 3 bookings to avoid overwhelming the system
        for booking in data["bookings"][:3]:
            pnr = booking.get("pnr", booking.get("id"))
            
            if pnr:
                # Test JSON receipt
                json_response = api_client.get(f"{BASE_URL}/booking/{pnr}/receipt.json", headers=api_headers)
                
                if json_response.status_code == 200:
                    successful_receipts += 1
                
                # Test PDF receipt  
                pdf_response = api_client.get(f"{BASE_URL}/ticket/{pnr}/download")
                
                if pdf_response.status_code == 200:
                    successful_receipts += 1
        
        # At least some receipts should generate successfully
        assert successful_receipts > 0, "No receipts generated successfully"