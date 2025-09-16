# Copyright (c) 2025 Adara Screen by Hebron
# Owner: Sujesh M S
# All Rights Reserved
#
# This software is proprietary to Adara Screen by Hebron.
# Unauthorized use, reproduction, or distribution is strictly prohibited.

"""
Simple analytics dashboard test page with live/batch toggle
"""

import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import websocket
import threading
import time

st.set_page_config(
    page_title="Digital Signage Platform™ Analytics", 
    page_icon="📊",
    layout="wide"
)

# WebSocket handling for live data
class WebSocketClient:
    def __init__(self):
        self.ws = None
        self.connected = False
        self.data_queue = []
        
    def connect(self):
        try:
            self.ws = websocket.WebSocketApp(
                "ws://localhost:8000/api/analytics/stream",
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            
            # Start WebSocket in a separate thread
            self.ws_thread = threading.Thread(target=self.ws.run_forever)
            self.ws_thread.daemon = True
            self.ws_thread.start()
            
        except Exception as e:
            st.error(f"WebSocket connection failed: {e}")
    
    def on_open(self, ws):
        self.connected = True
        st.success("🔗 Live connection established!")
        
    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            self.data_queue.append(data)
            if len(self.data_queue) > 100:  # Keep only last 100 messages
                self.data_queue.pop(0)
        except Exception as e:
            st.error(f"Error processing live data: {e}")
    
    def on_error(self, ws, error):
        st.error(f"WebSocket error: {error}")
        self.connected = False
        
    def on_close(self, ws, close_status_code, close_msg):
        self.connected = False
        st.warning("🔌 Live connection closed")
    
    def disconnect(self):
        if self.ws:
            self.ws.close()
        self.connected = False

# Initialize WebSocket client in session state
if 'ws_client' not in st.session_state:
    st.session_state.ws_client = WebSocketClient()

def fetch_analytics_data(time_range="24h", device="all"):
    """Fetch analytics data from the API"""
    try:
        response = requests.get(
            "http://localhost:8000/api/analytics/dashboard",
            params={"timeRange": time_range, "device": device},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")
        return None

def main():
    st.title("📊 Digital Signage Platform™ Analytics Dashboard")
    st.markdown("Real-time analytics for content performance, audience engagement, and monetization")
    
    # Sidebar controls
    st.sidebar.header("Dashboard Controls")
    
    # Live/Batch Toggle
    data_mode = st.sidebar.radio(
        "📡 Data Mode",
        ["📊 Batch (API Calls)", "🔴 Live (WebSocket)"],
        index=0
    )
    
    is_live_mode = data_mode.startswith("🔴")
    
    # WebSocket Connection Management
    if is_live_mode:
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("🔗 Connect"):
                st.session_state.ws_client.connect()
        with col2:
            if st.button("🔌 Disconnect"):
                st.session_state.ws_client.disconnect()
        
        # Connection status
        if st.session_state.ws_client.connected:
            st.sidebar.success("✅ Live Connected")
            st.sidebar.metric("Live Messages", len(st.session_state.ws_client.data_queue))
        else:
            st.sidebar.error("❌ Not Connected")
    
    # Standard controls
    time_range = st.sidebar.selectbox(
        "Time Range",
        ["1h", "24h", "7d", "30d"],
        index=1
    )
    
    device_filter = st.sidebar.selectbox(
        "Device Filter", 
        ["all", "DEVICE_001", "DEVICE_002", "DEVICE_003", "DEVICE_004"],
        index=0
    )
    
    # Auto-refresh for batch mode
    if not is_live_mode:
        auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", value=False)
        if auto_refresh:
            time.sleep(30)
            st.rerun()
    else:
        # Live mode auto-refresh
        if st.sidebar.checkbox("Live Updates", value=True):
            time.sleep(5)  # Refresh every 5 seconds in live mode
            st.rerun()
    
    # Data fetching based on mode
    if is_live_mode and st.session_state.ws_client.connected:
        # Use live WebSocket data
        if st.session_state.ws_client.data_queue:
            latest_data = st.session_state.ws_client.data_queue[-1]
            if 'metrics' in latest_data:
                data = latest_data['metrics']
            else:
                data = fetch_analytics_data(time_range, device_filter)
        else:
            st.info("🔄 Waiting for live data...")
            data = fetch_analytics_data(time_range, device_filter)
    else:
        # Use batch API calls
        data = fetch_analytics_data(time_range, device_filter)
    
    if data is None:
        st.warning("Unable to fetch analytics data. Please check if the backend server is running.")
        st.code("Backend URL: http://localhost:8000")
        return
    
    # Extract data
    summary = data.get("summary", {})
    devices = data.get("devices", [])
    time_series = data.get("timeSeriesData", [])
    
    # Key Metrics Row
    st.header("📈 Key Performance Indicators")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Devices", 
            summary.get("totalDevices", 0),
            delta=f"{summary.get('onlineDevices', 0)} online"
        )
    
    with col2:
        revenue = summary.get("totalRevenue", 0)
        st.metric("Total Revenue", f"${revenue:.2f}")
    
    with col3:
        impressions = summary.get("totalImpressions", 0)
        st.metric("Total Impressions", f"{impressions:,}")
    
    with col4:
        engagement = summary.get("averageEngagement", 0)
        st.metric("Avg Engagement", f"{engagement:.1f}%")
    
    with col5:
        st.metric("Data Points", len(time_series))
    
    # Charts Row
    if time_series:
        st.header("📊 Performance Trends")
        
        # Convert time series to DataFrame
        df = pd.DataFrame(time_series)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Impressions and Interactions over time
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['timestamp'], 
                y=df['impressions'],
                mode='lines+markers',
                name='Impressions',
                line=dict(color='blue')
            ))
            fig.add_trace(go.Scatter(
                x=df['timestamp'], 
                y=df['interactions'],
                mode='lines+markers',
                name='Interactions',
                line=dict(color='green')
            ))
            fig.update_layout(
                title="Content Performance Over Time",
                xaxis_title="Time",
                yaxis_title="Count"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Revenue over time
            fig = px.line(
                df, 
                x='timestamp', 
                y='revenue',
                title="Revenue Over Time",
                markers=True
            )
            fig.update_traces(line_color='orange')
            st.plotly_chart(fig, use_container_width=True)
    
    # Device Performance Table
    if devices:
        st.header("🖥️ Device Performance")
        
        # Create device DataFrame
        device_data = []
        for device in devices:
            device_data.append({
                "Device": device.get("deviceName", "Unknown"),
                "Status": "🟢 Online" if device.get("isOnline") else "🔴 Offline",
                "Revenue": f"${device.get('monetization', {}).get('totalRevenue', 0):.2f}",
                "Impressions": device.get('contentMetrics', {}).get('impressions', 0),
                "Interactions": device.get('contentMetrics', {}).get('interactions', 0),
                "Users Detected": device.get('proximityData', {}).get('totalDetections', 0),
                "Engagement": f"{device.get('proximityData', {}).get('averageEngagementTime', 0):.1f}s"
            })
        
        df_devices = pd.DataFrame(device_data)
        st.dataframe(df_devices, use_container_width=True)
        
        # Device Revenue Chart
        if len(devices) > 1:
            fig = px.bar(
                df_devices, 
                x='Device', 
                y=[float(x.replace('$', '')) for x in df_devices['Revenue']],
                title="Revenue by Device"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # System Health Overview
    st.header("🔧 System Health")
    if devices:
        health_cols = st.columns(min(len(devices), 4))
        for i, device in enumerate(devices[:4]):
            with health_cols[i]:
                st.subheader(device.get("deviceName", "Unknown"))
                health = device.get("systemHealth", {})
                
                # CPU Usage
                cpu = health.get("cpuUsage", 0)
                st.progress(cpu / 100, text=f"CPU: {cpu:.1f}%")
                
                # Memory Usage
                memory = health.get("memoryUsage", 0)
                st.progress(memory / 100, text=f"Memory: {memory:.1f}%")
                
                # Storage Usage
                storage = health.get("storageUsage", 0)
                st.progress(storage / 100, text=f"Storage: {storage:.1f}%")
                
                # Network Latency
                latency = health.get("networkLatency", 0)
                st.metric("Latency", f"{latency:.1f}ms")
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("🚀 **Digital Signage Platform™**")
    with col2:
        st.markdown(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    with col3:
        if st.button("🔄 Refresh Data"):
            st.rerun()

if __name__ == "__main__":
    main()
