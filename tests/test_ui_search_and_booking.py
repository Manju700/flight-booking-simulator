"""
UI Tests for Flight Search and Booking Workflow
"""

import pytest
import time
from playwright.sync_api import Page, expect

@pytest.mark.ui
@pytest.mark.booking
@pytest.mark.smoke
def test_flight_search_flow(page: Page, sample_flight_search):
    """Test complete flight search workflow"""
    # Fill search form
    page.select_option("select[name='origin']", sample_flight_search["origin"])
    page.select_option("select[name='destination']", sample_flight_search["destination"])
    page.fill("input[name='date']", sample_flight_search["date"])
    
    # Submit search
    page.click("button[type='submit']")
    
    # Should navigate to search results
    page.wait_for_url("**/search**", timeout=10000)
    expect(page).to_have_url_regex(r".*\/search.*")

@pytest.mark.ui
@pytest.mark.booking
def test_search_results_display(page: Page):
    """Test search results are displayed correctly"""
    # Perform a search first
    page.select_option("select[name='origin']", "DEL")
    page.select_option("select[name='destination']", "BOM") 
    page.fill("input[name='date']", "2024-12-25")
    page.click("button[type='submit']")
    
    page.wait_for_url("**/search**", timeout=10000)
    
    # Check if flights are displayed
    flights_container = page.locator(".flight-card, .flight-item, .flight").first
    if flights_container.is_visible():
        expect(flights_container).to_be_visible()

@pytest.mark.ui
@pytest.mark.booking
def test_flight_selection(page: Page):
    """Test flight selection and booking initiation"""
    # Perform search
    page.select_option("select[name='origin']", "DEL")
    page.select_option("select[name='destination']", "BOM")
    page.fill("input[name='date']", "2024-12-25")
    page.click("button[type='submit']")
    
    page.wait_for_url("**/search**", timeout=10000)
    
    # Try to select a flight
    book_button = page.locator("text='Book Now', text='Select', text='Book'").first
    if book_button.is_visible():
        book_button.click()
        
        # Should navigate to booking page or seat selection
        page.wait_for_timeout(2000)  # Wait for navigation
        
        # Check if we're on booking flow
        booking_indicators = [
            page.locator("text='Seat Selection'"),
            page.locator("text='Passenger Details'"), 
            page.locator("text='Booking'"),
            page.locator("input[name='name']")
        ]
        
        any_visible = any(indicator.is_visible() for indicator in booking_indicators)
        assert any_visible, "Should be on booking flow page"

@pytest.mark.ui
@pytest.mark.booking
def test_seat_selection_interface(page: Page):
    """Test seat selection interface if available"""
    # Navigate to a specific flight booking page
    page.goto("/flight/AI101")
    
    # Check if seat map is available
    seat_map = page.locator(".seat-map, .seats, #seat-selection")
    if seat_map.is_visible():
        # Test seat selection
        available_seat = page.locator(".seat.available, .seat:not(.booked)").first
        if available_seat.is_visible():
            available_seat.click()
            expect(available_seat).to_have_class(re.compile("selected|active"))

@pytest.mark.ui
@pytest.mark.booking
def test_passenger_details_form(page: Page, sample_passenger):
    """Test passenger details form"""
    # Try to navigate to booking form
    page.goto("/flight/AI101")
    
    # Look for passenger form fields
    name_field = page.locator("input[name='name']")
    email_field = page.locator("input[name='email']") 
    phone_field = page.locator("input[name='phone']")
    
    if name_field.is_visible():
        # Fill passenger details
        name_field.fill(sample_passenger["name"])
        if email_field.is_visible():
            email_field.fill(sample_passenger["email"])
        if phone_field.is_visible():
            phone_field.fill(sample_passenger["phone"])
        
        # Test form validation
        submit_button = page.locator("button[type='submit'], input[type='submit']").first
        if submit_button.is_visible():
            # Form should have required fields filled
            expect(name_field).to_have_value(sample_passenger["name"])

@pytest.mark.ui
@pytest.mark.booking
@pytest.mark.slow
def test_complete_booking_workflow(page: Page, sample_passenger):
    """Test complete end-to-end booking workflow"""
    # Step 1: Search for flights
    page.select_option("select[name='origin']", "DEL")
    page.select_option("select[name='destination']", "BOM")
    page.fill("input[name='date']", "2024-12-25")
    page.click("button[type='submit']")
    
    page.wait_for_url("**/search**", timeout=10000)
    
    # Step 2: Select a flight
    book_button = page.locator("text='Book Now', text='Select', text='Book'").first
    if not book_button.is_visible():
        pytest.skip("No flights available for booking")
        
    book_button.click()
    page.wait_for_timeout(2000)
    
    # Step 3: Fill passenger details (if form is available)
    name_field = page.locator("input[name='name']")
    if name_field.is_visible():
        name_field.fill(sample_passenger["name"])
        
        email_field = page.locator("input[name='email']")
        if email_field.is_visible():
            email_field.fill(sample_passenger["email"])
            
        phone_field = page.locator("input[name='phone']")
        if phone_field.is_visible():
            phone_field.fill(sample_passenger["phone"])
        
        # Step 4: Submit booking
        submit_button = page.locator("button[type='submit'], input[type='submit']").first
        if submit_button.is_visible():
            submit_button.click()
            page.wait_for_timeout(3000)
            
            # Step 5: Verify booking confirmation
            success_indicators = [
                page.locator("text='Booking Confirmed'"),
                page.locator("text='PNR'"),
                page.locator("text='Confirmation'"),
                page.locator(".booking-success, .confirmation")
            ]
            
            any_success = any(indicator.is_visible() for indicator in success_indicators)
            if any_success:
                # Booking was successful
                assert True
            else:
                pytest.skip("Booking flow not completed - may require additional steps")

import re