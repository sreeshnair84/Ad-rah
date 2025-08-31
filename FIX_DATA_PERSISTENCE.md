# 🔧 CRITICAL: Fix Data Persistence Issue

## ⚠️ Current Problem
Your OpenKiosk application is currently using **IN-MEMORY STORAGE**, which means:
- ❌ All data is lost when the server restarts
- ❌ Device registrations are lost
- ❌ User accounts are lost  
- ❌ Content uploads are lost
- ❌ All configuration is reset

## ✅ Solution: Enable MongoDB Persistent Storage

### Quick Fix (Recommended)

#### For Windows:
```bash
# Run the automated setup
setup-mongodb.bat

# Then start the application
cd backend\content_service
python start_with_mongo.py
```

#### For Linux/Mac:
```bash
# Run the automated setup
chmod +x setup-mongodb.sh
./setup-mongodb.sh

# Then start the application
cd backend/content_service
python start_with_mongo.py
```

### Manual Setup

#### Option 1: Using Docker (Easiest)

1. **Install Docker Desktop** from https://www.docker.com/products/docker-desktop

2. **Start MongoDB container:**
```bash
docker run -d \
  --name openkiosk-mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=openkiosk123 \
  -e MONGO_INITDB_DATABASE=openkiosk \
  -v openkiosk-mongodb-data:/data/db \
  mongo:7.0
```

3. **Set environment variable:**
```bash
# Windows
set MONGO_URI=mongodb://admin:openkiosk123@localhost:27017/openkiosk?authSource=admin

# Linux/Mac
export MONGO_URI="mongodb://admin:openkiosk123@localhost:27017/openkiosk?authSource=admin"
```

#### Option 2: Install MongoDB Locally

1. **Download MongoDB Community** from https://www.mongodb.com/try/download/community

2. **Install and start the service:**
   - Windows: Service starts automatically after installation
   - Linux: `sudo systemctl start mongod && sudo systemctl enable mongod`
   - Mac: `brew services start mongodb/brew/mongodb-community`

3. **Set environment variable:**
```bash
# Windows
set MONGO_URI=mongodb://localhost:27017/openkiosk

# Linux/Mac
export MONGO_URI="mongodb://localhost:27017/openkiosk"
```

### Starting the Application

#### Method 1: Use the enhanced startup script
```bash
cd backend/content_service
python start_with_mongo.py
```

#### Method 2: Traditional method with environment variables
```bash
# Set the MongoDB connection (choose one)
set MONGO_URI=mongodb://localhost:27017/openkiosk                           # Local MongoDB
set MONGO_URI=mongodb://admin:openkiosk123@localhost:27017/openkiosk?authSource=admin  # Docker MongoDB

# Install MongoDB dependencies
pip install -r requirements-mongodb.txt

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🎯 How to Verify It's Working

When you start the application, look for these messages:

### ✅ SUCCESS (Persistent Storage):
```
✅ Successfully initialized MongoDB repository - DATA WILL PERSIST
✅ PERSISTENT STORAGE ENABLED - Data will survive restarts!
📊 Repository type: MongoRepo
```

### ❌ STILL BROKEN (Temporary Storage):
```
⚠️  Using in-memory repository - DATA WILL BE LOST ON RESTART
⚠️ TEMPORARY STORAGE - Data will be LOST on restart!
💾 Repository type: InMemoryRepo
🔧 To enable persistence, run: setup-mongodb.bat (Windows) or setup-mongodb.sh (Linux/Mac)
```

## 🔍 Troubleshooting

### Issue: "Motor not available"
```bash
pip install motor pymongo dnspython
```

### Issue: "Connection failed"
- Check if MongoDB is running: `docker ps` or `systemctl status mongod`
- Verify the connection string is correct
- Check firewall settings (MongoDB uses port 27017)

### Issue: "Permission denied"
- Windows: Run Command Prompt as Administrator
- Linux/Mac: Use `sudo` for system service commands

### Issue: Environment variable not set
```bash
# Make it permanent (Windows)
setx MONGO_URI "mongodb://localhost:27017/openkiosk"

# Make it permanent (Linux/Mac) - add to ~/.bashrc or ~/.zshrc
echo 'export MONGO_URI="mongodb://localhost:27017/openkiosk"' >> ~/.bashrc
source ~/.bashrc
```

## 🎉 After Fixing

Once persistent storage is enabled:
- ✅ Device registrations persist between restarts
- ✅ User accounts and login credentials are saved
- ✅ Content uploads are permanently stored
- ✅ All configuration persists
- ✅ Application is production-ready

## 🚀 Using Docker Compose (Full Stack)

For a complete setup with frontend and backend:

```bash
# Start everything with persistent storage
docker-compose up -d

# View logs
docker-compose logs -f

# Stop everything
docker-compose down

# Reset everything (including data)
docker-compose down -v
```

---

**IMPORTANT**: This fix is CRITICAL for production use. Without persistent storage, your kiosk system will lose all device registrations and content every time the server restarts!