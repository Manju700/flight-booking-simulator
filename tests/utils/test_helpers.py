"""
Test Utility Functions and Helpers
"""

import json
import os
import time
import random
import string
from typing import Dict, List, Any, Optional
from playwright.sync_api import Page, Locator

# ==================== Data Helpers ====================

def load_test_data(filename: str = "test_data.json") -> Dict[str, Any]:
    """Load test data from JSON file"""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    file_path = os.path.join(data_dir, filename)
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {}

def generate_random_passenger() -> Dict[str, str]:
    """Generate random passenger data for testing"""
    first_names = ["John", "Jane", "Mike", "Sarah", "David", "Lisa", "Tom", "Emma"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller"]
    
    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    email = f"{name.lower().replace(' ', '.')}@testmail.com"
    phone = f"+91-{''.join(random.choices(string.digits, k=10))}"
    
    return {
        "name": name,
        "email": email, 
        "phone": phone,
        "age": random.randint(18, 65)
    }

def generate_pnr() -> str:
    """Generate random PNR for testing"""
    return f"TEST-{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

# ==================== Page Helpers ====================

def wait_for_page_load(page: Page, timeout: int = 10000) -> None:
    """Wait for page to fully load"""
    page.wait_for_load_state("networkidle", timeout=timeout)

def safe_click(page: Page, selector: str, timeout: int = 5000) -> bool:
    """Safely click element if it exists and is visible"""
    try:
        element = page.locator(selector)
        if element.is_visible(timeout=timeout):
            element.click()
            return True
    except Exception:
        pass
    return False

def safe_fill(page: Page, selector: str, value: str, timeout: int = 5000) -> bool:
    """Safely fill input if it exists and is visible"""
    try:
        element = page.locator(selector)
        if element.is_visible(timeout=timeout):
            element.fill(value)
            return True
    except Exception:
        pass
    return False

def safe_select(page: Page, selector: str, value: str, timeout: int = 5000) -> bool:
    """Safely select option if element exists"""
    try:
        element = page.locator(selector)
        if element.is_visible(timeout=timeout):
            element.select_option(value)
            return True
    except Exception:
        pass
    return False

def take_screenshot_on_error(page: Page, test_name: str) -> str:
    """Take screenshot on test failure"""
    timestamp = int(time.time())
    screenshot_dir = os.path.join(os.path.dirname(__file__), '..', 'screenshots')
    os.makedirs(screenshot_dir, exist_ok=True)
    
    screenshot_path = os.path.join(screenshot_dir, f"{test_name}_error_{timestamp}.png")
    page.screenshot(path=screenshot_path, full_page=True)
    
    return screenshot_path

# ==================== Form Helpers ====================

def fill_search_form(page: Page, origin: str, destination: str, date: str) -> bool:
    """Fill flight search form"""
    try:
        page.select_option("select[name='origin']", origin)
        page.select_option("select[name='destination']", destination)
        page.fill("input[name='date']", date)
        return True
    except Exception:
        return False

def fill_passenger_form(page: Page, passenger_data: Dict[str, str]) -> bool:
    """Fill passenger details form"""
    try:
        fields_filled = 0
        
        if safe_fill(page, "input[name='name'], input[name='passenger_name']", passenger_data["name"]):
            fields_filled += 1
            
        if safe_fill(page, "input[name='email'], input[name='passenger_email']", passenger_data["email"]):
            fields_filled += 1
            
        if safe_fill(page, "input[name='phone'], input[name='passenger_phone']", passenger_data["phone"]):
            fields_filled += 1
            
        return fields_filled > 0
    except Exception:
        return False

# ==================== API Helpers ====================

def validate_api_response(response_data: Dict[str, Any], required_fields: List[str]) -> bool:
    """Validate API response has required fields"""
    if not isinstance(response_data, dict):
        return False
        
    for field in required_fields:
        if field not in response_data:
            return False
            
    return True

def extract_pnr_from_response(response_data: Dict[str, Any]) -> Optional[str]:
    """Extract PNR from API response"""
    possible_pnr_fields = ["pnr", "booking_reference", "confirmation_number", "id"]
    
    for field in possible_pnr_fields:
        if field in response_data:
            return response_data[field]
            
    # Check nested structures
    if "booking" in response_data:
        booking = response_data["booking"]
        for field in possible_pnr_fields:
            if field in booking:
                return booking[field]
                
    return None

# ==================== Wait Helpers ====================

def wait_for_booking_confirmation(page: Page, timeout: int = 15000) -> bool:
    """Wait for booking confirmation page/message"""
    confirmation_selectors = [
        "text='Booking Confirmed'",
        "text='Confirmation'",
        "text='Thank you'",
        "text='PNR'",
        ".booking-success",
        ".confirmation",
        ".success-message"
    ]
    
    for selector in confirmation_selectors:
        try:
            page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            continue
            
    return False

def wait_for_element_or_timeout(page: Page, selector: str, timeout: int = 5000) -> bool:
    """Wait for element or return False on timeout"""
    try:
        page.wait_for_selector(selector, timeout=timeout)
        return True
    except Exception:
        return False

# ==================== Validation Helpers ====================

def is_valid_pnr(pnr: str) -> bool:
    """Check if PNR format is valid"""
    if not pnr or not isinstance(pnr, str):
        return False
        
    # Basic PNR validation - should be alphanumeric with possible dash/underscore
    return len(pnr.replace("-", "").replace("_", "")) >= 4

def is_valid_email(email: str) -> bool:
    """Basic email validation"""
    return "@" in email and "." in email.split("@")[1]

def is_valid_phone(phone: str) -> bool:
    """Basic phone validation"""
    digits = ''.join(filter(str.isdigit, phone))
    return len(digits) >= 10

# ==================== Browser Helpers ====================

def get_page_title(page: Page) -> str:
    """Get page title safely"""
    try:
        return page.title()
    except Exception:
        return ""

def get_current_url(page: Page) -> str:
    """Get current URL safely"""
    try:
        return page.url
    except Exception:
        return ""

def check_for_errors_on_page(page: Page) -> List[str]:
    """Check for common error indicators on page"""
    error_selectors = [
        ".error",
        ".alert-error",
        ".alert-danger",
        "text='Error'",
        "text='Failed'",
        "text='Invalid'"
    ]
    
    errors = []
    for selector in error_selectors:
        try:
            elements = page.locator(selector)
            if elements.count() > 0:
                for i in range(elements.count()):
                    error_text = elements.nth(i).text_content()
                    if error_text:
                        errors.append(error_text)
        except Exception:
            continue
            
    return errors

# ==================== Debug Helpers ====================

def debug_page_state(page: Page) -> Dict[str, Any]:
    """Get debug information about current page state"""
    return {
        "url": get_current_url(page),
        "title": get_page_title(page),
        "errors": check_for_errors_on_page(page),
        "timestamp": time.time()
    }

def log_test_step(step_name: str, details: str = "") -> None:
    """Log test step for debugging"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {step_name}: {details}")