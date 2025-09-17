import time
import os
import numpy as np
from datetime import datetime
from picamera import PiCamera
from picamera.array import PiRGBArray
from inference_sdk import InferenceHTTPClient

# Global variables for motion detection
frame_count = 0
capture_triggered = False
classification_in_progress = False
motion_threshold = 5000000  # Adjusted for sum of pixel differences
min_motion_frames = 5
motion_frame_count = 0
last_capture_time = 0
capture_cooldown = 5.0
motion_detected_time = 0
capture_delay = 1.0

def capture_and_analyze(camera):
    global frame_count, classification_in_progress

    frame_count += 1
    classification_in_progress = True

    if not os.path.exists('detected_images'):
        os.makedirs('detected_images')

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"detected_images/detection_{timestamp}_{frame_count}.jpg"

    try:
        print(f"\n📸 Capturing image with PiCamera...")
        camera.capture(filename)
        print(f"✅ Picture saved: {filename}")

        print("🔄 Running classification inference on captured image...")
        client = InferenceHTTPClient(
            api_url="https://serverless.roboflow.com",
            api_key="Mqg6MjfPG888hkIAilqR"
        )
        result = client.run_workflow(
            workspace_name="smartsort-vfpxc",
            workflow_id="smartsort-classify-simple-v3",
            images={"image": filename},
            use_cache=True
        )

        if result:
            print(f"📦 Classification Results for {filename}:")
            if isinstance(result, list) and len(result) > 0:
                model_predictions = result[0].get('model_predictions', {})
                predictions = model_predictions.get('predictions', [])
                if predictions:
                    first_prediction = predictions[0]
                    class_name = first_prediction.get('class', 'Unknown')
                    confidence = first_prediction.get('confidence', 0)
                    confidence_pct = confidence * 100 if isinstance(confidence, (int, float)) else confidence
                    print(f"   🎯 {class_name} (confidence: {confidence_pct:.1f}%)")
                else:
                    print("   ❌ No predictions found")
            elif isinstance(result, dict):
                if 'predictions' in result:
                    predictions = result['predictions']
                    if predictions:
                        first_prediction = predictions[0]
                        class_name = first_prediction.get('class', first_prediction.get('class_name', 'Unknown'))
                        confidence = first_prediction.get('confidence', 0)
                        confidence_pct = confidence * 100 if isinstance(confidence, (int, float)) else confidence
                        print(f"   🎯 {class_name} (confidence: {confidence_pct:.1f}%)")
                    else:
                        print("   ❌ No predictions found")
                else:
                    print(f"   ❌ Unexpected result format: {result}")
            else:
                print(f"   ❌ Unexpected result type: {type(result)}")
        else:
            print("❌ No classification results for captured image")

        classification_in_progress = False
        return True

    except Exception as e:
        print(f"❌ Error capturing/analyzing image: {e}")
        classification_in_progress = False
        return False

def detect_motion(prev_frame, curr_frame):
    global motion_frame_count, motion_threshold, min_motion_frames

    # Convert to grayscale for motion detection
    prev_gray = np.dot(prev_frame[...,:3], [0.2989, 0.5870, 0.1140])
    curr_gray = np.dot(curr_frame[...,:3], [0.2989, 0.5870, 0.1140])

    # Compute absolute difference and sum
    diff = np.abs(curr_gray - prev_gray)
    motion_score = np.sum(diff)

    if motion_score > motion_threshold:
        motion_frame_count += 1
        if motion_frame_count >= min_motion_frames:
            motion_frame_count = 0
            return True, motion_score
    else:
        motion_frame_count = 0

    return False, motion_score

def motion_detection_loop():
    global capture_triggered, last_capture_time, capture_cooldown, motion_detected_time, capture_delay, classification_in_progress

    camera = PiCamera()
    camera.resolution = (640, 480)
    camera.framerate = 10
    raw_capture = PiRGBArray(camera, size=(640, 480))

    print("🎥 Starting motion detection with PiCamera (no OpenCV)...")
    print("💡 Press Ctrl+C to stop")

    # Warm up camera
    time.sleep(2)
    prev_frame = None

    try:
        for frame in camera.capture_continuous(raw_capture, format="rgb", use_video_port=True):
            current_time = time.time()
            curr_frame = frame.array

            if prev_frame is None:
                prev_frame = np.copy(curr_frame)
                raw_capture.truncate(0)
                continue

            # Cooldown
            if current_time - last_capture_time < capture_cooldown:
                print(f"\r⏳ Cooldown: {capture_cooldown - (current_time - last_capture_time):.1f}s remaining", end="", flush=True)
                raw_capture.truncate(0)
                continue

            if classification_in_progress:
                print(f"\r🔄 Classification in progress...", end="", flush=True)
                raw_capture.truncate(0)
                time.sleep(0.5)
                continue

            # Detect motion
            motion_detected, motion_score = detect_motion(prev_frame, curr_frame)

            if motion_detected and not capture_triggered and not classification_in_progress and motion_detected_time == 0:
                motion_detected_time = current_time
                print(f"\n🔍 Motion detected! Score: {motion_score:.0f}")
                print(f"⏳ Waiting {capture_delay} seconds before capture...")
            elif motion_detected_time != 0 and not capture_triggered and not classification_in_progress:
                if current_time - motion_detected_time >= capture_delay:
                    print(f"\n📸 Capture delay complete! Triggering capture...")
                    capture_triggered = True
                    last_capture_time = current_time
                    motion_detected_time = 0
                    success = capture_and_analyze(camera)
                    if success:
                        print(f"✅ Automatic capture and analysis completed!")
                        print(f"⏳ Cooldown: {capture_cooldown} seconds before next detection...")
                    else:
                        print("❌ Automatic capture failed!")
                    print("=" * 50)
                    capture_triggered = False
                else:
                    remaining = capture_delay - (current_time - motion_detected_time)
                    print(f"\r⏳ Capturing in: {remaining:.1f}s", end="", flush=True)
            elif not classification_in_progress:
                if motion_detected_time != 0 and current_time - motion_detected_time < capture_delay:
                    remaining = capture_delay - (current_time - motion_detected_time)
                    print(f"\r⏳ Capturing in: {remaining:.1f}s", end="", flush=True)
                else:
                    if motion_detected_time != 0:
                        motion_detected_time = 0
                    print(f"\r⏳ No motion detected (score: {motion_score:.0f})", end="", flush=True)

            prev_frame = np.copy(curr_frame)
            raw_capture.truncate(0)
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n🛑 Stopping motion detection...")
    finally:
        camera.close()

def main():
    print("🚀 Starting SmartSort PiCamera Motion-Based Auto-Capture (No OpenCV)")
    print("=" * 60)
    print("📋 Features:")
    print("  • PiCamera integration for Raspberry Pi")
    print("  • Motion detection using NumPy frame differencing")
    print("  • Automatic capture when motion detected")
    print("  • Instant classification after capture")
    print("  • Runs classification model on captured images")
    print("  • 5-second cooldown between captures")
    print("=" * 60)
    print("⚙️  Motion Settings:")
    print(f"  • Motion threshold: {motion_threshold}")
    print(f"  • Min motion frames: {min_motion_frames}")
    print(f"  • Capture delay: {capture_delay} seconds")
    print(f"  • Capture cooldown: {capture_cooldown} seconds")
    print("=" * 60)

    try:
        motion_detection_loop()
    except KeyboardInterrupt:
        print("\n🛑 Stopping motion detection...")
    except Exception as e:
        print(f"❌ Error: {e}")
    print("✅ Motion detection stopped")

if __name__ == "__main__":
    main()
