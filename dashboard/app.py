from flask import Flask, render_template, jsonify, request, send_from_directory
import os
import json
import glob
from datetime import datetime
import re

app = Flask(__name__)

# Path to the detected images directory (relative to the dashboard folder)
DETECTED_IMAGES_PATH = "detected_images"

def get_classification_data():
    """
    Get all classification data from the detected images directory
    """
    classifications = []
    
    # Get all image files
    image_files = glob.glob(os.path.join(DETECTED_IMAGES_PATH, "*.jpg"))
    image_files.sort(key=os.path.getmtime, reverse=True)  # Sort by newest first
    
    for image_file in image_files:
        if os.path.exists(image_file):
            # Extract metadata from filename
            filename = os.path.basename(image_file)
            
            # Parse filename: detection_YYYYMMDD_HHMMSS_N.jpg
            match = re.match(r'detection_(\d{8})_(\d{6})_(\d+)\.jpg', filename)
            if match:
                date_str, time_str, frame_num = match.groups()
                
                # Parse date and time
                try:
                    date_obj = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                    formatted_date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    formatted_date = "Unknown"
                
                # Get file size
                file_size = os.path.getsize(image_file)
                file_size_mb = round(file_size / (1024 * 1024), 2)
                
                # For now, we'll use placeholder classification data
                # In a real implementation, you'd store this data in a database or JSON file
                classification_data = {
                    'id': len(classifications) + 1,
                    'filename': filename,
                    'image_path': f"images/{filename}",
                    'date': formatted_date,
                    'frame_number': int(frame_num),
                    'file_size_mb': file_size_mb,
                    'classification': 'Unknown',  # Placeholder
                    'confidence': 0.0,  # Placeholder
                    'timestamp': date_obj.timestamp() if 'date_obj' in locals() else 0
                }
                
                classifications.append(classification_data)
    
    return classifications

def load_classification_results():
    """
    Load classification results from a JSON file if it exists
    """
    results_file = os.path.join(DETECTED_IMAGES_PATH, "classification_results.json")
    if os.path.exists(results_file):
        try:
            with open(results_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_classification_result(filename, classification, confidence):
    """
    Save classification result to JSON file
    """
    results_file = os.path.join(DETECTED_IMAGES_PATH, "classification_results.json")
    
    # Load existing results
    results = load_classification_results()
    
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
        return True
    except:
        return False

@app.route('/')
def dashboard():
    """
    Main dashboard page
    """
    classifications = get_classification_data()
    results = load_classification_results()
    
    # Merge classification data with results
    for item in classifications:
        if item['filename'] in results:
            item['classification'] = results[item['filename']]['classification']
            item['confidence'] = results[item['filename']]['confidence']
    
    return render_template('dashboard.html', classifications=classifications)

@app.route('/api/classifications')
def api_classifications():
    """
    API endpoint to get all classifications
    """
    classifications = get_classification_data()
    results = load_classification_results()
    
    # Merge classification data with results
    for item in classifications:
        if item['filename'] in results:
            item['classification'] = results[item['filename']]['classification']
            item['confidence'] = results[item['filename']]['confidence']
    
    return jsonify(classifications)

@app.route('/api/classify', methods=['POST'])
def api_classify():
    """
    API endpoint to manually classify an image
    """
    data = request.get_json()
    filename = data.get('filename')
    classification = data.get('classification')
    confidence = data.get('confidence', 0.0)
    
    if filename and classification:
        success = save_classification_result(filename, classification, confidence)
        return jsonify({'success': success})
    
    return jsonify({'success': False, 'error': 'Missing filename or classification'})

@app.route('/images/<filename>')
def serve_image(filename):
    """
    Serve images from the detected_images directory
    """
    return send_from_directory(DETECTED_IMAGES_PATH, filename)

@app.route('/api/stats')
def api_stats():
    """
    API endpoint to get classification statistics
    """
    classifications = get_classification_data()
    results = load_classification_results()
    
    # Count classifications
    class_counts = {}
    total_classified = 0
    total_images = len(classifications)
    
    for item in classifications:
        if item['filename'] in results:
            classification = results[item['filename']]['classification']
            class_counts[classification] = class_counts.get(classification, 0) + 1
            total_classified += 1
    
    # Calculate average confidence
    confidences = [results[item['filename']]['confidence'] 
                  for item in classifications 
                  if item['filename'] in results and 'confidence' in results[item['filename']]]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    
    stats = {
        'total_images': total_images,
        'total_classified': total_classified,
        'classification_counts': class_counts,
        'average_confidence': round(avg_confidence, 2),
        'unclassified': total_images - total_classified
    }
    
    return jsonify(stats)

if __name__ == '__main__':
    # Create detected_images directory if it doesn't exist
    os.makedirs(DETECTED_IMAGES_PATH, exist_ok=True)
    
    print("🚀 Starting SmartSort Dashboard")
    print("=" * 50)
    print("📊 Dashboard Features:")
    print("  • View all captured images")
    print("  • See classification results")
    print("  • Manual classification interface")
    print("  • Statistics and analytics")
    print("=" * 50)
    print("🌐 Access the dashboard at: http://localhost:5001")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5001)
