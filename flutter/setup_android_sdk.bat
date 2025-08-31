@echo off
REM Android SDK Setup Script for Windows
REM Run this script with administrator privileges

echo Setting up Android SDK for Flutter development...

REM Define paths
set ANDROID_HOME=%USERPROFILE%\Android\Sdk
set ANDROID_SDK_ROOT=%ANDROID_HOME%
set CMD_TOOLS_PATH=%ANDROID_HOME%\cmdline-tools\latest

REM Create Android SDK directory
if not exist "%ANDROID_HOME%" (
    mkdir "%ANDROID_HOME%"
    echo Created Android SDK directory: %ANDROID_HOME%
)

REM Download Android SDK Command Line Tools
set CMD_TOOLS_URL=https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip
set CMD_TOOLS_ZIP=%TEMP%\cmdline-tools.zip

echo Downloading Android SDK Command Line Tools...
powershell -Command "Invoke-WebRequest -Uri '%CMD_TOOLS_URL%' -OutFile '%CMD_TOOLS_ZIP%'"

REM Extract to temporary location first
set EXTRACT_TEMP=%TEMP%\cmdline-tools-temp
if exist "%EXTRACT_TEMP%" rmdir /s /q "%EXTRACT_TEMP%"
mkdir "%EXTRACT_TEMP%"

echo Extracting Android SDK Command Line Tools...
powershell -Command "Expand-Archive -Path '%CMD_TOOLS_ZIP%' -DestinationPath '%EXTRACT_TEMP%'"

REM Move to correct location
if not exist "%CMD_TOOLS_PATH%" mkdir "%CMD_TOOLS_PATH%"
xcopy "%EXTRACT_TEMP%\cmdline-tools\*" "%CMD_TOOLS_PATH%\" /E /I /Y

REM Clean up
del "%CMD_TOOLS_ZIP%"
rmdir /s /q "%EXTRACT_TEMP%"

REM Set environment variables
echo Setting environment variables...

REM Add to PATH if not already there
echo ;%PATH%; | find /C /I ";%CMD_TOOLS_PATH%\bin;" >nul
if errorlevel 1 (
    setx PATH "%CMD_TOOLS_PATH%\bin;%PATH%" /M
    echo Added Android SDK to PATH
)

REM Set ANDROID_HOME and ANDROID_SDK_ROOT
setx ANDROID_HOME "%ANDROID_HOME%" /M
setx ANDROID_SDK_ROOT "%ANDROID_SDK_ROOT%" /M

echo Environment variables set:
echo ANDROID_HOME: %ANDROID_HOME%
echo ANDROID_SDK_ROOT: %ANDROID_SDK_ROOT%

REM Accept Android SDK licenses
echo Accepting Android SDK licenses...
echo y | "%CMD_TOOLS_PATH%\bin\sdkmanager.bat" --licenses

REM Install required SDK components
echo Installing required Android SDK components...

set SDK_COMPONENTS=platform-tools "platforms;android-34" "build-tools;34.0.0" emulator "system-images;android-34;google_apis;x86_64"

for %%i in (%SDK_COMPONENTS%) do (
    echo Installing %%i...
    "%CMD_TOOLS_PATH%\bin\sdkmanager.bat" "%%i"
)

echo Android SDK setup completed!
echo Please restart your command prompt for changes to take effect.
echo Then run: flutter doctor --android-licenses
echo And: flutter doctor

REM Create Android Virtual Devices
echo Creating Android Virtual Devices...

REM Create AVD directory if it doesn't exist
set AVD_HOME=%USERPROFILE%\.android\avd
if not exist "%AVD_HOME%" mkdir "%AVD_HOME%"

REM Create tablet AVD
echo Creating Tablet AVD for kiosk testing...
echo no | "%CMD_TOOLS_PATH%\bin\avdmanager.bat" create avd -n Tablet_Kiosk -k "system-images;android-34;google_apis;x86_64" -d pixel_tablet

REM Create phone AVD
echo Creating Phone AVD for mobile testing...
echo no | "%CMD_TOOLS_PATH%\bin\avdmanager.bat" create avd -n Phone_Test -k "system-images;android-34;google_apis;x86_64" -d pixel

REM Create TV AVD
echo Creating Android TV AVD for TV testing...
echo no | "%CMD_TOOLS_PATH%\bin\avdmanager.bat" create avd -n Android_TV -k "system-images;android-34;google_apis;x86_64" -d tv_1080p

echo Android Virtual Devices created!
echo Available emulators:
"%CMD_TOOLS_PATH%\bin\emulator.exe" -list-avds

echo.
echo Setup complete! You can now run:
echo flutter emulators --launch Tablet_Kiosk
echo flutter emulators --launch Phone_Test
echo flutter emulators --launch Android_TV

pause
