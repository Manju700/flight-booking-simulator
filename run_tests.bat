@echo off
REM Windows batch file to run Flight Reservation System tests

echo ========================================
echo Flight Reservation System Test Runner
echo ========================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "run_tests.py" (
    echo ERROR: run_tests.py not found. Please run from project root directory.
    pause
    exit /b 1
)

REM Parse command line arguments
set TEST_TYPE=all
set BROWSER=chromium
set HEADED=false
set VERBOSE=false
set INSTALL_DEPS=false

:parse_args
if "%1"=="" goto run_tests
if "%1"=="--type" (
    set TEST_TYPE=%2
    shift
    shift
    goto parse_args
)
if "%1"=="--browser" (
    set BROWSER=%2
    shift
    shift
    goto parse_args
)
if "%1"=="--headed" (
    set HEADED=true
    shift
    goto parse_args
)
if "%1"=="--verbose" (
    set VERBOSE=true
    shift
    goto parse_args
)
if "%1"=="--install-deps" (
    set INSTALL_DEPS=true
    shift
    goto parse_args
)
shift
goto parse_args

:run_tests
echo Test Configuration:
echo - Type: %TEST_TYPE%
echo - Browser: %BROWSER%
echo - Mode: %HEADED%
echo - Verbose: %VERBOSE%
echo ========================================

REM Build Python command
set PY_CMD=python run_tests.py --type %TEST_TYPE% --browser %BROWSER%

if "%HEADED%"=="true" (
    set PY_CMD=%PY_CMD% --headed
)

if "%VERBOSE%"=="true" (
    set PY_CMD=%PY_CMD% --verbose
)

if "%INSTALL_DEPS%"=="true" (
    set PY_CMD=%PY_CMD% --install-deps
)

REM Execute Python test runner
echo Running: %PY_CMD%
echo ========================================
%PY_CMD%

REM Check exit code
if errorlevel 1 (
    echo ========================================
    echo TESTS FAILED!
    echo ========================================
    pause
    exit /b 1
) else (
    echo ========================================
    echo ALL TESTS PASSED!
    echo ========================================
)

pause