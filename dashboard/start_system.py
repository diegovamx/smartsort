#!/usr/bin/env python3
"""
SmartSort System Launcher
Runs both the Flask dashboard and the detection system simultaneously
"""

import subprocess
import sys
import time
import os
import signal
import threading
from pathlib import Path

class SmartSortLauncher:
    def __init__(self):
        self.flask_process = None
        self.detection_process = None
        self.running = True
        
    def start_flask_dashboard(self):
        """Start the Flask dashboard server"""
        print("🚀 Starting Flask Dashboard...")
        try:
            self.flask_process = subprocess.Popen([
                sys.executable, 'app.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Wait a moment for Flask to start
            time.sleep(3)
            
            if self.flask_process.poll() is None:
                print("✅ Flask Dashboard started successfully!")
                print("🌐 Dashboard available at: http://localhost:5001")
                print("👤 User Interface available at: http://localhost:5001/user")
            else:
                print("❌ Failed to start Flask Dashboard")
                return False
                
        except Exception as e:
            print(f"❌ Error starting Flask Dashboard: {e}")
            return False
            
        return True
    
    def start_detection_system(self):
        """Start the detection system with auto-detection"""
        print("🎥 Starting Detection System with auto-detection...")
        try:
            self.detection_process = subprocess.Popen([
                sys.executable, 'auto_detect_camera.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Wait a moment for detection system to initialize
            time.sleep(2)
            
            if self.detection_process.poll() is None:
                print("✅ Detection System started successfully!")
            else:
                print("❌ Failed to start Detection System")
                return False
                
        except Exception as e:
            print(f"❌ Error starting Detection System: {e}")
            return False
            
        return True
    
    def monitor_processes(self):
        """Monitor both processes and restart if needed"""
        while self.running:
            time.sleep(5)  # Check every 5 seconds
            
            # Check Flask process
            if self.flask_process and self.flask_process.poll() is not None:
                print("⚠️ Flask Dashboard stopped unexpectedly")
                if self.running:
                    print("🔄 Restarting Flask Dashboard...")
                    self.start_flask_dashboard()
            
            # Check Detection process
            if self.detection_process and self.detection_process.poll() is not None:
                print("⚠️ Detection System stopped unexpectedly")
                if self.running:
                    print("🔄 Restarting Detection System...")
                    self.start_detection_system()
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n🛑 Shutting down SmartSort System...")
        self.running = False
        
        if self.flask_process:
            print("🔄 Stopping Flask Dashboard...")
            self.flask_process.terminate()
            try:
                self.flask_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.flask_process.kill()
        
        if self.detection_process:
            print("🔄 Stopping Detection System...")
            self.detection_process.terminate()
            try:
                self.detection_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.detection_process.kill()
        
        print("✅ SmartSort System stopped")
        sys.exit(0)
    
    def run(self):
        """Main launcher function"""
        print("=" * 60)
        print("🤖 SmartSort System Launcher")
        print("=" * 60)
        print("📊 Starting both Flask Dashboard and Detection System...")
        print("=" * 60)
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Start Flask Dashboard
        if not self.start_flask_dashboard():
            print("❌ Failed to start Flask Dashboard. Exiting.")
            return
        
        # Start Detection System
        if not self.start_detection_system():
            print("❌ Failed to start Detection System. Exiting.")
            self.cleanup()
            return
        
        print("=" * 60)
        print("🎉 SmartSort System is now running!")
        print("=" * 60)
        print("📊 Dashboard: http://localhost:5001")
        print("👤 User Interface: http://localhost:5001/user")
        print("🎥 Detection System: Running in background")
        print("=" * 60)
        print("💡 Press Ctrl+C to stop the system")
        print("=" * 60)
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
        monitor_thread.start()
        
        try:
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)
    
    def cleanup(self):
        """Clean up processes"""
        if self.flask_process:
            self.flask_process.terminate()
        if self.detection_process:
            self.detection_process.terminate()

def main():
    """Main entry point"""
    # Check if we're in the right directory
    if not os.path.exists('app.py') or not os.path.exists('integrated_auto_capture.py'):
        print("❌ Error: Please run this script from the dashboard directory")
        print("💡 Make sure app.py and integrated_auto_capture.py are in the current directory")
        sys.exit(1)
    
    # Create launcher and run
    launcher = SmartSortLauncher()
    launcher.run()

if __name__ == "__main__":
    main()
