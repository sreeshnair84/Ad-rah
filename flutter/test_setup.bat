@echo off
REM Flutter App Test Script
REM Run this script to test your Flutter setup and app

echo Testing Flutter Digital Signage App Setup...

REM Change to Flutter project directory
set "SCRIPT_DIR=%~dp0"
set "PROJECT_PATH=%SCRIPT_DIR%adarah_digital_signage"

if not exist "%PROJECT_PATH%" (
    echo Error: Flutter project not found at %PROJECT_PATH%
    pause
    exit /b 1
)

cd /d "%PROJECT_PATH%"

REM Test 1: Flutter Doctor
echo.
echo 1. Running Flutter Doctor...
flutter doctor

REM Test 2: Flutter Pub Get
echo.
echo 2. Running Flutter Pub Get...
flutter pub get

REM Test 3: Flutter Analyze
echo.
echo 3. Running Flutter Analyze...
flutter analyze

REM Test 4: Check for compilation errors
echo.
echo 4. Testing App Compilation...
flutter build apk --debug > build_output.txt 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] App compiles successfully!
) else (
    echo [ERROR] Compilation failed:
    type build_output.txt
)
del build_output.txt

REM Test 5: List available devices/emulators
echo.
echo 5. Available Devices and Emulators:
flutter devices

REM Test 6: List available emulators
echo.
echo 6. Available Emulators:
flutter emulators

REM Test 7: Check project structure
echo.
echo 7. Project Structure Check:
set "REQUIRED_FILES=lib\main.dart lib\screens\setup_registration_screen.dart lib\screens\main_display_screen.dart lib\screens\interactive_screen.dart lib\screens\status_diagnostics_screen.dart lib\screens\error_offline_screen.dart pubspec.yaml README.md"

for %%f in (%REQUIRED_FILES%) do (
    if exist "%%f" (
        echo [OK] %%f - Found
    ) else (
        echo [ERROR] %%f - Missing
    )
)

REM Test 8: Check pubspec.yaml dependencies
echo.
echo 8. Checking Dependencies:
if exist "pubspec.yaml" (
    findstr /C:"flutter:" pubspec.yaml >nul
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Flutter dependency found
    ) else (
        echo [ERROR] Flutter dependency missing
    )

    findstr /C:"cupertino_icons:" pubspec.yaml >nul
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Cupertino icons dependency found
    ) else (
        echo [ERROR] Cupertino icons dependency missing
    )
) else (
    echo [ERROR] pubspec.yaml not found
)

echo.
echo ==================================================
echo Test Summary:
echo ==================================================

if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Setup looks good! You can now run the app.
    echo Try: flutter run
    echo Or: flutter emulators --launch Tablet_Kiosk && flutter run
) else (
    echo [WARNING] Some issues found. Please check the output above.
    echo Common fixes:
    echo 1. Run: flutter pub get
    echo 2. Run: flutter clean ^&^& flutter pub get
    echo 3. Check Android SDK setup
)

echo.
pause
