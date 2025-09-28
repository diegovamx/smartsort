#!/usr/bin/env python3
"""
SmartSort Camera Auto-Detection Script
Automatically detects the system and runs the appropriate camera version
"""

import sys
import os
import platform
import subprocess

def detect_system():
    """Detect the system type and camera availability"""
    system_info = {
        'platform': platform.system(),
        'machine': platform.machine(),
        'is_raspberry_pi': False,
        'has_picamera': False,
        'has_cv2': False
    }
    
    # Check if running on Raspberry Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'BCM' in cpuinfo or 'Raspberry Pi' in cpuinfo:
                system_info['is_raspberry_pi'] = True
    except:
        pass
    
    # Check for PiCamera availability
    try:
        import picamera
        system_info['has_picamera'] = True
    except ImportError:
        system_info['has_picamera'] = False
    except OSError as e:
        if 'libbcm_host.so' in str(e):
            print("⚠️  PiCamera detected but not running on Raspberry Pi")
            system_info['has_picamera'] = False
        else:
            system_info['has_picamera'] = False
    
    # Check for OpenCV availability
    try:
        import cv2
        system_info['has_cv2'] = True
    except ImportError:
        system_info['has_cv2'] = False
    
    return system_info

def choose_camera_version():
    """Choose the appropriate camera version based on system detection"""
    system_info = detect_system()
    
    print("🔍 Detecting system and camera capabilities...")
    print(f"   Platform: {system_info['platform']}")
    print(f"   Machine: {system_info['machine']}")
    print(f"   Raspberry Pi: {system_info['is_raspberry_pi']}")
    print(f"   PiCamera available: {system_info['has_picamera']}")
    print(f"   OpenCV available: {system_info['has_cv2']}")
    
    # Decision logic
    if system_info['is_raspberry_pi'] and system_info['has_picamera']:
        print("✅ Using PiCamera version (Raspberry Pi + PiCamera)")
        return 'picamera'
    elif system_info['has_cv2']:
        print("✅ Using OpenCV version (Standard computer)")
        return 'cv2'
    else:
        print("❌ No suitable camera library found!")
        print("💡 Please install either:")
        print("   - OpenCV: pip install opencv-python")
        print("   - PiCamera: pip install picamera (Raspberry Pi only)")
        return None

def run_detection_system(camera_type):
    """Run the appropriate detection system"""
    if camera_type == 'picamera':
        print("🚀 Starting PiCamera detection system...")
        try:
            import integrated_auto_capture_picamera
            integrated_auto_capture_picamera.main()
        except Exception as e:
            print(f"❌ Error running PiCamera version: {e}")
            print("💡 Falling back to OpenCV version...")
            return run_detection_system('cv2')
    
    elif camera_type == 'cv2':
        print("🚀 Starting OpenCV detection system...")
        try:
            import integrated_auto_capture
            integrated_auto_capture.main()
        except Exception as e:
            print(f"❌ Error running OpenCV version: {e}")
            return False
    
    return True

def main():
    """Main function to auto-detect and run the appropriate system"""
    print("🎯 SmartSort Auto-Detection System")
    print("=" * 50)
    
    # Detect system and choose camera version
    camera_type = choose_camera_version()
    
    if camera_type is None:
        print("❌ Cannot start system - no suitable camera library found")
        sys.exit(1)
    
    print("=" * 50)
    
    # Run the detection system
    success = run_detection_system(camera_type)
    
    if not success:
        print("❌ Failed to start detection system")
        sys.exit(1)

if __name__ == "__main__":
    main()
