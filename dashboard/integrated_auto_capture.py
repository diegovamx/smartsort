import time
import os
import cv2
import json
from datetime import datetime
from inference_sdk import InferenceHTTPClient
import requests
import stepper_motor_control
import RPi.GPIO as GPIO

# Global variables for motion detection
frame_count = 0
capture_triggered = False
classification_in_progress = False
background_subtractor = None
motion_threshold = 15000  # Minimum area of motion to trigger capture (less sensitive)
min_motion_frames = 8  # Number of consecutive frames with motion required (more stable)
motion_frame_count = 0
last_capture_time = 0
capture_cooldown = 20.0  # seconds between captures (allows full UI interaction cycle)
motion_detected_time = 0
capture_delay = 2.0  # seconds to wait after motion before capturing

classificationMap = {
    #Recycle category
    'plastic': 'recycle',
    'metal': 'recycle',
    'glass': 'recycle',
    'green-glass': 'recycle',
    'white-glass': 'recycle',
    'paper': 'recycle',
    'cardboard': 'recycle',
    'recycle': 'recycle',
    'recycling': 'recycle',

    #Organic category
    'organic': 'organic',
    'food': 'organic',
    'compost': 'organic',
    'biological': 'organic',

    #Waste category(everything else )
    'clothes': 'waste',
    'shoes': 'waste',
    'electronics': 'waste',
    'other': 'waste',
    'waste': 'waste'
}

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
        # Convert confidence to percentage if needed
        confidence_pct = confidence * 100 if confidence <= 1 else confidence
        
        update_data = {
            'filename': filename,
            'classification': classification,
            'confidence': round(confidence_pct, 2),
            'timestamp': datetime.now().isoformat(),
            'image_path': f"images/{filename}"
        }
        
        # Send to dashboard (assuming it's running on localhost:5001)
        response = requests.post(
            'http://localhost:5001/api/realtime_update',
            json=update_data,
            timeout=2
        )
        
        if response.status_code == 200:
            print(f"📡 Sent real-time update: {classification}")
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
        cv2.imwrite(filepath, frame)
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
                import threading
                def reset_cooldown():
                    global capture_cooldown
                    capture_cooldown = original_cooldown
                threading.Timer(5.0, reset_cooldown).start()
                
                return True
            else:
                # Save classification result for dashboard (valid classifications)
                confidence_value = confidence * 100 if confidence <= 1 else confidence
                save_classification_result(filename, classification, round(confidence_value, 2))
                print("!!!!moving motor brr please work please work why dont' you work")
                category = classificationMap[classification]
                stepper_motor_control.move(*stepper_motor_control.num_and_dir_steps[category])
                stepper_motor_control.move_solenoid()
                stepper_motor_control.move(stepper_motor_control.num_and_dir_steps[category][0],
                                           int(not stepper_motor_control.num_and_dir_steps[category][1]))
                # move motor to correct category

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
            import threading
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
        
    except KeyboardInterrupt as e:
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
    Main motion detection loop using OpenCV
    """
    global capture_triggered, last_capture_time, capture_cooldown, motion_detected_time, capture_delay, classification_in_progress
    
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Error: Could not open webcam")
        return
    
    # Set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    print("🎥 Starting motion detection...")
    print("💡 Press 'q' to quit, or Ctrl+C to stop")
    
    # Give camera time to adjust and learn background
    print("🔄 Learning background (5 seconds)...")
    for i in range(150):  # ~5 seconds at 30fps
        ret, frame = cap.read()
        if ret:
            detect_motion(frame)  # Initialize background model
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
            
            # Read frame from webcam only when not in classification
            ret, frame = cap.read()
            if not ret:
                print("❌ Error: Could not read frame from webcam")
                break
            
            # Detect motion
            motion_detected, motion_area = detect_motion(frame)
            
            if motion_detected and not capture_triggered and not classification_in_progress and motion_detected_time == 0:
                # First time motion is detected - start countdown
                motion_detected_time = current_time
                print(f"\n🔍 Motion detected! Area: {motion_area:.0f} pixels")
                print(f"⏳ Waiting {capture_delay} seconds before capture...")
            elif motion_detected_time != 0 and not capture_triggered and not classification_in_progress:
                # Check if capture delay has passed
                if current_time - motion_detected_time >= capture_delay:
                    print(f"\n📸 Capture delay complete! Triggering capture...")
                    
                    # Set flag to prevent multiple captures
                    capture_triggered = True
                    last_capture_time = current_time
                    motion_detected_time = 0  # Reset motion detection time
                    
                    # Capture and analyze using current frame
                    success = capture_and_analyze(frame)
                    
                    if success:
                        print(f"✅ Automatic capture and analysis completed!")
                        print(f"⏳ Cooldown: {capture_cooldown} seconds before next detection...")
                    else:
                        print("❌ Automatic capture failed!")
                    
                    print("=" * 50)
                    
                    # Reset flag
                    capture_triggered = False
                else:
                    # Still in capture delay period - show countdown
                    remaining = capture_delay - (current_time - motion_detected_time)
                    print(f"\r⏳ Capturing in: {remaining:.1f}s", end="", flush=True)
            elif not classification_in_progress:
                # No motion detected, reset motion detection time only if we're not in capture delay period
                if motion_detected_time != 0 and current_time - motion_detected_time < capture_delay:
                    # Still in capture delay period, don't reset - continue countdown
                    remaining = capture_delay - (current_time - motion_detected_time)
                    print(f"\r⏳ Capturing in: {remaining:.1f}s", end="", flush=True)
                else:
                    # No motion and not in capture delay period, reset
                    if motion_detected_time != 0:
                        motion_detected_time = 0
                    print(f"\r⏳ No motion detected (area: {motion_area:.0f})", end="", flush=True)
            
            # Show live feed (optional - comment out if you don't want to see the video)
            # cv2.imshow('Motion Detection', frame)
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break
            
            time.sleep(0.033)  # ~30fps
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping motion detection...")
    finally:
        cap.release()
        cv2.destroyAllWindows()

def main():
    print("🚀 Starting SmartSort Motion-Based Auto-Capture (Dashboard Integrated)")
    print("=" * 70)
    print("📋 Features:")
    print("  • Motion detection using background subtraction")
    print("  • Automatic capture when motion detected")
    print("  • Instant classification after capture")
    print("  • Runs classification model on captured images")
    print("  • Dashboard integration - results saved to JSON")
    print("  • 5-second cooldown between captures")
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
    stepper_motor_control.initialize_gpio()
    try:
        # Start motion detection loop
        motion_detection_loop()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping motion detection...")
        GPIO.cleanup()
    #except Exception as e:
    #    print(f"❌ Error: {e}")
    print("✅ Motion detection stopped")

if __name__ == "__main__":
    print("running main...")
    main()
