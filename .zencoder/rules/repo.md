# Flight Reservation System - Repository Rules

## Project Information
- **Type**: Flask Web Application with REST API
- **Language**: Python 3.8+
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: SQLite (development)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Testing**: Playwright (E2E), pytest (Test Framework)

## Target Framework
- **targetFramework**: Playwright

## Project Structure
```
flight_reservation_system/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── requirements.txt       # Production dependencies
├── templates/            # Jinja2 HTML templates
├── static/              # CSS, JS, assets
└── instance/            # SQLite database

tests/                   # E2E Testing Framework
├── test_ui_*.py        # UI/Frontend tests
├── test_api_*.py       # API endpoint tests
├── test_integration_*.py # Integration tests
├── conftest.py         # Test fixtures
├── data/               # Test data files
└── utils/              # Test utilities

requirements-test.txt    # Testing dependencies
run_tests.py            # Test runner script
pytest.ini              # Test configuration
playwright.config.py    # Browser configuration
```

## Development Guidelines

### Testing Standards
- All new features require E2E tests
- UI changes need cross-browser validation
- API endpoints require comprehensive testing
- Integration tests for complete workflows
- Minimum 80% code coverage required

### Code Standards
- Follow PEP 8 Python style guide
- Use descriptive function and variable names
- Add docstrings to all functions
- Handle errors gracefully with proper logging
- Validate all user inputs

### Database Operations
- Use SQLAlchemy ORM for all database operations
- Implement proper transaction handling
- Add database migration support for schema changes
- Ensure data integrity with foreign key constraints

### API Design
- Follow RESTful conventions
- Return consistent JSON response format
- Implement proper HTTP status codes
- Add comprehensive error handling
- Support filtering, sorting, and pagination

### Frontend Requirements
- Maintain responsive design across all screen sizes
- Ensure cross-browser compatibility (Chrome, Firefox, Safari)
- Implement proper form validation
- Use semantic HTML5 elements
- Follow accessibility guidelines (WCAG 2.1)

## Testing Commands

### Quick Test Execution
```bash
# Run all tests
python run_tests.py

# Run smoke tests only
python run_tests.py --type smoke

# Run UI tests in visible browser
python run_tests.py --type ui --headed

# Install dependencies and run tests
python run_tests.py --install-deps --type all
```

### Advanced Test Options
```bash
# Cross-browser testing
python run_tests.py --type ui --browser firefox
python run_tests.py --type ui --browser webkit

# Specific test categories
python run_tests.py --type api          # API tests only
python run_tests.py --type integration  # Integration tests only
python run_tests.py --type admin       # Admin functionality
python run_tests.py --type receipts    # Receipt generation
```

## Deployment Considerations
- Ensure all environment variables are documented
- Include database initialization scripts
- Provide clear installation and setup instructions
- Test deployment in production-like environment
- Implement proper logging and monitoring

## Security Requirements
- Validate and sanitize all user inputs
- Use parameterized queries to prevent SQL injection
- Implement proper session management
- Secure admin access with strong authentication
- Add CSRF protection for forms
- Use HTTPS in production environment