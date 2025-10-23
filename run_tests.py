#!/usr/bin/env python3
"""
Test Runner for Flight Reservation System E2E Tests
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Add flight_reservation_system to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flight_reservation_system'))

def install_dependencies():
    """Install test dependencies"""
    print("Installing test dependencies...")
    
    # Install test requirements
    subprocess.run([
        sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"
    ], check=True)
    
    # Install Playwright browsers
    subprocess.run([
        sys.executable, "-m", "playwright", "install"
    ], check=True)
    
    print("Dependencies installed successfully!")

def run_tests(test_type="all", browser="chromium", headless=True, verbose=False):
    """Run the test suite"""
    
    # Base pytest command
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add test markers based on test type
    if test_type == "smoke":
        cmd.extend(["-m", "smoke"])
    elif test_type == "ui":
        cmd.extend(["-m", "ui"])
    elif test_type == "api":
        cmd.extend(["-m", "api"]) 
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "admin":
        cmd.extend(["-m", "admin"])
    elif test_type == "booking":
        cmd.extend(["-m", "booking"])
    elif test_type == "receipts":
        cmd.extend(["-m", "receipts"])
    
    # Add browser selection (for UI tests)
    if test_type in ["ui", "integration", "all"]:
        os.environ["PLAYWRIGHT_BROWSER"] = browser
    
    # Add headless mode
    os.environ["HEADLESS"] = "true" if headless else "false"
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    
    # Add test directory
    cmd.append("tests/")
    
    print(f"Running tests: {' '.join(cmd)}")
    print(f"Browser: {browser}, Headless: {headless}")
    
    # Run tests
    result = subprocess.run(cmd)
    return result.returncode

def generate_reports():
    """Generate test reports"""
    print("\nGenerating test reports...")
    
    reports_dir = Path("tests/reports")
    reports_dir.mkdir(exist_ok=True)
    
    # The reports are generated automatically by pytest configuration
    html_report = reports_dir / "report.html"
    coverage_report = reports_dir / "coverage" / "index.html"
    
    print(f"Test reports generated:")
    if html_report.exists():
        print(f"  - HTML Report: {html_report.absolute()}")
    if coverage_report.exists():
        print(f"  - Coverage Report: {coverage_report.absolute()}")

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Flight Reservation System Test Runner")
    
    parser.add_argument(
        "--type", 
        choices=["all", "smoke", "ui", "api", "integration", "admin", "booking", "receipts"],
        default="all",
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "--browser",
        choices=["chromium", "firefox", "webkit"],
        default="chromium", 
        help="Browser for UI tests"
    )
    
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run browser tests in headed mode (visible)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install test dependencies before running"
    )
    
    args = parser.parse_args()
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    try:
        # Install dependencies if requested
        if args.install_deps:
            install_dependencies()
        
        # Run tests
        print(f"\n{'='*60}")
        print(f"FLIGHT RESERVATION SYSTEM - E2E TEST SUITE")
        print(f"{'='*60}")
        print(f"Test Type: {args.type.upper()}")
        print(f"Browser: {args.browser}")
        print(f"Mode: {'Headed' if args.headed else 'Headless'}")
        print(f"{'='*60}")
        
        exit_code = run_tests(
            test_type=args.type,
            browser=args.browser, 
            headless=not args.headed,
            verbose=args.verbose
        )
        
        # Generate reports
        generate_reports()
        
        # Print summary
        print(f"\n{'='*60}")
        if exit_code == 0:
            print("✅ ALL TESTS PASSED!")
        else:
            print("❌ SOME TESTS FAILED!")
        print(f"{'='*60}")
        
        return exit_code
        
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)