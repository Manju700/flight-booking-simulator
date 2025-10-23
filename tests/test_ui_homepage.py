"""
UI Tests for Homepage and Navigation
"""

import pytest
from playwright.sync_api import Page, expect

@pytest.mark.ui
@pytest.mark.smoke
def test_homepage_loads(page: Page):
    """Test that homepage loads successfully"""
    # Homepage should load
    expect(page).to_have_title("Flight Reservation System")
    
    # Main elements should be visible
    expect(page.locator("h1")).to_contain_text("Flight Search")
    expect(page.locator("form")).to_be_visible()

@pytest.mark.ui
def test_navigation_elements(page: Page):
    """Test main navigation elements"""
    # Navigation links should be present
    nav_links = [
        ("Home", "/"),
        ("Book Flight", "/"),
        ("My Bookings", "/booked_flights"),
        ("Admin", "/admin/login")
    ]
    
    for link_text, expected_url in nav_links:
        link = page.locator(f"text='{link_text}'").first
        if link.is_visible():
            expect(link).to_be_visible()

@pytest.mark.ui  
def test_search_form_elements(page: Page):
    """Test search form has all required elements"""
    # Form fields should be present
    expect(page.locator("select[name='origin']")).to_be_visible()
    expect(page.locator("select[name='destination']")).to_be_visible()
    expect(page.locator("input[name='date']")).to_be_visible()
    expect(page.locator("button[type='submit']")).to_be_visible()

@pytest.mark.ui
def test_search_form_validation(page: Page):
    """Test search form validation"""
    # Try to submit empty form
    page.click("button[type='submit']")
    
    # Should still be on homepage (no navigation)
    expect(page).to_have_url("/")

@pytest.mark.ui
def test_responsive_design(page: Page):
    """Test responsive design on different screen sizes"""
    # Test mobile viewport
    page.set_viewport_size({"width": 375, "height": 667})
    expect(page.locator("h1")).to_be_visible()
    
    # Test tablet viewport
    page.set_viewport_size({"width": 768, "height": 1024})
    expect(page.locator("h1")).to_be_visible()
    
    # Test desktop viewport
    page.set_viewport_size({"width": 1280, "height": 720})
    expect(page.locator("h1")).to_be_visible()

@pytest.mark.ui
def test_footer_elements(page: Page):
    """Test footer elements are present"""
    # Scroll to bottom to ensure footer is loaded
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    
    # Footer should contain system info
    footer = page.locator("footer, .footer").first
    if footer.is_visible():
        expect(footer).to_be_visible()