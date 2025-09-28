// User Interface JavaScript - Only runs when backend is active

let isScanning = false;
let classificationTimeout = null;
let guessingTimer = null;
let currentTimer = 5;
let userGuess = null;
let actualClassification = null;
let actualConfidence = null;
let lastProcessedTimestamp = null;
let pollingInterval = null;
let backendActive = false;
let cameraStream = null;

// Initialize the interface only if backend is running
document.addEventListener("DOMContentLoaded", function () {
  initializeCamera();
  checkBackendAndShowComponent();
  
  // Start continuous system monitoring
  startSystemMonitoring();
  
  // Listen for refresh signal from backend
  if (typeof io !== 'undefined') {
    const socket = io();
    
    socket.on('connect', function() {
      console.log('🔌 WebSocket connected');
    });
    
    socket.on('refresh_page', function(data) {
      console.log('🔄 Received refresh signal from backend:', data.message);
      console.log('🔄 Data received:', data);
      // Just refresh without showing any message
      // Refresh the page after a short delay
      setTimeout(() => {
        window.location.reload();
      }, 2000);
    });
    
    socket.on('disconnect', function() {
      console.log('🔌 WebSocket disconnected');
    });
  } else {
    console.warn('⚠️ Socket.IO not available - using polling fallback');
    // Fallback: poll for refresh signal
    checkForRefreshSignal();
  }
});

// Initialize camera feed
async function initializeCamera() {
  try {
    const video = document.getElementById('camera-feed');
    if (!video) return;
    
    console.log('📹 Initializing camera...');
    
    // Try different camera configurations for USB cameras
    let constraints = [
      // Try with specific resolution first
      {
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          frameRate: { ideal: 30 }
        }
      },
      // Fallback to any resolution
      {
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          frameRate: { ideal: 30 }
        }
      },
      // Fallback to basic video
      {
        video: true
      }
    ];
    
    let cameraStream = null;
    let lastError = null;
    
    // Try each constraint until one works
    for (let i = 0; i < constraints.length; i++) {
      try {
        console.log(`📹 Trying camera constraint ${i + 1}/${constraints.length}...`);
        cameraStream = await navigator.mediaDevices.getUserMedia(constraints[i]);
        console.log(`✅ Camera constraint ${i + 1} successful!`);
        break;
      } catch (error) {
        console.log(`❌ Camera constraint ${i + 1} failed:`, error.message);
        lastError = error;
        continue;
      }
    }
    
    if (!cameraStream) {
      throw lastError || new Error('No camera constraints worked');
    }
    
    // Set up the video element
    video.srcObject = cameraStream;
    
    // Wait for video to load
    video.onloadedmetadata = function() {
      console.log('📹 Video metadata loaded');
      video.play().then(() => {
        console.log('📹 Camera playing successfully');
      }).catch(error => {
        console.error('❌ Video play failed:', error);
      });
    };
    
    // Handle video errors
    video.onerror = function(error) {
      console.error('❌ Video error:', error);
    };
    
    console.log('📹 Camera initialized successfully');
    
  } catch (error) {
    console.error('❌ Camera initialization failed:', error);
    console.log('💡 Make sure:');
    console.log('   - Camera is connected and not being used by another app');
    console.log('   - Browser has camera permissions');
    console.log('   - Try refreshing the page');
    
    // Retry camera initialization after a delay
    console.log('🔄 Retrying camera initialization in 3 seconds...');
    setTimeout(() => {
      initializeCamera();
    }, 3000);
  }
}

// Stop camera when page unloads
window.addEventListener('beforeunload', function() {
  if (cameraStream) {
    cameraStream.getTracks().forEach(track => track.stop());
  }
});

// Hide camera feed
function hideCameraFeed() {
  const cameraContainer = document.querySelector(".camera-feed-container");
  if (cameraContainer) {
    cameraContainer.style.display = "none";
  }
  
  // Hide scan overlay when camera is hidden
  const scanOverlay = document.querySelector('.scan-overlay');
  if (scanOverlay) {
    scanOverlay.style.display = 'none';
  }
}

// Show camera feed
function showCameraFeed() {
  console.log('📹 showCameraFeed() called');
  const cameraContainer = document.querySelector(".camera-feed-container");
  if (cameraContainer) {
    cameraContainer.style.display = "block";
    console.log('📹 Camera container shown');
  } else {
    console.error('❌ Camera container not found!');
  }
  
  // Show scan overlay when camera is displayed
  const scanOverlay = document.querySelector('.scan-overlay');
  if (scanOverlay) {
    scanOverlay.style.display = 'block';
    console.log('📹 Scan overlay shown');
  } else {
    console.error('❌ Scan overlay not found!');
  }
  
  updateStatus("ready", "Ready to Scan", "Scan Trash");
}

// Show processing component
function showProcessingComponent() {
  const processingContainer = document.getElementById("processing-container");
  if (processingContainer) {
    processingContainer.style.display = "block";
  }
}

// Hide processing component
function hideProcessingComponent() {
  const processingContainer = document.getElementById("processing-container");
  if (processingContainer) {
    processingContainer.style.display = "none";
  }
}

// Update processing status
function updateProcessingStatus(type, title, message) {
  const processingIcon = document.getElementById("processing-icon");
  const processingTitle = document.getElementById("processing-title");
  const processingMessage = document.getElementById("processing-message");

  if (processingIcon) {
    // Find the icon element inside the processing-icon div
    const iconElement = processingIcon.querySelector('i');
    if (iconElement) {
      iconElement.className = `fas ${getStatusIcon(type)}`;
    }
  }
  if (processingTitle) processingTitle.textContent = title;
  if (processingMessage) processingMessage.textContent = message;
}

// Fallback polling mechanism for refresh signal
function checkForRefreshSignal() {
  setInterval(async () => {
    try {
      const response = await fetch('/api/system_status');
      if (response.ok) {
        const data = await response.json();
        // If system is ready and detection is active, refresh the page
        if (data.system_ready && data.detection_active) {
          console.log('🔄 Polling detected system ready - refreshing page');
          showRefreshMessage();
          setTimeout(() => {
            window.location.reload();
          }, 2000);
        }
      }
    } catch (error) {
      // Ignore errors in polling
    }
  }, 1000); // Check every second
}

function showRefreshMessage() {
  document.body.innerHTML = `
    <div style="display: flex; justify-content: center; align-items: center; min-height: 100vh; background: linear-gradient(135deg, #f8f9fa, #e9ecef);">
      <div style="text-align: center; background: white; padding: 2rem; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
        <div style="font-size: 3rem; color: #28a745; margin-bottom: 1rem;">🔄</div>
        <h2 style="color: #2c3e50; margin-bottom: 1rem;">System Ready!</h2>
        <p style="color: #6c757d;">Refreshing page...</p>
      </div>
    </div>
  `;
}

async function checkBackendAndShowComponent() {
  console.log('🔍 Checking backend and system status...');
  
  try {
    // Check if system is ready
    const response = await fetch('/api/system_status');
    console.log('📡 System status response:', response.status);
    
    if (response.ok) {
      const data = await response.json();
      console.log('📊 System status data:', data);
      
      // Check if system is ready OR if detection is active (meaning system is running)
      if (data.system_ready || data.detection_active) {
        console.log('✅ System ready detected - showing camera feed');
        // System is ready - show the component and initialize
        backendActive = true;
        showUserInterface();
        initializeInterface();
        startRealTimeUpdates();
        updateStatus("ready", "Ready to Scan", "Scan Trash");
        return;
      } else {
        console.log('❌ System not ready - system_ready:', data.system_ready, 'detection_active:', data.detection_active);
        throw new Error('System not ready');
      }
    } else {
      console.log('❌ Backend not responding with status:', response.status);
      throw new Error('Backend not responding');
    }
  } catch (error) {
    console.log('⚠️ Primary check failed:', error.message);
    
    // Try fallback check first
    console.log('🔄 Trying fallback check...');
    const fallbackSuccess = await checkSystemReadinessFallback();
    if (fallbackSuccess) {
      console.log('✅ Fallback check succeeded');
      return; // Fallback worked, we're done
    }
    
    console.log('❌ Both primary and fallback checks failed');
    
    // Try one more aggressive fallback - just check if backend is reachable
    try {
      const testResponse = await fetch('/api/detection_status');
      if (testResponse.ok) {
        console.log('🚀 Backend is reachable - showing interface anyway');
        backendActive = true;
        showUserInterface();
        initializeInterface();
        startRealTimeUpdates();
        updateStatus("ready", "Ready to Scan", "Scan Trash");
        return;
      }
    } catch (testError) {
      console.log('❌ Backend not reachable at all');
    }
    
    // System not ready - show initializing overlay and retry
    backendActive = false;
    showInitializingOverlay();
    console.log('System not ready:', error.message);
    
    // Retry every 2 seconds until system is ready
    setTimeout(() => {
      checkBackendAndShowComponent();
    }, 2000);
  }
}

// Fallback check for system readiness
async function checkSystemReadinessFallback() {
  try {
    console.log('🔄 Fallback: Checking /api/latest_classification...');
    // Try to check if we can reach the backend at all
    const response = await fetch('/api/latest_classification');
    console.log('🔄 Fallback response status:', response.status);
    
    if (response.ok) {
      const data = await response.json();
      console.log('🔄 Fallback data:', data);
      
      // If we can get a response, the system is probably ready
      if (data.detection_active !== false) {
        console.log('✅ Fallback detected system ready');
        backendActive = true;
        showUserInterface();
        initializeInterface();
        startRealTimeUpdates();
        updateStatus("ready", "Ready to Scan", "Scan Trash");
        return true;
      } else {
        console.log('❌ Fallback: detection_active is false');
      }
    } else {
      console.log('❌ Fallback: Response not ok:', response.status);
    }
  } catch (error) {
    console.log('❌ Fallback check failed:', error.message);
  }
  return false;
}

function showUserInterface() {
  // Show the main container
  const mainContainer = document.querySelector('.container');
  if (mainContainer) {
    mainContainer.style.display = 'block';
  }
  
  // Show all interface elements
  const statusCard = document.querySelector('.status-card');
  if (statusCard) {
    statusCard.style.display = 'block';
  }
}

function hideUserInterface() {
  // Hide the main container completely
  const mainContainer = document.querySelector('.container');
  if (mainContainer) {
    mainContainer.style.display = 'none';
  }
}

function showWaitingForSystem() {
  // Show waiting message while system initializes
  const body = document.body;
  body.innerHTML = `
    <div class="offline-container">
      <div class="offline-card">
        <div class="offline-icon">
          <i class="fas fa-spinner fa-spin"></i>
        </div>
        <h2>System Initializing</h2>
        <p>Please wait while the detection system starts up...</p>
        <div class="offline-instructions">
          <h4>System Setup:</h4>
          <ol>
            <li>Camera learning background (10 seconds)</li>
            <li>Frontend connecting (5 seconds)</li>
            <li><strong>Press ENTER in terminal to start</strong></li>
            <li>System will be ready automatically</li>
          </ol>
          <div class="alert alert-info mt-3">
            <i class="fas fa-info-circle"></i>
            <strong>Waiting for terminal input...</strong><br>
            Please press ENTER in the terminal where you ran the detection system.
          </div>
        </div>
        <div class="spinner">
          <div class="spinner-border text-primary" role="status">
            <span class="sr-only">Loading...</span>
          </div>
        </div>
      </div>
    </div>
  `;
  
  // Add waiting styles
  const style = document.createElement('style');
  style.textContent = `
    .offline-container {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      background: linear-gradient(135deg, #f8f9fa, #e9ecef);
      padding: 2rem;
    }
    
    .offline-card {
      background: white;
      border-radius: 20px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
      padding: 3rem;
      text-align: center;
      max-width: 500px;
      width: 100%;
    }
    
    .offline-icon {
      font-size: 4rem;
      color: #007bff;
      margin-bottom: 1rem;
    }
    
    .offline-card h2 {
      color: #2c3e50;
      margin-bottom: 1rem;
    }
    
    .offline-card p {
      color: #6c757d;
      margin-bottom: 2rem;
    }
    
    .offline-instructions {
      background: #f8f9fa;
      border-radius: 10px;
      padding: 1.5rem;
      margin: 2rem 0;
      text-align: left;
    }
    
    .offline-instructions h4 {
      color: #2c3e50;
      margin-bottom: 1rem;
    }
    
    .offline-instructions ol {
      color: #6c757d;
      margin: 0;
      padding-left: 1.5rem;
    }
    
    .spinner {
      margin-top: 2rem;
    }
    
    .spinner-border {
      width: 3rem;
      height: 3rem;
    }
  `;
  document.head.appendChild(style);
}

// Show system initializing overlay
function showInitializingOverlay() {
  const overlay = document.getElementById('initializing-overlay');
  console.log('🔄 Showing initializing overlay, overlay element:', overlay);
  if (overlay) {
    overlay.style.display = 'flex';
    console.log('✅ Initializing overlay shown');
  } else {
    console.error('❌ Initializing overlay element not found');
  }
}

// Hide system initializing overlay
function hideInitializingOverlay() {
  const overlay = document.getElementById('initializing-overlay');
  console.log('🔄 Hiding initializing overlay, overlay element:', overlay);
  if (overlay) {
    overlay.style.display = 'none';
    console.log('✅ Initializing overlay hidden');
  } else {
    console.error('❌ Initializing overlay element not found for hiding');
  }
}

// Continuous system monitoring
function startSystemMonitoring() {
  console.log('🔄 Starting continuous system monitoring...');
  
  setInterval(async () => {
    try {
      const response = await fetch('/api/system_status');
      if (response.ok) {
        const data = await response.json();
        console.log('📊 System monitoring check:', data);
        
        // Check if system is ready
        if (data.system_ready || data.detection_active) {
          console.log('✅ System active');
          if (!backendActive) {
            backendActive = true;
            showUserInterface();
            initializeInterface();
            startRealTimeUpdates();
            updateStatus("ready", "Ready to Scan", "Scan Trash");
          }
        }
      } else {
        console.log('❌ System monitoring: Backend not responding');
        backendActive = false;
      }
    } catch (error) {
      console.log('❌ System monitoring error:', error);
      backendActive = false;
    }
  }, 1000); // Check every 1 second
}

// Offline functionality removed

function initializeInterface() {
  // Only initialize if backend is active
  if (!backendActive) return;
  
  // Set initial state
  updateStatus(
    "ready",
    "Ready to Scan",
    "Position your item in front of the camera"
  );
  hideClassificationResult();
  hideGuessingInterface();
  
  // Show the camera feed automatically
  showCameraFeed();
}

function updateStatus(type, title, message) {
  // Don't show any status component - just log
  console.log(`Status update: ${type} - ${title}: ${message}`);
}

function getStatusIcon(type) {
  switch (type) {
    case "ready": return "fa-check-circle";
    case "scanning": return "fa-brain";
    case "complete": return "fa-check-circle";
    case "error": return "fa-exclamation-triangle";
    default: return "fa-question-circle";
  }
}

function showClassificationResult(classification, confidence) {
  if (!backendActive) return;
  
  // Ensure camera stays hidden during result display
  hideCameraFeed();
  
  const resultCard = document.querySelector(".classification-result");
  
  if (resultCard) {
    resultCard.style.display = "block";
    
    // Map the AI classification to simplified category
    const simplifiedClassification = mapClassificationToSimplified(classification);
    
    const badgeText = document.getElementById("badge-text");
    const confidenceFill = document.getElementById("confidence-fill");
    const confidenceText = document.getElementById("confidence-text");
    
    if (badgeText) {
      badgeText.textContent = simplifiedClassification;
      badgeText.className = `badge-text ${simplifiedClassification.toLowerCase()}`;
    }
    
    if (confidenceFill) {
      confidenceFill.style.width = `${confidence}%`;
    }
    
    if (confidenceText) {
      confidenceText.textContent = `Confidence: ${confidence.toFixed(2)}%`;
    }
  }
}

function hideClassificationResult() {
  const resultCard = document.querySelector(".classification-result");
  
  if (resultCard) resultCard.style.display = "none";
  // Camera will be shown by resetToReady() function
}

function hideGuessingInterface() {
  const guessingInterface = document.querySelector(".guessing-interface");
  if (guessingInterface) {
    guessingInterface.style.display = "none";
  }
}

function resetToReady() {
  if (!backendActive) return;
  
  updateStatus("ready", "Ready to Scan", "Scan Trash");
  hideClassificationResult();
  hideGuessingInterface();
  showCameraFeed(); // Show camera feed again after classification results
  isScanning = false;
  actualClassification = null;
  actualConfidence = null;
  userGuess = null;
  // Don't reset lastProcessedTimestamp here - let it be reset by new classifications
}

function handleNewClassification(data) {
  if (!backendActive) return;
  
  actualClassification = data.classification;
  actualConfidence = data.confidence;
  
  // Check if classification is Unknown
  if (actualClassification === "Unknown") {
    // Show unknown prompt and reset to camera
    showUnknownPrompt();
    return;
  }
  
  // Hide camera feed when processing starts
  hideCameraFeed();
  
  // Show processing component
  showProcessingComponent();
  
  // Show processing without timer
  updateProcessingStatus("scanning", "Processing Classification", "Running AI inference...");
  
  // Wait 3 seconds then proceed
  setTimeout(() => {
    hideProcessingComponent();
    showGuessingInterface();
  }, 3000);
}

function showUnknownPrompt() {
  if (!backendActive) return;
  
  // Hide camera feed
  hideCameraFeed();
  
  // Show processing component with unknown message
  showProcessingComponent();
  updateProcessingStatus("scanning", "Unknown Object", "Please scan again with a clearer view");
  
  // Wait 3 seconds then return to camera
  setTimeout(() => {
    hideProcessingComponent();
    showCameraFeed();
    isScanning = false;
    actualClassification = null;
    actualConfidence = null;
    userGuess = null;
  }, 3000);
}

// Guessing functionality
function showGuessingInterface() {
  if (!backendActive) return;
  
  // Ensure camera is hidden during guessing
  hideCameraFeed();
  
  const guessingInterface = document.querySelector(".guessing-interface");
  
  if (guessingInterface) {
    guessingInterface.style.display = "block";
    startGuessingTimer();
  }
}

function startGuessingTimer() {
  if (!backendActive) return;
  
  currentTimer = 5;
  const timerText = document.getElementById("timer-text");
  if (timerText) timerText.textContent = currentTimer;
  
  guessingTimer = setInterval(() => {
    currentTimer--;
    if (timerText) timerText.textContent = currentTimer;
    
    if (currentTimer <= 0) {
      clearInterval(guessingTimer);
      guessingTimer = null;
      // Auto-select "Unknown" if no guess made
      makeGuess("Unknown");
    }
  }, 1000);
}

function makeGuess(guess) {
  if (!backendActive) return;
  
  userGuess = guess;
  clearInterval(guessingTimer);
  guessingTimer = null;
  
  // Show guess result
  showGuessResult(guess);
}

function showGuessResult(guess) {
  if (!backendActive) return;
  
  const guessingInterface = document.querySelector(".guessing-interface");
  const guessResult = document.querySelector(".guess-result");
  
  if (guessingInterface) guessingInterface.style.display = "none";
  if (guessResult) {
    guessResult.style.display = "block";
    
    // Map actual classification to simplified categories
    const actualSimplified = mapClassificationToSimplified(actualClassification);
    const isCorrect = guess === actualSimplified;
    
    const resultIcon = document.getElementById("guess-result-icon");
    const resultTitle = document.getElementById("guess-result-title");
    const resultMessage = document.getElementById("guess-result-message");
    const userGuessSpan = document.getElementById("user-guess");
    const actualGuessSpan = document.getElementById("actual-classification");
    
    if (resultIcon) {
      resultIcon.className = `result-icon ${isCorrect ? 'correct' : 'incorrect'}`;
      resultIcon.innerHTML = isCorrect ? '<i class="fas fa-check"></i>' : '<i class="fas fa-times"></i>';
    }
    
    if (resultTitle) {
      resultTitle.textContent = isCorrect ? 'Correct!' : 'Incorrect';
    }
    
    if (resultMessage) {
      resultMessage.textContent = isCorrect 
        ? `Great job! You correctly identified it as ${actualSimplified}.`
        : `Not quite. You guessed ${guess}, but it's actually ${actualSimplified}.`;
    }
    
    if (userGuessSpan) userGuessSpan.textContent = guess;
    if (actualGuessSpan) actualGuessSpan.textContent = actualSimplified;
  }
  
  // Show final classification result after 3 seconds
  setTimeout(() => {
    showFinalClassificationResult();
  }, 3000);
}

function mapClassificationToSimplified(classification) {
  // Map AI classifications to simplified 3-category system
  const classificationMap = {
    // Recycle category
    'plastic': 'recycle',
    'metal': 'recycle', 
    'glass': 'recycle',
    'green-glass': 'recycle',
    'white-glass': 'recycle',
    'paper': 'recycle',
    'cardboard': 'recycle',
    'recycle': 'recycle',
    'recycling': 'recycle',
    
    // Organic category  
    'organic': 'organic',
    'food': 'organic',
    'compost': 'organic',
    'biological': 'organic',
    
    // Waste category (everything else)
    'clothes': 'waste',
    'shoes': 'waste',
    'electronics': 'waste',
    'other': 'waste',
    'waste': 'waste'
  };
  
  // Keep Unknown as Unknown, don't map to any category
  if (classification.toLowerCase() === 'unknown') {
    return 'unknown';
  }
  
  return classificationMap[classification.toLowerCase()] || 'waste';
}

function showFinalClassificationResult() {
  if (!backendActive) return;
  
  const guessResult = document.querySelector(".guess-result");
  const guessingInterface = document.querySelector(".guessing-interface");
  
  if (guessResult) guessResult.style.display = "none";
  if (guessingInterface) guessingInterface.style.display = "none";
  
  // Show the actual classification result
  showClassificationResult(actualClassification, actualConfidence);
  
  // Show cooldown period (3 seconds to match terminal)
  let cooldownTime = 3;
  const cooldownInterval = setInterval(() => {
    cooldownTime--;
    updateStatus("ready", "Ready to Scan", "Scan Trash");
    
    if (cooldownTime <= 0) {
      clearInterval(cooldownInterval);
      hideClassificationResult();
      isScanning = false; // Reset scanning flag
      resetToReady();
    }
  }, 1000);
}

function hideGuessResult() {
  const guessResult = document.querySelector(".guess-result");
  if (guessResult) guessResult.style.display = "none";
}

function startRealTimeUpdates() {
  if (!backendActive) return;
  
  // Clear any existing polling
  stopRealTimeUpdates();
  
  // Poll for new classifications every 500ms for real-time updates
  pollingInterval = setInterval(() => {
    if (!backendActive) {
      stopRealTimeUpdates();
      return;
    }
    
    fetch('/api/latest_classification')
      .then(response => {
        if (!response.ok) {
          throw new Error('Backend not responding');
        }
        return response.json();
      })
      .then(data => {
        // Debug: Log the data received from backend
        console.log('📡 Received from backend:', data);
        console.log('🔍 Current state - isScanning:', isScanning, 'actualClassification:', actualClassification);
        
        // Trigger on any valid classification (simplified logic)
        if (data.classification && 
            data.classification !== 'null' && 
            data.classification !== 'Unknown' &&
            data.detection_active &&
            !isScanning &&
            data.timestamp !== lastProcessedTimestamp) {
          
          console.log('🎯 New classification detected:', data.classification, data.confidence, 'at', data.timestamp);
          lastProcessedTimestamp = data.timestamp;
          isScanning = true; // Set scanning flag to prevent duplicate triggers
          handleNewClassification(data);
        } else {
          console.log('❌ Classification not triggered - classification:', data.classification, 'detection_active:', data.detection_active, 'isScanning:', isScanning, 'timestamp:', data.timestamp, 'lastProcessed:', lastProcessedTimestamp);
        }
      })
      .catch(error => {
        console.error('Error polling for classifications:', error);
        // Backend went offline - stop everything
        backendActive = false;
        stopRealTimeUpdates();
        showOfflineState();
      });
  }, 500);
}

function stopRealTimeUpdates() {
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
    console.log('Stopped real-time updates polling');
  }
}

// Manual override functions
function manualOverride() {
  if (!backendActive) return;
  
  const overrideOptions = document.getElementById('override-options');
  if (overrideOptions) {
    overrideOptions.style.display = 'block';
  }
}

function showOverrideOptions() {
  if (!backendActive) return;
  
  const overrideOptions = document.getElementById('override-options');
  if (overrideOptions) {
    overrideOptions.style.display = 'block';
  }
}

async function selectOverride(classification) {
  if (!backendActive) return;
  
  // Hide the override options
  const overrideOptions = document.getElementById('override-options');
  if (overrideOptions) {
    overrideOptions.style.display = 'none';
  }
  
  // Update the classification result with the manual selection
  const badgeText = document.getElementById('badge-text');
  const confidenceFill = document.getElementById('confidence-fill');
  const confidenceText = document.getElementById('confidence-text');
  
  // Update classification
  if (badgeText) {
    badgeText.textContent = classification;
    badgeText.className = `badge-text ${classification.toLowerCase()}`;
  }
  
  // Set confidence to 100% for manual override
  if (confidenceFill) {
    confidenceFill.style.width = '100%';
  }
  if (confidenceText) {
    confidenceText.textContent = 'Confidence: 100.00% (Manual Override)';
  }
  
  // Send manual override to backend
  try {
    const response = await fetch('/api/manual_override', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        classification: classification,
        confidence: 100.0,
        timestamp: new Date().toISOString()
      })
    });
    
    const result = await response.json();
    
    if (result.success) {
      console.log('✅ Manual override saved successfully');
      showAlert('Classification updated with manual override!', 'success');
    } else {
      console.error('❌ Failed to save manual override:', result.error);
      showAlert('Failed to save manual override. Please try again.', 'warning');
    }
  } catch (error) {
    console.error('❌ Error saving manual override:', error);
    showAlert('Error saving manual override. Please try again.', 'danger');
  }
  
  // Show cooldown period (3 seconds to match terminal)
  let cooldownTime = 3;
  const cooldownInterval = setInterval(() => {
    cooldownTime--;
    updateStatus("ready", "Ready to Scan", "Scan Trash");
    
    if (cooldownTime <= 0) {
      clearInterval(cooldownInterval);
      hideClassificationResult();
      isScanning = false; // Reset scanning flag
      resetToReady();
    }
  }, 1000);
}

function showAlert(message, type) {
  // Simple alert implementation
  const alertDiv = document.createElement('div');
  alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
  alertDiv.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  
  const container = document.querySelector('.container');
  if (container) {
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
      if (alertDiv.parentNode) {
        alertDiv.parentNode.removeChild(alertDiv);
      }
    }, 3000);
  }
}