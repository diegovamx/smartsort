import cv2
import time
from inference import InferencePipeline
import os

# Force CPU execution for macOS compatibility
os.environ['ONNXRUNTIME_PROVIDER_NAMES'] = 'CPUExecutionProvider'
os.environ['CORE_MODEL_PE_ENABLED'] = 'False'

# Global variables for timing control
last_detection_time = 0
detection_interval = 5.0  # seconds between detections
frame_count = 0

def custom_detection_sink(result, video_frame):
    """
    Custom sink for object detection results.
    Prints detection results to terminal every 5 seconds.
    """
    global last_detection_time, frame_count
    
    current_time = time.time()
    frame_count += 1
    
    # Check if it's time for a new detection analysis
    if current_time - last_detection_time >= detection_interval:
        print(f"\n🔍 === DETECTION ANALYSIS #{frame_count} ===")
        print(f"⏰ Time: {time.strftime('%H:%M:%S')}")
        
        if result and hasattr(result, 'predictions') and result.predictions:
            print(f"📦 Objects detected: {len(result.predictions)}")
            
            for i, prediction in enumerate(result.predictions):
                if hasattr(prediction, 'class_name'):
                    class_name = prediction.class_name
                elif hasattr(prediction, 'class'):
                    class_name = getattr(prediction, 'class')
                else:
                    class_name = "Unknown"
                
                # Get confidence score
                if hasattr(prediction, 'confidence'):
                    confidence = prediction.confidence
                else:
                    confidence = "N/A"
                
                # Get bounding box coordinates
                if hasattr(prediction, 'x') and hasattr(prediction, 'y'):
                    x = prediction.x
                    y = prediction.y
                else:
                    x, y = "N/A", "N/A"
                
                if hasattr(prediction, 'width') and hasattr(prediction, 'height'):
                    width = prediction.width
                    height = prediction.height
                else:
                    width, height = "N/A", "N/A"
                
                print(f"  {i+1}. {class_name}")
                print(f"     Confidence: {confidence}")
                print(f"     Position: ({x}, {y})")
                print(f"     Size: {width} x {height}")
                print()
        else:
            print("❌ No objects detected in this frame")
        
        # Update last detection time
        last_detection_time = current_time
        
        # Show countdown for next detection
        print(f"⏳ Next detection in {detection_interval} seconds...")
        print("=" * 50)
    
    # Show live countdown
    else:
        remaining = detection_interval - (current_time - last_detection_time)
        if frame_count % 30 == 0:  # Update every 30 frames (roughly every second)
            print(f"\r⏳ Next detection in {remaining:.1f}s...", end="", flush=True)

def main():
    print("🚀 Starting SmartSort Object Detection (Simple Version)")
    print("=" * 60)
    print("📋 Features:")
    print("  • Object detection every 5 seconds")
    print("  • Terminal output only (no dashboard)")
    print("  • Real-time countdown display")
    print("  • Detailed detection information")
    print("=" * 60)
    
    # Initialize the inference pipeline
    try:
        print("🔄 Initializing object detection model...")
        
        # Replace with your actual object detection model ID
        pipeline = InferencePipeline.init(
            model_id="recyclesorting/1",  # Your detection model
            video_render=False,  # No video rendering
            on_prediction=custom_detection_sink
        )
        
        print("✅ Model initialized successfully!")
        print("🎥 Starting webcam feed...")
        print("💡 Press Ctrl+C to stop")
        print()
        
        # Start the pipeline
        pipeline.start()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping detection...")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure you have a valid object detection model ID")
    finally:
        if 'pipeline' in locals():
            pipeline.stop()
        print("✅ Detection stopped")

if __name__ == "__main__":
    main()

