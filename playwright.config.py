"""
Playwright Configuration for Flight Reservation System E2E Tests
"""

from playwright.sync_api import Playwright
import os

# Test configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
BROWSER_TIMEOUT = 30000  # 30 seconds
TEST_TIMEOUT = 120000   # 2 minutes per test

# Playwright browser configuration
BROWSERS = ["chromium", "firefox", "webkit"]
VIEWPORT = {"width": 1280, "height": 720}

# Test data paths
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "tests", "data")
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "tests", "screenshots")
DOWNLOADS_DIR = os.path.join(os.path.dirname(__file__), "tests", "downloads")

# Create directories if they don't exist
for directory in [TEST_DATA_DIR, SCREENSHOTS_DIR, DOWNLOADS_DIR]:
    os.makedirs(directory, exist_ok=True)

def get_browser_config():
    """Get browser configuration for Playwright"""
    return {
        "headless": HEADLESS,
        "args": [
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--disable-dev-shm-usage",
            "--no-sandbox"
        ]
    }

def get_context_config():
    """Get context configuration for Playwright"""
    return {
        "viewport": VIEWPORT,
        "record_video_dir": os.path.join("tests", "videos"),
        "record_video_size": VIEWPORT,
        "ignore_https_errors": True
    }