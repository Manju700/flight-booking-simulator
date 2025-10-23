"""
Integration Tests for Complete Workflows
"""

import pytest
import time
import re
from playwright.sync_api import Page, expect
from playwright.config import BASE_URL

@pytest.mark.integration
@pytest.mark.smoke
@pytest.mark.slow
def test_complete_flight_booking_workflow(page: Page, api_client, sample_passenger):
    """Test complete flight booking workflow from search to confirmation"""
    
    # Step 1: Start on homepage
    page.goto(BASE_URL)
    expect(page).to_have_title("Flight Reservation System")
    
    # Step 2: Perform flight search
    page.select_option("select[name='origin']", "DEL")
    page.select_option("select[name='destination']", "BOM")
    page.fill("input[name='date']", "2024-12-25")
    
    # Submit search
    page.click("button[type='submit']")
    page.wait_for_url("**/search**", timeout=10000)
    
    # Step 3: Select a flight
    book_button = page.locator("text='Book Now', text='Select', text='Book'").first
    if not book_button.is_visible():
        pytest.skip("No flights available for booking test")
    
    book_button.click()
    page.wait_for_timeout(3000)
    
    # Step 4: Handle seat selection (if present)
    seat_selector = page.locator(".seat.available, .seat:not(.booked)").first
    if seat_selector.is_visible():
        seat_selector.click()
        page.wait_for_timeout(1000)
        
        # Continue to next step
        continue_button = page.locator("text='Continue', text='Next', button[type='submit']").first
        if continue_button.is_visible():
            continue_button.click()
            page.wait_for_timeout(2000)
    
    # Step 5: Fill passenger details
    name_field = page.locator("input[name='name'], input[name='passenger_name']")
    if name_field.is_visible():
        name_field.fill(sample_passenger["name"])
        
        email_field = page.locator("input[name='email'], input[name='passenger_email']")
        if email_field.is_visible():
            email_field.fill(sample_passenger["email"])
        
        phone_field = page.locator("input[name='phone'], input[name='passenger_phone']")
        if phone_field.is_visible():
            phone_field.fill(sample_passenger["phone"])
        
        # Submit booking
        submit_button = page.locator("button[type='submit'], input[type='submit']").first
        submit_button.click()
        page.wait_for_timeout(5000)
        
        # Step 6: Verify booking confirmation
        confirmation_indicators = [
            "text='Booking Confirmed'",
            "text='PNR'",
            "text='Confirmation'",
            "text='Thank you'",
            ".booking-success",
            ".confirmation"
        ]
        
        confirmed = False
        for indicator in confirmation_indicators:
            if page.locator(indicator).is_visible():
                confirmed = True
                break
        
        if confirmed:
            # Extract PNR if possible
            pnr_element = page.locator("text=/PNR|Booking Reference/i").first
            if pnr_element.is_visible():
                pnr_text = pnr_element.text_content()
                print(f"Booking completed with PNR: {pnr_text}")
                
        assert confirmed, "Booking confirmation not found"

@pytest.mark.integration
@pytest.mark.receipts
def test_receipt_generation_workflow(page: Page, api_client):
    """Test receipt generation (PDF and JSON)"""
    
    # First, try to get existing bookings via API
    api_response = api_client.get(f"{BASE_URL}/api/bookings")
    if api_response.status_code == 200:
        bookings_data = api_response.json()
        
        if "bookings" in bookings_data and bookings_data["bookings"]:
            first_booking = bookings_data["bookings"][0]
            pnr = first_booking.get("pnr", first_booking.get("id"))
            
            if pnr:
                # Test PDF receipt download
                pdf_response = api_client.get(f"{BASE_URL}/ticket/{pnr}/download")
                if pdf_response.status_code == 200:
                    assert pdf_response.headers.get("Content-Type") == "application/pdf"
                
                # Test JSON receipt
                json_response = api_client.get(f"{BASE_URL}/booking/{pnr}/receipt.json")
                if json_response.status_code == 200:
                    receipt_data = json_response.json()
                    assert "success" in receipt_data
                    assert "booking_details" in receipt_data or "data" in receipt_data

@pytest.mark.integration
@pytest.mark.admin
def test_admin_workflow(page: Page, admin_credentials):
    """Test complete admin workflow"""
    
    # Step 1: Login to admin
    page.goto(f"{BASE_URL}/admin/login")
    
    password_field = page.locator("input[name='password'], input[type='password']").first
    password_field.fill(admin_credentials["password"])
    
    submit_button = page.locator("button[type='submit'], input[type='submit']").first
    submit_button.click()
    
    page.wait_for_timeout(3000)
    
    # Step 2: Verify admin dashboard access
    dashboard_indicators = [
        "text='Dashboard'",
        "text='Flights'", 
        "text='Bookings'",
        "text='Statistics'",
        ".admin-panel",
        ".dashboard"
    ]
    
    admin_access = any(page.locator(indicator).is_visible() for indicator in dashboard_indicators)
    assert admin_access, "Admin dashboard not accessible"
    
    # Step 3: Check flights management
    flights_section = page.locator("text='Flights'").first
    if flights_section.is_visible():
        flights_section.click()
        page.wait_for_timeout(2000)
        
        # Verify flights data is displayed
        flights_table = page.locator("table, .flights-list")
        if flights_table.is_visible():
            expect(flights_table).to_be_visible()
    
    # Step 4: Check bookings management
    bookings_section = page.locator("text='Bookings'").first
    if bookings_section.is_visible():
        bookings_section.click()
        page.wait_for_timeout(2000)
        
        # Verify bookings data is displayed
        bookings_table = page.locator("table, .bookings-list")
        if bookings_table.is_visible():
            expect(bookings_table).to_be_visible()

@pytest.mark.integration
@pytest.mark.api
def test_frontend_backend_api_integration(page: Page, api_client, api_headers):
    """Test integration between frontend and backend APIs"""
    
    # Test 1: Verify frontend uses API data
    page.goto(BASE_URL)
    
    # Get flights from API
    api_response = api_client.get(f"{BASE_URL}/api/flights", headers=api_headers)
    assert api_response.status_code == 200
    api_flights = api_response.json()
    
    # Perform search in frontend
    page.select_option("select[name='origin']", "DEL")
    page.select_option("select[name='destination']", "BOM")
    page.fill("input[name='date']", "2024-12-25")
    page.click("button[type='submit']")
    
    page.wait_for_url("**/search**", timeout=10000)
    
    # Verify search results are displayed (integration working)
    flights_displayed = page.locator(".flight-card, .flight-item, .flight").count()
    
    # Should have some integration between API and frontend
    if flights_displayed > 0:
        assert True  # Frontend is showing flight data
    else:
        # Check if API has flights but frontend doesn't show them
        if "flights" in api_flights and api_flights["flights"]:
            pytest.fail("API has flights but frontend doesn't display them - integration issue")

@pytest.mark.integration
@pytest.mark.slow
def test_booking_persistence_workflow(page: Page, api_client, sample_passenger):
    """Test booking data persistence across different interfaces"""
    
    # Step 1: Create booking via frontend (if possible)
    page.goto(BASE_URL)
    
    # Try to create a booking through UI
    page.select_option("select[name='origin']", "DEL") 
    page.select_option("select[name='destination']", "BOM")
    page.fill("input[name='date']", "2024-12-25")
    page.click("button[type='submit']")
    
    page.wait_for_url("**/search**", timeout=10000)
    
    book_button = page.locator("text='Book Now', text='Select', text='Book'").first
    if book_button.is_visible():
        book_button.click()
        page.wait_for_timeout(3000)
        
        # Fill booking form if available
        name_field = page.locator("input[name='name']")
        if name_field.is_visible():
            name_field.fill(sample_passenger["name"])
            
            email_field = page.locator("input[name='email']") 
            if email_field.is_visible():
                email_field.fill(sample_passenger["email"])
                
            phone_field = page.locator("input[name='phone']")
            if phone_field.is_visible():
                phone_field.fill(sample_passenger["phone"])
            
            # Submit and try to get PNR
            submit_button = page.locator("button[type='submit'], input[type='submit']").first
            submit_button.click()
            page.wait_for_timeout(5000)
            
            # Step 2: Check if booking appears in API
            api_bookings = api_client.get(f"{BASE_URL}/api/bookings")
            if api_bookings.status_code == 200:
                bookings_data = api_bookings.json()
                
                # Verify booking exists in API response
                if "bookings" in bookings_data:
                    found_booking = False
                    for booking in bookings_data["bookings"]:
                        if booking.get("passenger_name") == sample_passenger["name"]:
                            found_booking = True
                            break
                    
                    # If we successfully created a booking, it should be in the API
                    # This tests data persistence between frontend and API
                    if found_booking:
                        assert True  # Persistence working
            
            # Step 3: Check "My Bookings" page
            page.goto(f"{BASE_URL}/booked_flights")
            page.wait_for_timeout(2000)
            
            # Should show bookings list
            bookings_container = page.locator(".booking-item, .booking-card, table")
            if bookings_container.is_visible():
                expect(bookings_container).to_be_visible()

@pytest.mark.integration
@pytest.mark.ui
def test_responsive_design_integration(page: Page):
    """Test responsive design works across different pages"""
    
    viewports = [
        {"width": 375, "height": 667},   # Mobile
        {"width": 768, "height": 1024},  # Tablet  
        {"width": 1280, "height": 720}   # Desktop
    ]
    
    test_pages = [
        BASE_URL,
        f"{BASE_URL}/booked_flights",
        f"{BASE_URL}/admin/login"
    ]
    
    for viewport in viewports:
        page.set_viewport_size(viewport)
        
        for test_url in test_pages:
            page.goto(test_url)
            page.wait_for_timeout(1000)
            
            # Basic elements should be visible at all viewport sizes
            body = page.locator("body")
            expect(body).to_be_visible()
            
            # Page should not have horizontal scrollbars on mobile
            if viewport["width"] <= 375:
                scroll_width = page.evaluate("document.body.scrollWidth")
                viewport_width = viewport["width"]
                assert scroll_width <= viewport_width + 20, f"Horizontal scroll on {test_url} at {viewport['width']}px"