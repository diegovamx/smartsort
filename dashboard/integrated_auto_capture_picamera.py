import time
import os
import numpy as np
import json
from datetime import datetime
from inference_sdk import InferenceHTTPClient
import requests
import threading
from picamera import PiCamera
from picamera.array import PiRGBArray
import io

# Global variables for motion detection
frame_count = 0
capture_triggered = False
classification_in_progress = False
background_subtractor = None
motion_threshold = 5000  # Minimum area of motion to trigger capture
min_motion_frames = 5  # Number of consecutive frames with motion required
motion_frame_count = 0
last_capture_time = 0
capture_cooldown = 20.0  # seconds between captures (allows full UI interaction cycle)
motion_detected_time = 0
capture_delay = 2.0  # seconds to wait after motion before capturing

# Initialize picamera
camera = None
raw_capture = None

def save_classification_result(filename, classification, confidence):
    """
    Save classification result to JSON file for dashboard integration
    """
    results_file = os.path.join('detected_images', 'classification_results.json')
    
    # Load existing results
    results = {}
    if os.path.exists(results_file):
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)
        except:
            results = {}
    
    # Add new result
    results[filename] = {
        'classification': classification,
        'confidence': confidence,
        'timestamp': datetime.now().isoformat()
    }
    
    # Save back to file
    try:
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"💾 Classification result saved to {results_file}")
        
        # Send real-time update to dashboard
        send_realtime_update(filename, classification, confidence)
        
        return True
    except Exception as e:
        print(f"❌ Error saving classification result: {e}")
        return False

def send_frontend_refresh():
    """
    Send refresh signal to frontend to automatically reload the page
    """
    try:
        # Send refresh signal to dashboard
        response = requests.post(
            'http://localhost:5001/api/refresh_frontend',
            json={'refresh': True},
            timeout=2
        )
        
        if response.status_code == 200:
            print("🔄 Frontend refresh signal sent!")
        else:
            print(f"⚠️ Failed to send refresh signal: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Frontend refresh failed: {str(e)}")
        # Don't fail the main process if refresh fails

def send_realtime_update(filename, classification, confidence):
    """
    Send real-time update to the dashboard via HTTP request
    """
    try:
        response = requests.post(
            'http://localhost:5001/api/realtime_update',
            json={
                'filename': filename,
                'classification': classification,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat()
            },
            timeout=2
        )
        
        if response.status_code == 200:
            print("📡 Real-time update sent to dashboard")
        else:
            print(f"⚠️ Failed to send real-time update: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Real-time update failed: {str(e)}")
        # Don't fail the main process if real-time updates fail

def capture_and_analyze(frame):
    """
    Save the current frame and run classification inference
    """
    global frame_count, classification_in_progress, capture_cooldown
    
    frame_count += 1
    classification_in_progress = True
    
    # Create images directory if it doesn't exist
    if not os.path.exists('detected_images'):
        os.makedirs('detected_images')
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"detection_{timestamp}_{frame_count}.jpg"
    filepath = os.path.join('detected_images', filename)
    
    try:
        print(f"\n📸 Capturing image...")
        
        # Save the current frame
        # Convert numpy array to image and save
        from PIL import Image
        img = Image.fromarray(frame)
        img.save(filepath)
        print(f"✅ Picture saved: {filepath}")
        
        # Run classification inference immediately on the captured image
        print("🔄 Running classification inference on captured image...")
        
        # Initialize the HTTP client
        client = InferenceHTTPClient(
            api_url="https://serverless.roboflow.com",
            api_key="Mqg6MjfPG888hkIAilqR"
        )
        
        # Run the workflow on the captured image
        result = client.run_workflow(
            workspace_name="smartsort-vfpxc",
            workflow_id="smartsort-classify-v1",
            #alternative models
                # workflow_id="smartsort-classify-simple-v2",
                # workflow_id="smartsort-classify-simple-v3",
                # workflow_id="smartsort-classify-simple-v4",
            images={
                "image": filepath
            },
            use_cache=True  # cache workflow definition for 15 minutes
        )
        
        if result:
            print(f"📦 Classification Results for {filename}:")
            
            # Parse the result - get the first prediction
            classification = "Unknown"
            confidence = 0.0
            
            if isinstance(result, list) and len(result) > 0:
                # Handle list format (workflow result)
                model_predictions = result[0].get('model_predictions', {})
                predictions = model_predictions.get('predictions', [])
                
                if predictions:
                    first_prediction = predictions[0]
                    classification = first_prediction.get('class', 'Unknown')
                    confidence = first_prediction.get('confidence', 0)
                    confidence_pct = confidence * 100 if isinstance(confidence, (int, float)) else confidence
                    
                    print(f"   🎯 {classification} (confidence: {confidence_pct:.2f}%)")
                else:
                    print("   ❌ No predictions found")
            elif isinstance(result, dict):
                # Handle dict format
                if 'predictions' in result:
                    predictions = result['predictions']
                    if predictions:
                        first_prediction = predictions[0]
                        classification = first_prediction.get('class', first_prediction.get('class_name', 'Unknown'))
                        confidence = first_prediction.get('confidence', 0)
                        confidence_pct = confidence * 100 if isinstance(confidence, (int, float)) else confidence
                        
                        print(f"   🎯 {classification} (confidence: {confidence_pct:.2f}%)")
                    else:
                        print("   ❌ No predictions found")
                else:
                    print(f"   ❌ Unexpected result format: {result}")
            else:
                print(f"   ❌ Unexpected result type: {type(result)}")
            
            # Check if we have valid predictions or Unknown classification
            if classification == "Unknown" or (classification == "Unknown" and confidence == 0.0):
                print("❌ Unknown classification - resetting to camera feed")
                print("🔄 Please scan again with a clearer view of the object")
                
                # Save "Unknown" result
                save_classification_result(filename, "Unknown", 0.0)
                
                # Send refresh signal to frontend to go back to camera
                send_frontend_refresh()
                
                # Set shorter cooldown for unknown classifications
                original_cooldown = capture_cooldown
                capture_cooldown = 5.0  # 5 second cooldown for unknown
                
                # Reset cooldown after 5 seconds
                def reset_cooldown():
                    global capture_cooldown
                    capture_cooldown = original_cooldown
                threading.Timer(5.0, reset_cooldown).start()
                
                return True
            else:
                # Save classification result for dashboard (valid classifications)
                confidence_value = confidence * 100 if confidence <= 1 else confidence
                save_classification_result(filename, classification, round(confidence_value, 2))
        else:
            print("❌ No classification results for captured image")
            print("🔄 Please scan again with a clearer view of the object")
            
            # Save "No Result" for failed classification
            save_classification_result(filename, "No Result", 0.0)
            
            # Send refresh signal to frontend
            send_frontend_refresh()
            
            # Set shorter cooldown for no results
            original_cooldown = capture_cooldown
            capture_cooldown = 5.0  # 5 second cooldown for no results
            
            # Reset cooldown after 5 seconds
            def reset_cooldown():
                global capture_cooldown
                capture_cooldown = original_cooldown
            threading.Timer(5.0, reset_cooldown).start()
            
            return True
        
        # Keep classification in progress for full UI interaction period
        # UI needs: 3s processing + 5s guessing + 3s result + 9s cooldown = 20s total
        print(f"⏳ UI interaction period: 20 seconds (processing + guessing + result + cooldown)")
        print(f"🔄 Classification in progress for UI interaction...")
        
        # Send refresh signal to frontend to switch to UI
        print("🔄 Sending refresh signal to switch to UI...")
        send_frontend_refresh()
        
        # Don't reset classification_in_progress immediately
        # It will be reset by the cooldown period in the main loop
        return True
        
    except Exception as e:
        print(f"❌ Error capturing/analyzing image: {e}")
        classification_in_progress = False
        return False

def detect_motion(frame):
    """
    Detect motion in the frame using background subtraction
    """
    global background_subtractor, motion_frame_count, motion_threshold, min_motion_frames
    
    # Initialize background subtractor if not already done
    if background_subtractor is None:
        import cv2
        background_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True,
            varThreshold=50,
            history=500
        )
        return False, 0
    
    # Apply background subtraction
    fg_mask = background_subtractor.apply(frame)
    
    # Remove noise with morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
    
    # Find contours of motion
    contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Calculate total motion area
    motion_area = 0
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 100:  # Filter out small noise
            motion_area += area
    
    # Check if motion is significant enough
    if motion_area > motion_threshold:
        motion_frame_count += 1
        if motion_frame_count >= min_motion_frames:
            motion_frame_count = 0  # Reset counter
            return True, motion_area
    else:
        motion_frame_count = 0  # Reset counter if no motion
    
    return False, motion_area

def motion_detection_loop():
    """
    Main motion detection loop using PiCamera
    """
    global capture_triggered, last_capture_time, capture_cooldown, motion_detected_time, capture_delay, classification_in_progress, camera, raw_capture
    
    # Initialize PiCamera
    try:
        camera = PiCamera()
        camera.resolution = (1280, 720)
        camera.framerate = 30
        raw_capture = PiRGBArray(camera, size=(1280, 720))
        
        # Allow camera to warm up
        time.sleep(2)
        
        print("🎥 Starting motion detection with PiCamera...")
        print("💡 Press 'q' to quit, or Ctrl+C to stop")
        
        # Give camera time to adjust and learn background
        print("🔄 Learning background (5 seconds)...")
        for i in range(150):  # ~5 seconds at 30fps
            camera.capture(raw_capture, format="bgr")
            frame = raw_capture.array
            if frame is not None:
                detect_motion(frame)  # Initialize background model
            raw_capture.truncate(0)
            time.sleep(0.033)  # ~30fps
        
        print("✅ Background learning complete!")
        
        print("🎯 Motion detection ready!")
        print("=" * 50)
        print("📋 SYSTEM READY - Press ENTER to start motion detection")
        print("=" * 50)
        
        # Create a status file to indicate system is ready
        status_file = os.path.join('detected_images', 'system_status.json')
        os.makedirs('detected_images', exist_ok=True)
        
        with open(status_file, 'w') as f:
            json.dump({
                'system_ready': True,
                'timestamp': datetime.now().isoformat(),
                'message': 'System ready for motion detection'
            }, f)
        
        # Wait for user to press Enter
        input()
        
        # Send refresh signal to frontend
        send_frontend_refresh()
        
        print("🚀 Motion detection starting in 10 seconds...")
        print("⏰ Get ready to place an object in front of the camera!")
        
        # Countdown before starting motion detection
        for i in range(10, 0, -1):
            print(f"⏳ Starting in {i}...", end="", flush=True)
            time.sleep(1)
            print("\r" + " " * 20 + "\r", end="", flush=True)  # Clear the line
        
        print("🎯 Motion detection active! Place an object in front of the camera.")
        print("💡 Press 'q' to quit, or Ctrl+C to stop")
        
        try:
            while True:
                current_time = time.time()
                
                # Check cooldown period
                if current_time - last_capture_time < capture_cooldown:
                    remaining = capture_cooldown - (current_time - last_capture_time)
                    print(f"\r⏳ Cooldown: {remaining:.1f}s remaining", end="", flush=True)
                    
                    # Reset classification_in_progress when cooldown is almost over
                    if remaining < 2.0 and classification_in_progress:
                        print(f"\n✅ UI interaction complete, ready for next detection")
                        classification_in_progress = False
                    
                    time.sleep(0.1)
                    continue
                
                # Skip motion detection if classification is in progress
                if classification_in_progress:
                    print(f"\r🔄 Classification in progress...", end="", flush=True)
                    time.sleep(0.5)  # Longer sleep to reduce CPU usage
                    continue
                
                # Capture frame from PiCamera
                camera.capture(raw_capture, format="bgr")
                frame = raw_capture.array
                raw_capture.truncate(0)
                
                if frame is None:
                    print("❌ Error: Could not read frame from camera")
                    break
                
                # Detect motion in the frame
                motion_detected, motion_area = detect_motion(frame)
                
                if motion_detected:
                    print(f"\n🎯 Motion detected! Area: {motion_area:.0f} pixels")
                    
                    # Check if we're in the delay period
                    if motion_detected_time == 0:
                        motion_detected_time = current_time
                        print(f"⏳ Waiting {capture_delay} seconds before capture...")
                        continue
                    elif current_time - motion_detected_time >= capture_delay:
                        # Time to capture!
                        print(f"📸 Capturing image after {capture_delay}s delay...")
                        
                        # Capture and analyze the image
                        if capture_and_analyze(frame):
                            last_capture_time = current_time
                            capture_triggered = True
                            motion_detected_time = 0  # Reset motion detection
                        else:
                            print("❌ Automatic capture failed!")
                            motion_detected_time = 0  # Reset motion detection
                    else:
                        # Still in delay period
                        remaining = capture_delay - (current_time - motion_detected_time)
                        print(f"\r⏳ Capture in {remaining:.1f}s...", end="", flush=True)
                else:
                    # No motion detected, reset motion timer
                    if motion_detected_time != 0:
                        motion_detected_time = 0
                        print(f"\r🔍 Monitoring for motion...", end="", flush=True)
                    else:
                        print(f"\r🔍 Monitoring for motion...", end="", flush=True)
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.033)  # ~30fps
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping motion detection...")
        finally:
            if camera:
                camera.close()
                print("📷 Camera closed")
    
    except Exception as e:
        print(f"❌ Error initializing PiCamera: {e}")
        print("💡 Make sure you're running this on a Raspberry Pi with a camera connected")
        return

def main():
    print("🚀 Starting SmartSort Motion-Based Auto-Capture (PiCamera Version)")
    print("=" * 70)
    print("📋 Features:")
    print("  • Motion detection using background subtraction")
    print("  • Automatic capture when motion detected")
    print("  • Instant classification after capture")
    print("  • Runs classification model on captured images")
    print("  • Dashboard integration - results saved to JSON")
    print("  • PiCamera integration for Raspberry Pi")
    print("=" * 70)
    print("💡 Behavior:")
    print("  • Learns background for 5 seconds on startup")
    print("  • Detects motion continuously")
    print("  • Automatically captures and classifies when motion found")
    print("  • Results are saved for dashboard viewing")
    print("  • Press Ctrl+C to stop")
    print("=" * 70)
    print("⚙️  Motion Settings:")
    print(f"  • Motion threshold: {motion_threshold} pixels")
    print(f"  • Min motion frames: {min_motion_frames}")
    print(f"  • Capture delay: {capture_delay} seconds")
    print(f"  • Capture cooldown: {capture_cooldown} seconds")
    print("=" * 70)
    print("🌐 Dashboard: Run 'python app.py' in the dashboard folder to view results")
    print("=" * 70)
    
    try:
        # Start motion detection loop
        motion_detection_loop()
        
    except KeyboardInterrupt:
        print("\n🛑 SmartSort system stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if camera:
            camera.close()
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()
