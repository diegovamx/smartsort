from flask import Flask, render_template, jsonify, request, Response, send_file
from flask_socketio import SocketIO, emit
import json
import time
from datetime import datetime
import threading
import queue
import os
import cv2

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smartsort-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global data store for classification results
classification_results = []
results_queue = queue.Queue()

# Store the last 100 results for analytics
MAX_RESULTS = 100

# Global webcam capture
webcam_capture = None
webcam_lock = threading.Lock()

# Global variable to store latest detection results for video overlay
latest_detections = []
detections_lock = threading.Lock()

def get_webcam():
    """Get or create webcam capture"""
    global webcam_capture
    if webcam_capture is None:
        try:
            webcam_capture = cv2.VideoCapture(0)
            if not webcam_capture.isOpened():
                print("Failed to open webcam")
                return None
            print("Webcam opened successfully")
        except Exception as e:
            print(f"Error opening webcam: {e}")
            return None
    return webcam_capture

def draw_detections_on_frame(frame, detections):
    """Draw bounding boxes and labels on a frame"""
    if not detections:
        return frame
    
    for pred in detections:
        try:
            # Validate prediction data structure
            if not isinstance(pred, dict):
                print(f"Skipping invalid prediction format: {type(pred)} - {pred}")
                continue
            
            # Get prediction data with safe defaults
            class_name = pred.get('class', 'Unknown')
            confidence = pred.get('confidence', 0)
            
            # Skip if no class name
            if not class_name:
                continue
            
            # Get bounding box coordinates with validation
            x = pred.get('x', 0)
            y = pred.get('y', 0)
            width = pred.get('width', 0)
            height = pred.get('height', 0)
            
            # Skip if no valid coordinates
            if not all(isinstance(coord, (int, float)) for coord in [x, y, width, height]):
                continue
            
            # Convert to integer coordinates
            x1, y1 = int(x), int(y)
            x2, y2 = int(x + width), int(y + height)
            
            # Validate coordinates are within frame bounds
            frame_height, frame_width = frame.shape[:2]
            if x1 < 0 or y1 < 0 or x2 > frame_width or y2 > frame_height:
                continue
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Prepare label text
            confidence_pct = confidence if isinstance(confidence, (int, float)) else 0
            label = f"{class_name}: {confidence_pct:.1%}"
            
            # Get text size for background
            (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            
            # Draw label background
            cv2.rectangle(frame, (x1, y1 - text_height - 10), (x1 + text_width + 10, y1), (0, 255, 0), -1)
            
            # Draw label text
            cv2.putText(frame, label, (x1 + 5, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            
        except Exception as e:
            print(f"Error drawing detection: {e}")
            print(f"Prediction data: {pred}")
            continue
    
    return frame

def generate_mjpeg_stream():
    """Generate MJPEG stream from webcam with detection overlays"""
    webcam = get_webcam()
    if webcam is None:
        return
    
    while True:
        try:
            with webcam_lock:
                ret, frame = webcam.read()
                if not ret:
                    continue
                
                # Get latest detections for overlay
                with detections_lock:
                    current_detections = latest_detections.copy()
                
                # Draw detections on frame
                frame_with_detections = draw_detections_on_frame(frame, current_detections)
                
                # Encode frame to JPEG
                ret, buffer = cv2.imencode('.jpg', frame_with_detections, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if not ret:
                    continue
                
                # Yield frame data
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                
        except Exception as e:
            print(f"Error in video stream: {e}")
            break
        
        time.sleep(0.033)  # ~30 FPS

@app.route('/')
def dashboard():
    """Main dashboard page"""
    try:
        return render_template('dashboard.html')
    except Exception as e:
        print(f"Error rendering template: {e}")
        return f"Error: {e}", 500

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_mjpeg_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/analyzed_images/<filename>')
def serve_analyzed_image(filename):
    """Serve analyzed images from the analyzed_images directory"""
    try:
        image_path = os.path.join('analyzed_images', filename)
        if os.path.exists(image_path):
            return send_file(image_path, mimetype='image/jpeg')
        else:
            return "Image not found", 404
    except Exception as e:
        print(f"Error serving image {filename}: {e}")
        return "Error serving image", 500

@app.route('/api/results', methods=['GET'])
def get_results():
    """API endpoint to get recent classification results"""
    return jsonify({
        'results': classification_results[-20:],  # Last 20 results
        'total_count': len(classification_results),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """API endpoint to get analytics data"""
    if not classification_results:
        return jsonify({'error': 'No data available'})
    
    # Calculate analytics
    class_counts = {}
    confidence_avg = {}
    
    for result in classification_results:
        timestamp = result['timestamp']
        for pred in result['predictions']:
            class_name = pred['class']
            confidence = pred['confidence']
            
            if class_name not in class_counts:
                class_counts[class_name] = 0
                confidence_avg[class_name] = []
            
            class_counts[class_name] += 1
            confidence_avg[class_name].append(confidence)
    
    # Calculate average confidence for each class
    for class_name in confidence_avg:
        confidence_avg[class_name] = sum(confidence_avg[class_name]) / len(confidence_avg[class_name])
    
    return jsonify({
        'class_counts': class_counts,
        'confidence_averages': confidence_avg,
        'total_detections': sum(class_counts.values()),
        'unique_classes': len(class_counts)
    })

def clear_old_detections():
    """Clear old detections to avoid showing stale bounding boxes"""
    global latest_detections
    with detections_lock:
        latest_detections = []

def update_detections_for_video(predictions, result_type="classification"):
    """Update detections for video overlay based on result type"""
    global latest_detections
    
    try:
        with detections_lock:
            if result_type == "object_detection" and isinstance(predictions, list):
                # For detection models, validate and use the predictions
                valid_predictions = []
                for pred in predictions:
                    if isinstance(pred, dict) and 'class' in pred:
                        # Ensure required fields exist
                        if all(key in pred for key in ['x', 'y', 'width', 'height']):
                            valid_predictions.append(pred)
                        else:
                            print(f"Skipping prediction without coordinates: {pred}")
                    else:
                        print(f"Skipping invalid prediction format: {pred}")
                
                latest_detections = valid_predictions
                print(f"Updated video overlay with {len(valid_predictions)} valid detections")
            else:
                # For classification models, clear detections since no bounding boxes
                latest_detections = []
                print("Cleared video overlay (classification model)")
                
    except Exception as e:
        print(f"Error updating detections for video: {e}")
        latest_detections = []

@app.route('/api/submit', methods=['POST'])
def submit_result():
    """API endpoint for SmartSort script to submit results"""
    try:
        data = request.get_json()
        
        # Debug: Print received data structure
        print(f"Received data type: {type(data)}")
        print(f"Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        
        # Add timestamp if not present
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
        
        # Validate predictions data
        predictions = data.get('predictions', [])
        if predictions:
            print(f"Predictions type: {type(predictions)}")
            print(f"First prediction: {predictions[0] if predictions else 'None'}")
        
        # Add to results
        classification_results.append(data)
        
        # Keep only recent results
        if len(classification_results) > MAX_RESULTS:
            classification_results.pop(0)
        
        # Update detections for video overlay
        result_type = data.get('model_type', 'classification')
        update_detections_for_video(predictions, result_type)
        
        # Emit to connected clients via WebSocket
        socketio.emit('new_result', data)
        
        return jsonify({'status': 'success', 'message': 'Result received'})
    
    except Exception as e:
        print(f"Error in submit_result: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'results_count': len(classification_results)
    })

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print(f"Client connected: {request.sid}")
    emit('connected', {'data': 'Connected to SmartSort Dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print(f"Client disconnected: {request.sid}")

def cleanup_webcam():
    """Cleanup webcam resources"""
    global webcam_capture
    if webcam_capture:
        webcam_capture.release()
        print("Webcam released")

def detection_cleanup_worker():
    """Worker thread to periodically clear old detections"""
    while True:
        try:
            time.sleep(10)  # Clear detections every 10 seconds
            clear_old_detections()
        except Exception as e:
            print(f"Error in detection cleanup worker: {e}")
            break

def start_server():
    """Start the Flask server"""
    print("Starting SmartSort Analytics Dashboard...")
    print(f"Template directory: {app.template_folder}")
    print(f"Current working directory: {os.getcwd()}")
    print("Dashboard available at: http://localhost:8080")
    print("Live video stream available at: http://localhost:8080/video_feed")
    print("Bounding boxes will appear on video when using object detection models")
    
    # Start detection cleanup worker thread
    cleanup_thread = threading.Thread(target=detection_cleanup_worker, daemon=True)
    cleanup_thread.start()
    
    try:
        socketio.run(app, host='0.0.0.0', port=8080, debug=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
        cleanup_webcam()
    finally:
        cleanup_webcam()

if __name__ == '__main__':
    start_server()
