#!/usr/bin/env python3
"""
SmartSort Dashboard Startup Script
This script starts the analytics dashboard and provides instructions.
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import flask
        import flask_socketio
        import requests
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Please install requirements: pip3 install -r requirements.txt")
        return False

def start_dashboard():
    """Start the Flask dashboard server"""
    print("🚀 Starting SmartSort Analytics Dashboard...")
    print("=" * 50)
    
    try:
        # Start the dashboard server
        process = subprocess.Popen([
            sys.executable, "web_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if server is running
        try:
            import requests
            response = requests.get("http://localhost:8080", timeout=5)
            if response.status_code == 200:
                print("✅ Dashboard started successfully!")
                print("🌐 Dashboard URL: http://localhost:8080")
                
                # Try to open in browser
                try:
                    webbrowser.open("http://localhost:8080")
                    print("🌍 Opened dashboard in your default browser")
                except:
                    print("📱 Please open http://localhost:8080 in your browser")
                
                print("\n" + "=" * 50)
                print("📋 NEXT STEPS:")
                print("1. Keep this terminal open (dashboard is running)")
                print("2. Open a NEW terminal window")
                print("3. Run: python3 smartsort.py")
                print("4. Point your webcam at objects to see live data!")
                print("=" * 50)
                
                # Keep the dashboard running
                try:
                    process.wait()
                except KeyboardInterrupt:
                    print("\n🛑 Dashboard stopped by user")
                    process.terminate()
                    
            else:
                print(f"⚠️  Dashboard responded with status: {response.status_code}")
                
        except requests.exceptions.RequestException:
            print("❌ Dashboard failed to start properly")
            process.terminate()
            return False
            
    except Exception as e:
        print(f"❌ Failed to start dashboard: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print("🔄 SmartSort Analytics Dashboard")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Start dashboard
    if start_dashboard():
        print("🎉 Dashboard setup complete!")
    else:
        print("💥 Failed to start dashboard")

if __name__ == "__main__":
    main()
