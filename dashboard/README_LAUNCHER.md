# SmartSort System Launcher

## 🚀 Quick Start

Run the entire SmartSort system with one command:

```bash
python3 start_system.py
```

This will start both:

- **Flask Dashboard** (http://localhost:5001)
- **Detection System** (motion detection + AI classification)

## 📋 What It Does

1. **Starts Flask Dashboard** - Web interface for viewing results
2. **Starts Detection System** - Motion detection and AI classification
3. **Monitors Both Processes** - Automatically restarts if they crash
4. **Graceful Shutdown** - Press Ctrl+C to stop everything

## 🌐 Access Points

- **Dashboard**: http://localhost:5001
- **User Interface**: http://localhost:5001/user

## 🛑 Stopping the System

Press `Ctrl+C` to stop both processes gracefully.

## 🔧 Manual Control

If you prefer to run components separately:

```bash
# Terminal 1: Flask Dashboard
python3 app.py

# Terminal 2: Detection System
python3 integrated_auto_capture.py
```

## 📊 System Flow

1. **Detection System** detects motion → captures image → runs AI classification
2. **Flask Dashboard** serves the web interface and API
3. **User Interface** shows real-time classification results and guessing game
4. **Synchronized Timing** - Backend pauses during UI interaction

## 🎯 Features

- **Real-time Motion Detection**
- **AI Classification** (clothes, plastic, metal, etc.)
- **Interactive Guessing Game** (recycle, waste, organic)
- **Manual Override** options
- **Dashboard Analytics** with charts and statistics
- **Perfect Timing Synchronization** between backend and frontend
