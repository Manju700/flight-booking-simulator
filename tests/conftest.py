"""
Pytest Configuration and Fixtures for Flight Reservation System Tests
"""

import pytest
import os
import sys
import time
import subprocess
import requests
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, Page
from faker import Faker
import json

# Add the flight_reservation_system directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'flight_reservation_system'))

from playwright.config import (
    BASE_URL, BROWSERS, get_browser_config, get_context_config, 
    SCREENSHOTS_DIR, DOWNLOADS_DIR, TEST_TIMEOUT
)

fake = Faker()

# ==================== Flask Application Fixtures ====================

@pytest.fixture(scope="session")
def flask_app():
    """Start Flask application for testing"""
    app_dir = os.path.join(os.path.dirname(__file__), '..', 'flight_reservation_system')
    
    # Start Flask app in background
    env = os.environ.copy()
    env['FLASK_ENV'] = 'testing'
    
    process = subprocess.Popen(
        [sys.executable, 'app.py'],
        cwd=app_dir,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    # Wait for app to start
    for _ in range(30):
        try:
            response = requests.get(BASE_URL, timeout=5)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            time.sleep(1)
    else:
        process.kill()
        pytest.fail("Flask app failed to start")
    
    yield process
    
    # Cleanup
    process.kill()
    process.wait()

# ==================== Playwright Fixtures ====================

@pytest.fixture(scope="session")
def playwright():
    """Playwright instance for all tests"""
    with sync_playwright() as p:
        yield p

@pytest.fixture(scope="session", params=BROWSERS)
def browser_type(playwright, request):
    """Browser type fixture (parameterized for cross-browser testing)"""
    browser_name = request.param
    return getattr(playwright, browser_name)

@pytest.fixture(scope="function")
def browser(browser_type):
    """Browser instance for each test"""
    browser = browser_type.launch(**get_browser_config())
    yield browser
    browser.close()

@pytest.fixture(scope="function")
def context(browser):
    """Browser context for each test"""
    context = browser.new_context(**get_context_config())
    context.set_default_timeout(TEST_TIMEOUT)
    yield context
    context.close()

@pytest.fixture(scope="function")
def page(context, flask_app):
    """Page instance for each test"""
    page = context.new_page()
    page.goto(BASE_URL)
    yield page
    
    # Take screenshot on failure
    if hasattr(pytest, 'current_test_failed') and pytest.current_test_failed:
        screenshot_path = os.path.join(SCREENSHOTS_DIR, f"failure_{int(time.time())}.png")
        page.screenshot(path=screenshot_path)

# ==================== Test Data Fixtures ====================

@pytest.fixture
def sample_passenger():
    """Generate sample passenger data"""
    return {
        "name": fake.name(),
        "email": fake.email(),
        "phone": fake.phone_number()[:15],  # Limit phone number length
        "age": fake.random_int(min=18, max=80)
    }

@pytest.fixture
def sample_flight_search():
    """Generate sample flight search data"""
    return {
        "origin": fake.random_element(elements=["DEL", "BOM", "BLR", "MAA", "CCU", "HYD"]),
        "destination": fake.random_element(elements=["DEL", "BOM", "BLR", "MAA", "CCU", "HYD"]),
        "date": fake.date_between(start_date="today", end_date="+30d").strftime("%Y-%m-%d")
    }

@pytest.fixture
def admin_credentials():
    """Admin login credentials"""
    return {
        "password": os.environ.get("FRS_ADMIN_PASS", "admin123")
    }

# ==================== API Testing Fixtures ====================

@pytest.fixture
def api_client():
    """HTTP client for API testing"""
    return requests.Session()

@pytest.fixture
def api_headers():
    """Common API headers"""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

# ==================== Utility Functions ====================

def wait_for_element(page, selector, timeout=10000):
    """Wait for element to be visible"""
    page.wait_for_selector(selector, timeout=timeout)

def take_screenshot(page, name):
    """Take screenshot with timestamp"""
    timestamp = int(time.time())
    screenshot_path = os.path.join(SCREENSHOTS_DIR, f"{name}_{timestamp}.png")
    page.screenshot(path=screenshot_path)
    return screenshot_path

# ==================== Pytest Hooks ====================

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to capture test failures for screenshot taking"""
    outcome = yield
    rep = outcome.get_result()
    
    if rep.when == "call" and rep.failed:
        pytest.current_test_failed = True
    else:
        pytest.current_test_failed = False