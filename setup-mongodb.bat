@echo off
REM OpenKiosk MongoDB Setup Script for Windows
REM This script helps set up MongoDB for the OpenKiosk application

echo 🚀 OpenKiosk MongoDB Setup
echo ==========================

REM Check if Docker is available
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Docker found - setting up MongoDB with Docker
    
    REM Check if MongoDB container already exists
    docker ps -a | findstr openkiosk-mongodb >nul 2>&1
    if %errorlevel% equ 0 (
        echo 📋 Existing MongoDB container found
        
        REM Check if it's running
        docker ps | findstr openkiosk-mongodb >nul 2>&1
        if %errorlevel% equ 0 (
            echo ✅ MongoDB container is already running
        ) else (
            echo 🔄 Starting existing MongoDB container...
            docker start openkiosk-mongodb
        )
    ) else (
        echo 🆕 Creating new MongoDB container...
        docker run -d ^
            --name openkiosk-mongodb ^
            -p 27017:27017 ^
            -e MONGO_INITDB_ROOT_USERNAME=admin ^
            -e MONGO_INITDB_ROOT_PASSWORD=openkiosk123 ^
            -e MONGO_INITDB_DATABASE=openkiosk ^
            -v openkiosk-mongodb-data:/data/db ^
            mongo:7.0
        
        echo ⏳ Waiting for MongoDB to start...
        timeout /t 8 >nul
        
        REM Initialize the database
        echo 📋 Initializing database...
        docker exec -i openkiosk-mongodb mongosh openkiosk -u admin -p openkiosk123 --authenticationDatabase admin < backend\content_service\init-mongo.js
    )
    
    echo ✅ MongoDB is ready!
    echo 📊 Connection: mongodb://admin:openkiosk123@localhost:27017/openkiosk?authSource=admin
    
) else (
    REM Check if MongoDB is installed locally
    mongod --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ MongoDB found locally - starting service
        
        REM Try to start MongoDB service
        net start MongoDB >nul 2>&1
        if %errorlevel% equ 0 (
            echo ✅ MongoDB service started!
        ) else (
            echo ⚠️  MongoDB service may already be running or needs manual start
        )
        
        echo 📊 Connection: mongodb://localhost:27017/openkiosk
        
    ) else (
        echo ❌ Neither Docker nor MongoDB found!
        echo.
        echo Please install one of the following:
        echo 1. Docker Desktop: https://www.docker.com/products/docker-desktop
        echo 2. MongoDB Community: https://www.mongodb.com/try/download/community
        echo.
        echo Then run this script again.
        pause
        exit /b 1
    )
)

echo.
echo 🎯 Next Steps:
echo 1. Set environment variable: set MONGO_URI=mongodb://admin:openkiosk123@localhost:27017/openkiosk?authSource=admin
echo 2. Start the backend: cd backend\content_service ^&^& python start_with_mongo.py
echo 3. All your data will now persist between restarts! 🎉
echo.
pause