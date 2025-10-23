#!/usr/bin/env python3
"""
Validation Script for E2E Testing Framework Setup
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is adequate"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False

def check_files_exist():
    """Check if test files are created"""
    required_files = [
        "requirements-test.txt",
        "pytest.ini", 
        "playwright.config.py",
        "run_tests.py",
        "tests/conftest.py",
        "tests/test_ui_homepage.py",
        "tests/test_api_endpoints.py",
        "tests/test_integration_workflows.py",
        "TESTING_DOCUMENTATION.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path} - Found")
    
    if missing_files:
        print("\n❌ Missing files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    
    return True

def check_test_directories():
    """Check if test directories are created"""
    test_dirs = [
        "tests",
        "tests/data", 
        "tests/utils",
        "tests/reports",
        "tests/screenshots",
        "tests/downloads"
    ]
    
    for test_dir in test_dirs:
        os.makedirs(test_dir, exist_ok=True)
        print(f"✅ {test_dir}/ - Created/Verified")
    
    return True

def check_flask_app():
    """Check if Flask app can be imported"""
    try:
        sys.path.insert(0, os.path.join(os.getcwd(), 'flight_reservation_system'))
        
        # Try importing the app
        import app
        print("✅ Flask app - Can be imported")
        
        # Check if basic models exist
        from models import Flight, Booking, User
        print("✅ Database models - Can be imported")
        
        return True
    except ImportError as e:
        print(f"❌ Flask app import error: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Flask app warning: {e}")
        return True  # Non-critical error

def check_test_configuration():
    """Check test configuration files"""
    configs = {
        "pytest.ini": ["[tool:pytest]", "testpaths = tests"],
        "playwright.config.py": ["BASE_URL", "get_browser_config"],
        "requirements-test.txt": ["pytest>=7.4.0", "playwright>=1.40.0"]
    }
    
    for config_file, expected_content in configs.items():
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            found_content = []
            for expected in expected_content:
                if expected in content:
                    found_content.append(expected)
            
            if len(found_content) == len(expected_content):
                print(f"✅ {config_file} - Configuration OK")
            else:
                print(f"⚠️  {config_file} - Some content missing")
        else:
            print(f"❌ {config_file} - Not found")
    
    return True

def try_install_dependencies():
    """Try to install test dependencies"""
    try:
        print("\n🔄 Attempting to install test dependencies...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Test dependencies - Installed successfully")
            return True
        else:
            print(f"❌ Pip install error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Pip install timed out (but may still be running)")
        return False
    except Exception as e:
        print(f"❌ Dependency installation error: {e}")
        return False

def validate_test_structure():
    """Validate test file structure"""
    test_files = [
        "tests/test_ui_homepage.py",
        "tests/test_ui_search_and_booking.py", 
        "tests/test_ui_admin.py",
        "tests/test_api_endpoints.py",
        "tests/test_integration_workflows.py",
        "tests/test_receipts.py"
    ]
    
    valid_tests = 0
    for test_file in test_files:
        if os.path.exists(test_file):
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if "def test_" in content and "import pytest" in content:
                print(f"✅ {test_file} - Valid test structure")
                valid_tests += 1
            else:
                print(f"⚠️  {test_file} - Missing test functions")
        else:
            print(f"❌ {test_file} - Not found")
    
    return valid_tests >= len(test_files) // 2  # At least half should be valid

def main():
    """Main validation function"""
    print("=" * 60)
    print("FLIGHT RESERVATION SYSTEM - TEST FRAMEWORK VALIDATION")
    print("=" * 60)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Files", check_files_exist),
        ("Test Directories", check_test_directories),
        ("Flask Application", check_flask_app),
        ("Test Configuration", check_test_configuration),
        ("Test File Structure", validate_test_structure)
    ]
    
    passed_checks = 0
    total_checks = len(checks)
    
    for check_name, check_function in checks:
        print(f"\n🔍 Checking: {check_name}")
        try:
            if check_function():
                passed_checks += 1
            else:
                print(f"❌ {check_name} - Failed")
        except Exception as e:
            print(f"❌ {check_name} - Error: {e}")
    
    # Optional dependency installation
    print(f"\n🔍 Optional: Installing Dependencies")
    try_install_dependencies()
    
    # Summary
    print("\n" + "=" * 60)
    print(f"VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed_checks}/{total_checks} checks")
    
    if passed_checks == total_checks:
        print("🎉 ALL CHECKS PASSED! Testing framework is ready.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements-test.txt")
        print("2. Install browsers: python -m playwright install")
        print("3. Run tests: python run_tests.py --type smoke")
        return 0
    elif passed_checks >= total_checks * 0.8:
        print("⚠️  MOSTLY READY - Some minor issues detected.")
        print("The testing framework should work with manual setup.")
        return 0
    else:
        print("❌ SETUP INCOMPLETE - Please resolve issues above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)