# SmartSort Dashboard

A web-based dashboard for viewing and managing SmartSort classification results.

## Features

- 📊 **Real-time Statistics**: View total images, classified count, and average confidence
- 🖼️ **Image Gallery**: Browse all captured images in grid or list view
- 🏷️ **Manual Classification**: Classify unclassified images manually
- 📈 **Analytics**: See classification breakdown and statistics
- 🔄 **Auto-refresh**: Dashboard updates automatically every 30 seconds
- 📱 **Responsive Design**: Works on desktop and mobile devices

## Installation

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Make sure the `detected_images` folder exists in the parent directory with captured images.

## Usage

1. Start the dashboard:

```bash
python app.py
```

2. Open your browser and go to: http://localhost:5000

3. The dashboard will automatically load all images from the `../detected_images` folder.

## API Endpoints

- `GET /` - Main dashboard page
- `GET /api/classifications` - Get all classification data
- `POST /api/classify` - Manually classify an image
- `GET /api/stats` - Get classification statistics

## File Structure

```
dashboard/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/
│   └── dashboard.html    # Main dashboard template
└── static/
    ├── css/
    │   └── dashboard.css # Custom styles
    └── js/
        └── dashboard.js  # Dashboard functionality
```

## Integration with Auto-Capture Script

The dashboard automatically reads images from the `../detected_images` folder that are created by the auto-capture script. It also reads classification results from a `classification_results.json` file in the same folder.

To integrate with your auto-capture script, make sure it saves classification results in this format:

```json
{
  "detection_20250911_142114_3.jpg": {
    "classification": "paper",
    "confidence": 57.1,
    "timestamp": "2025-09-11T14:21:14.123456"
  }
}
```

## Customization

- **Classification Types**: Edit the dropdown options in `dashboard.html`
- **Styling**: Modify `dashboard.css` for custom colors and layouts
- **Auto-refresh Interval**: Change the interval in `dashboard.js` (default: 30 seconds)
- **Image Path**: Update `DETECTED_IMAGES_PATH` in `app.py` if needed

## Troubleshooting

- **No images showing**: Make sure the `../detected_images` folder exists and contains image files
- **Classification not saving**: Check that the dashboard has write permissions to the detected_images folder
- **Port already in use**: Change the port in `app.py` (line with `app.run()`)
