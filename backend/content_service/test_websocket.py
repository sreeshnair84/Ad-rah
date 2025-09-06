"""
Test WebSocket connection with proper datetime handling
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_websocket():
    uri = "ws://localhost:8000/api/analytics/stream"
    
    try:
        print("🔗 Connecting to WebSocket...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Listen for initial messages
            for i in range(5):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    print(f"📨 Message {i+1}:")
                    print(f"   Type: {data.get('type', 'unknown')}")
                    print(f"   Timestamp: {data.get('timestamp', 'none')}")
                    if 'metrics' in data:
                        print(f"   Metrics: {len(data['metrics'])} items")
                    print()
                    
                except asyncio.TimeoutError:
                    print(f"⏰ Timeout waiting for message {i+1}")
                    break
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                except Exception as e:
                    print(f"❌ Error receiving message: {e}")
            
            # Send a test message
            test_message = {
                "type": "request_current_metrics",
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(test_message))
            print("📤 Sent test request")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)
                print("📥 Response received:")
                print(f"   Type: {data.get('type', 'unknown')}")
                print(f"   Timestamp: {data.get('timestamp', 'none')}")
                
            except asyncio.TimeoutError:
                print("⏰ Timeout waiting for response")
                
    except ConnectionRefusedError:
        print("❌ Connection refused - is the backend server running?")
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

if __name__ == "__main__":
    print("🚀 Testing WebSocket Analytics Stream")
    print("Backend should be running at: http://localhost:8000")
    print()
    
    asyncio.run(test_websocket())
