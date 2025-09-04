# SmartSort - AI-Powered Waste Classification with Analytics Dashboard

SmartSort is an intelligent waste classification system that uses AI to identify different types of waste and provides real-time analytics through a beautiful web dashboard.

## 🚀 Features

- **Real-time AI Classification**: Uses Roboflow models to classify waste in real-time
- **Web Analytics Dashboard**: Beautiful, responsive web interface showing live results
- **5-Second Intervals**: Configurable timing for classification frequency
- **Real-time Updates**: WebSocket-powered live data streaming
- **Statistics & Charts**: Visual analytics including detection distribution
- **Mobile Responsive**: Works on desktop, tablet, and mobile devices

## 🏗️ System Architecture

```
SmartSort Script (smartsort.py)
           ↓
    HTTP POST to Dashboard
           ↓
    Flask Web Server (web_server.py)
           ↓
    WebSocket → Real-time Dashboard
```

## 📋 Requirements

- Python 3.7+
- Webcam or camera module
- Roboflow API key
- Internet connection for model inference

## 🛠️ Installation

1. **Install Python dependencies:**

   ```bash
   pip3 install -r requirements.txt
   ```

2. **Configure your Roboflow API key** in `smartsort.py`

## 🚀 Quick Start

### Option 1: Automated Startup (Recommended)

```bash
python3 start_dashboard.py
```

### Option 2: Manual Startup

1. **Start the dashboard:**

   ```bash
   python3 web_server.py
   ```

2. **In a new terminal, run SmartSort:**

   ```bash
   python3 smartsort.py
   ```

3. **Open your browser** to `http://localhost:8080`

## 📊 Dashboard Features

### Live Statistics

- Total detections
- Unique classes detected
- Average confidence scores
- Last update timestamp

### Detection Distribution Chart

- Doughnut chart showing class distribution
- Real-time updates as new detections occur

### Recent Results

- Live feed of classification results
- Frame numbers and timestamps
- Confidence scores for each prediction

## ⚙️ Configuration

### SmartSort Script (`smartsort.py`)

- **Detection Interval**: Change `detection_interval = 5.0` for different timing
- **Model ID**: Update `model_id` to use different Roboflow models
- **Camera Source**: Modify `video_reference` for different video sources

### Dashboard (`web_server.py`)

- **Port**: Change port 8080 if needed
- **Host**: Modify host binding for network access
- **Data Retention**: Adjust `MAX_RESULTS` for memory usage

## 🌐 Network Access

To access the dashboard from other devices on your network:

1. **Find your IP address:**

   ```bash
   ifconfig  # macOS/Linux
   ipconfig  # Windows
   ```

2. **Access from other devices:**
   ```
   http://YOUR_IP_ADDRESS:8080
   ```

## 📱 Raspberry Pi Deployment

Perfect for IoT waste sorting projects:

1. **Install on Pi:**

   ```bash
   sudo apt update
   sudo apt install python3-pip python3-opencv
   pip3 install -r requirements.txt
   ```

2. **Run headless:**

   ```bash
   python3 web_server.py &
   python3 smartsort.py
   ```

3. **Access from any device** on your network

## 🔧 Troubleshooting

### Dashboard won't start

- Check if port 8080 is available
- Verify all dependencies are installed
- Check console for error messages

### No data in dashboard

- Ensure SmartSort script is running
- Check network connectivity
- Verify API endpoints are working

### Camera issues

- Check camera permissions
- Try different `video_reference` values
- Verify camera is not in use by other applications

## 📈 Future Enhancements

- **Data Export**: CSV/JSON export of results
- **Historical Analysis**: Long-term trend analysis
- **Image Storage**: Save classified images
- **Alert System**: Notifications for specific classes
- **Multi-Camera Support**: Multiple camera feeds
- **Database Integration**: Persistent data storage

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve SmartSort!

## 📄 License

This project is open source and available under the MIT License.

---

**Happy Sorting! 🗑️♻️🌱**
