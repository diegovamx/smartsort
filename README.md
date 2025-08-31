# SmartSort - Raspberry Pi Object Detection

This project uses Roboflow Inference to perform real-time object detection on a Raspberry Pi.

## Prerequisites

- Raspberry Pi 4 Model B or Raspberry Pi 5
- 64-bit Raspberry Pi OS (recommended: "Raspberry Pi OS with desktop and recommended software")
- Camera module or USB camera
- Roboflow account and API key

## Setup Instructions

### 1. Install Dependencies

Install the required packages manually:

```bash
# Install Python dependencies
pip install roboflow opencv-python inference-sdk

# Install inference CLI
pip install inference-cli

# Start inference server
inference server start
```

### 2. Configure Your Model

Edit `smartsort.py` and replace the placeholder values:

```python
pipeline = InferencePipeline(
    model_id="YOUR_PROJECT/YOUR_VERSION",  # Replace with your actual project ID and version
    api_key="YOUR_API_KEY",               # Replace with your Roboflow API key
)
```

### 3. Run the Application

```bash
python smartsort.py
```

## Performance Expectations

- **Raspberry Pi 4**: ~1 FPS with "Roboflow 3.0 Fast" models
- **Raspberry Pi 5**: ~4 FPS with "Roboflow 3.0 Fast" models

## Troubleshooting

### Camera Issues

If you get camera errors, try:

- Checking camera connections
- Running `sudo raspi-config` and enabling camera
- Using a different camera index: `cv2.VideoCapture(1)`

### Performance Issues

- Use smaller models for better performance
- Consider using a USB 3.0 camera for better frame rates
- Close other applications to free up resources

### Server Issues

If the inference server fails to start:

```bash
# Check if Docker is running
sudo systemctl status docker

# Restart Docker if needed
sudo systemctl restart docker

# Try manual container start
sudo docker run -d \
    --name inference-server \
    --read-only \
    -p 9001:9001 \
    --volume ~/.inference/cache:/tmp:rw \
    --security-opt="no-new-privileges" \
    --cap-drop="ALL" \
    --cap-add="NET_BIND_SERVICE" \
    roboflow/roboflow-inference-server-cpu:latest
```

## Controls

- **ESC key**: Exit the application
- The application will display real-time object detection results

## Next Steps

1. Replace the model_id with your actual Roboflow project details
2. Test with your camera
3. Customize the confidence threshold and visualization
4. Integrate with sorting mechanisms if needed
