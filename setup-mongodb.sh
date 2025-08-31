#!/bin/bash

# OpenKiosk MongoDB Setup Script
# This script helps set up MongoDB for the OpenKiosk application

echo "🚀 OpenKiosk MongoDB Setup"
echo "=========================="

# Check if Docker is available
if command -v docker >/dev/null 2>&1; then
    echo "✅ Docker found - setting up MongoDB with Docker"
    
    # Check if MongoDB container already exists
    if docker ps -a | grep -q openkiosk-mongodb; then
        echo "📋 Existing MongoDB container found"
        
        # Check if it's running
        if docker ps | grep -q openkiosk-mongodb; then
            echo "✅ MongoDB container is already running"
        else
            echo "🔄 Starting existing MongoDB container..."
            docker start openkiosk-mongodb
        fi
    else
        echo "🆕 Creating new MongoDB container..."
        docker run -d \
            --name openkiosk-mongodb \
            -p 27017:27017 \
            -e MONGO_INITDB_ROOT_USERNAME=admin \
            -e MONGO_INITDB_ROOT_PASSWORD=openkiosk123 \
            -e MONGO_INITDB_DATABASE=openkiosk \
            -v openkiosk-mongodb-data:/data/db \
            mongo:7.0
        
        echo "⏳ Waiting for MongoDB to start..."
        sleep 5
        
        # Initialize the database
        echo "📋 Initializing database..."
        docker exec -i openkiosk-mongodb mongosh openkiosk -u admin -p openkiosk123 --authenticationDatabase admin < backend/content_service/init-mongo.js
    fi
    
    echo "✅ MongoDB is ready!"
    echo "📊 Connection: mongodb://admin:openkiosk123@localhost:27017/openkiosk?authSource=admin"
    
elif command -v mongod >/dev/null 2>&1; then
    echo "✅ MongoDB found locally - starting service"
    
    # Try to start MongoDB service
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo systemctl start mongod
        sudo systemctl enable mongod
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start mongodb/brew/mongodb-community
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        net start MongoDB
    fi
    
    echo "✅ MongoDB service started!"
    echo "📊 Connection: mongodb://localhost:27017/openkiosk"
    
else
    echo "❌ Neither Docker nor MongoDB found!"
    echo ""
    echo "Please install one of the following:"
    echo "1. Docker Desktop: https://www.docker.com/products/docker-desktop"
    echo "2. MongoDB Community: https://www.mongodb.com/try/download/community"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo ""
echo "🎯 Next Steps:"
echo "1. Set environment variable: export MONGO_URI=\"mongodb://admin:openkiosk123@localhost:27017/openkiosk?authSource=admin\""
echo "2. Start the backend: cd backend/content_service && python start_with_mongo.py"
echo "3. All your data will now persist between restarts! 🎉"