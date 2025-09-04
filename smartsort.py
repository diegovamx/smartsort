# import the InferencePipeline interface
from inference import InferencePipeline
import time
import requests
import json
from datetime import datetime
import os

# Set environment variables to force CPU execution and avoid CoreML issues
os.environ['ONNXRUNTIME_PROVIDER_NAMES'] = 'CPUExecutionProvider'
os.environ['CORE_MODEL_PE_ENABLED'] = 'False'

# Global variables to track timing
last_detection_time = 0
detection_interval = 5.0  # 5 seconds
frame_count = 0

# Dashboard configuration
DASHBOARD_URL = "http://localhost:8080/api/submit"
DASHBOARD_ENABLED = True

def send_to_dashboard(result_data):
    """
    Send classification results to the dashboard
    """
    global DASHBOARD_ENABLED
    
    if not DASHBOARD_ENABLED:
        return
    
    try:
        # Prepare data for dashboard
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'frame_count': result_data.get('frame_count', frame_count),
            'predictions': result_data.get('predictions', [])
        }
        
        # Send to dashboard
        response = requests.post(
            DASHBOARD_URL,
            json=dashboard_data,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"✅ Data sent to dashboard successfully")
        else:
            print(f"⚠️  Dashboard response: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send to dashboard: {e}")
        # Disable dashboard if it's not available
        DASHBOARD_ENABLED = False
        print("Dashboard disabled - continuing with terminal output only")

def custom_classification_sink(result, video_frame):
    """
    Custom sink for classification results - shows results on video and prints to terminal every 5 seconds
    """
    global last_detection_time, frame_count
    
    current_time = time.time()
    frame_count += 1
    
    # Only print to terminal every 5 seconds
    if current_time - last_detection_time >= detection_interval:
        last_detection_time = current_time
        
        if result.get("predictions"):
            predictions = result["predictions"]
            
            # Prepare result data
            result_data = {
                'frame_count': frame_count,
                'timestamp': current_time,
                'predictions': predictions
            }
            
            # Send to dashboard
            send_to_dashboard(result_data)
            
            # Print detailed results to console
            print("\n" + "="*50)
            print(f"CLASSIFICATION RESULTS (Frame {frame_count}, Time: {current_time:.1f}s):")
            print("="*50)
            for i, pred in enumerate(predictions):
                class_name = pred.get("class", "Unknown")
                confidence = pred.get("confidence", 0)
                confidence_pct = confidence * 100
                print(f"{i+1:2d}. {class_name:20s} - {confidence_pct:5.1f}%")
            print("="*50)
        else:
            print(f"Frame {frame_count}: No predictions available")
    
    # Show countdown in terminal
    time_until_next = max(0, detection_interval - (current_time - last_detection_time))
    if time_until_next < 1:  # Only show when close to next detection
        print(f"Next classification in: {time_until_next:.1f}s")

# create an inference pipeline object
pipeline = InferencePipeline.init(
    # model_id="classification-waste/11",  # Classification model
     model_id="garbage-lzfii/4", # set the model id to a yolov8x model with in put size 1280
    video_reference=0, # set the video reference (source of video), it can be a link/path to a video file, an RTSP stream url, or an integer representing a device id (usually 0 for built in webcams)
    on_prediction=custom_classification_sink, # Use custom classification sink
    api_key="Mqg6MjfPG888hkIAilqR", # provide your roboflow api key for loading models from the roboflow api
)

print("Starting SmartSort classification...")
print("Point your webcam at objects to see classifications every 5 seconds")
print("Dashboard integration enabled - results will be sent to web interface")

# start the pipeline
pipeline.start()
# wait for the pipeline to finish
pipeline.join()