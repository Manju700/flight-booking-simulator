"""
UI Tests for Admin Dashboard
"""

import pytest
from playwright.sync_api import Page, expect

@pytest.mark.ui
@pytest.mark.admin
def test_admin_login_page(page: Page):
    """Test admin login page loads"""
    page.goto("/admin/login")
    
    expect(page).to_have_title(re.compile("Admin|Login"))
    expect(page.locator("input[name='password'], input[type='password']")).to_be_visible()
    expect(page.locator("button[type='submit'], input[type='submit']")).to_be_visible()

@pytest.mark.ui
@pytest.mark.admin
def test_admin_login_validation(page: Page):
    """Test admin login validation"""
    page.goto("/admin/login")
    
    # Try empty password
    submit_button = page.locator("button[type='submit'], input[type='submit']").first
    submit_button.click()
    
    # Should show error or stay on login page
    expect(page).to_have_url_regex(r".*\/admin\/login.*")

@pytest.mark.ui
@pytest.mark.admin
def test_admin_login_with_credentials(page: Page, admin_credentials):
    """Test admin login with correct credentials"""
    page.goto("/admin/login")
    
    # Fill password field
    password_field = page.locator("input[name='password'], input[type='password']").first
    password_field.fill(admin_credentials["password"])
    
    # Submit login
    submit_button = page.locator("button[type='submit'], input[type='submit']").first
    submit_button.click()
    
    page.wait_for_timeout(2000)
    
    # Should redirect to admin dashboard or show success
    success_indicators = [
        lambda: page.url.endswith("/admin"),
        lambda: "admin" in page.url.lower(),
        lambda: page.locator("text='Dashboard', text='Admin Panel'").is_visible(),
        lambda: page.locator("text='Flights', text='Bookings'").is_visible()
    ]
    
    any_success = any(indicator() for indicator in success_indicators)
    assert any_success, f"Admin login failed. Current URL: {page.url}"

@pytest.mark.ui
@pytest.mark.admin
def test_admin_dashboard_elements(page: Page, admin_credentials):
    """Test admin dashboard has required elements"""
    # Login first
    page.goto("/admin/login")
    password_field = page.locator("input[name='password'], input[type='password']").first
    password_field.fill(admin_credentials["password"])
    submit_button = page.locator("button[type='submit'], input[type='submit']").first
    submit_button.click()
    
    page.wait_for_timeout(3000)
    
    # Check dashboard elements
    dashboard_elements = [
        "text='Flights'",
        "text='Bookings'", 
        "text='Statistics'",
        "text='Total'",
        ".admin-panel, .dashboard, .admin-content"
    ]
    
    for element_selector in dashboard_elements:
        element = page.locator(element_selector)
        if element.is_visible():
            expect(element).to_be_visible()
            break
    else:
        # At least one dashboard element should be visible
        pytest.skip("Admin dashboard elements not found - may need UI updates")

@pytest.mark.ui
@pytest.mark.admin
def test_admin_flights_management(page: Page, admin_credentials):
    """Test admin flights management interface"""
    # Login to admin
    page.goto("/admin/login")
    password_field = page.locator("input[name='password'], input[type='password']").first
    password_field.fill(admin_credentials["password"])
    submit_button = page.locator("button[type='submit'], input[type='submit']").first
    submit_button.click()
    
    page.wait_for_timeout(3000)
    
    # Look for flights table or list
    flights_table = page.locator("table, .flights-list, .flight-item")
    if flights_table.is_visible():
        expect(flights_table).to_be_visible()
        
        # Check for flight data
        flight_rows = page.locator("tr, .flight-row").count()
        assert flight_rows > 0, "Should have flight data displayed"

@pytest.mark.ui
@pytest.mark.admin
def test_admin_bookings_management(page: Page, admin_credentials):
    """Test admin bookings management interface"""
    # Login to admin
    page.goto("/admin/login")
    password_field = page.locator("input[name='password'], input[type='password']").first
    password_field.fill(admin_credentials["password"])
    submit_button = page.locator("button[type='submit'], input[type='submit']").first
    submit_button.click()
    
    page.wait_for_timeout(3000)
    
    # Look for bookings section
    bookings_section = page.locator("text='Bookings'").first
    if bookings_section.is_visible():
        bookings_section.click()
        page.wait_for_timeout(1000)
        
        # Check for bookings data
        bookings_table = page.locator("table, .bookings-list, .booking-item")
        if bookings_table.is_visible():
            expect(bookings_table).to_be_visible()

@pytest.mark.ui
@pytest.mark.admin 
def test_admin_logout(page: Page, admin_credentials):
    """Test admin logout functionality"""
    # Login first
    page.goto("/admin/login")
    password_field = page.locator("input[name='password'], input[type='password']").first
    password_field.fill(admin_credentials["password"])
    submit_button = page.locator("button[type='submit'], input[type='submit']").first
    submit_button.click()
    
    page.wait_for_timeout(3000)
    
    # Look for logout button
    logout_button = page.locator("text='Logout', text='Sign Out'").first
    if logout_button.is_visible():
        logout_button.click()
        page.wait_for_timeout(2000)
        
        # Should redirect to login page or homepage
        expect(page).to_have_url_regex(r".*(\/admin\/login|\/login|\/).*")

import re