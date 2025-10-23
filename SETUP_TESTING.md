# Flight Reservation System - Testing Setup Guide

## Quick Setup Instructions

### 1. Install Testing Dependencies

```bash
# Install all test dependencies
pip install -r requirements-test.txt

# Install Playwright browsers (required for UI tests)
python -m playwright install
```

### 2. Verify Installation

```bash
# Check pytest installation
python -m pytest --version

# Check Playwright installation  
python -c "from playwright.sync_api import sync_playwright; print('Playwright ready')"

# List available browsers
python -m playwright install --help
```

### 3. Run Tests

#### Quick Start
```bash
# Run all tests (installs dependencies automatically)
python run_tests.py --install-deps

# Run smoke tests only (fastest)
python run_tests.py --type smoke
```

#### Specific Test Categories
```bash
# UI Tests (frontend validation)
python run_tests.py --type ui

# API Tests (backend validation)  
python run_tests.py --type api

# Integration Tests (end-to-end workflows)
python run_tests.py --type integration

# Admin Tests (admin dashboard)
python run_tests.py --type admin

# Receipt Tests (PDF/JSON generation)
python run_tests.py --type receipts
```

#### Browser Selection
```bash
# Test with different browsers
python run_tests.py --type ui --browser chromium
python run_tests.py --type ui --browser firefox
python run_tests.py --type ui --browser webkit
```

#### Development Mode
```bash
# Run with visible browser (for debugging)
python run_tests.py --type ui --headed

# Verbose output for detailed logging
python run_tests.py --type all --verbose
```

### 4. Windows Users

Use the batch file for easier execution:

```cmd
REM Quick test run
run_tests.bat

REM Specific configurations
run_tests.bat --type smoke --browser chromium
run_tests.bat --type integration --headed --verbose
```

## Test Reports

After running tests, reports are generated in:
- **HTML Report**: `tests/reports/report.html`
- **Coverage Report**: `tests/reports/coverage/index.html`
- **Screenshots**: `tests/screenshots/` (for failures)

## Troubleshooting

### Common Issues

**1. Playwright Installation Issues**
```bash
# Force reinstall browsers
python -m playwright install --force

# Check system requirements
python -m playwright install-deps
```

**2. Flask App Won't Start**
```bash
# Check if port 5000 is in use
netstat -an | findstr :5000

# Install Flask dependencies
cd flight_reservation_system
pip install -r requirements.txt
```

**3. Permission Errors (Windows)**
```cmd
REM Run as administrator
run_tests.bat --type smoke
```

**4. Python Path Issues**
```bash
# Verify Python version (requires 3.8+)
python --version

# Check if modules are installed
python -m pip list | findstr pytest
python -m pip list | findstr playwright
```

### Test Configuration

Environment variables (optional):
```bash
set BASE_URL=http://localhost:5000
set HEADLESS=true
set FRS_ADMIN_PASS=admin123
```

### Manual Test Execution

If the test runner has issues, run pytest directly:

```bash
# Install dependencies manually
pip install pytest>=7.4.0 playwright>=1.40.0 requests>=2.31.0

# Install browsers
python -m playwright install

# Run specific tests
python -m pytest tests/test_api_endpoints.py -v
python -m pytest tests/ -m smoke
python -m pytest tests/ --html=report.html
```

## Test Coverage

The testing framework validates:

### ✅ Frontend (UI Tests)
- Homepage loading and navigation
- Flight search functionality
- Booking workflow (multi-step)
- Admin dashboard interface
- Responsive design validation
- Form validation and error handling

### ✅ Backend (API Tests)  
- All 16+ REST API endpoints
- JSON response format validation
- Error handling and status codes
- Data filtering and sorting
- CRUD operations validation

### ✅ Integration (E2E Tests)
- Complete booking workflows
- Receipt generation (PDF/JSON)
- Admin management operations
- Data persistence validation
- Cross-component integration

### ✅ System Validation
- Cross-browser compatibility
- Database transaction integrity
- Error handling and recovery
- Performance baseline validation

## Development Workflow

### Adding New Tests

1. **UI Tests**: Add to `tests/test_ui_*.py`
2. **API Tests**: Add to `tests/test_api_*.py`
3. **Integration**: Add to `tests/test_integration_*.py`

### Test Structure
```python
import pytest
from playwright.sync_api import Page

@pytest.mark.ui
@pytest.mark.smoke  # Use appropriate markers
def test_your_functionality(page: Page):
    """Test description"""
    # Test implementation
    page.goto("http://localhost:5000")
    # Assertions
    assert page.title() == "Expected Title"
```

### Running During Development
```bash
# Quick smoke test during development
python run_tests.py --type smoke

# Test specific functionality
python -m pytest tests/test_ui_homepage.py::test_homepage_loads -v

# Debug mode with visible browser
python run_tests.py --type ui --headed --verbose
```

## Production Deployment

Before deploying to production:

```bash
# Run full test suite
python run_tests.py --type all

# Generate coverage report
python -m pytest tests/ --cov=flight_reservation_system --cov-report=html

# Cross-browser validation
python run_tests.py --type ui --browser firefox
python run_tests.py --type ui --browser webkit
```

**Success Criteria**: All tests pass with >80% code coverage.

## CI/CD Integration

The testing framework is ready for CI/CD integration:

```yaml
# Example GitHub Actions workflow
- name: Install dependencies
  run: pip install -r requirements-test.txt

- name: Install Playwright browsers
  run: python -m playwright install

- name: Run tests
  run: python run_tests.py --type all

- name: Upload test results
  uses: actions/upload-artifact@v2
  with:
    name: test-results
    path: tests/reports/
```

## Support

For issues or questions:
1. Check this documentation
2. Review test logs in `tests/reports/`
3. Check screenshots in `tests/screenshots/` for UI failures
4. Verify Flask app starts correctly: `cd flight_reservation_system && python app.py`

The testing framework ensures the Flight Reservation System is **production-ready** with comprehensive validation of all components and user workflows.