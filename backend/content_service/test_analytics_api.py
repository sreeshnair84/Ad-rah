#!/usr/bin/env python3
"""
Quick test script for the analytics dashboard API
"""

import requests
import json

def test_analytics_api():
    """Test the analytics dashboard API"""
    
    # Test the analytics dashboard endpoint
    try:
        response = requests.get(
            "http://localhost:8000/api/analytics/dashboard",
            params={
                "timeRange": "24h",
                "device": "all"
            },
            headers={
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Analytics dashboard API working!")
            print(f"📊 Total devices: {data.get('summary', {}).get('totalDevices', 0)}")
            print(f"💰 Total revenue: ${data.get('summary', {}).get('totalRevenue', 0):.2f}")
            print(f"👁️ Total impressions: {data.get('summary', {}).get('totalImpressions', 0)}")
            print(f"📈 Average engagement: {data.get('summary', {}).get('averageEngagement', 0):.1f}%")
            print(f"🎯 Time series data points: {len(data.get('timeSeriesData', []))}")
            
            # Show sample device data
            devices = data.get('devices', [])
            if devices:
                print(f"\n📱 Sample device data:")
                for i, device in enumerate(devices[:2]):  # Show first 2 devices
                    print(f"  Device {i+1}: {device.get('deviceName')} - Revenue: ${device.get('monetization', {}).get('totalRevenue', 0):.2f}")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error text: {response.text}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_analytics_health():
    """Test analytics health endpoint"""
    try:
        response = requests.get("http://localhost:8000/api/analytics/health", timeout=5)
        if response.status_code == 200:
            print("✅ Analytics service is healthy")
            print(f"📋 Health data: {response.json()}")
        else:
            print(f"⚠️ Analytics health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

def test_real_time_metrics():
    """Test real-time metrics endpoint"""
    try:
        response = requests.get("http://localhost:8000/api/analytics/real-time", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Real-time metrics working!")
            print(f"📊 Metrics available: {len(data.get('metrics', []))}")
        else:
            print(f"⚠️ Real-time metrics failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Real-time metrics error: {e}")

if __name__ == "__main__":
    print("🚀 Testing Digital Signage Platform™ Analytics")
    print("=" * 50)
    
    # Test health first
    test_analytics_health()
    print()
    
    # Test real-time metrics
    test_real_time_metrics()
    print()
    
    # Test dashboard API
    test_analytics_api()
    
    print("\n✅ Analytics API testing completed!")
