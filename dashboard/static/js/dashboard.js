// SmartSort Dashboard JavaScript

let currentClassifications = [];
let currentFilename = '';
let classificationChart = null;

// Theme management
let currentTheme = localStorage.getItem('theme') || 'light';

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
    loadData();
    
    // Initialize theme
    applyTheme(currentTheme);
    
    // View mode toggle
    document.getElementById('grid-view').addEventListener('change', function() {
        if (this.checked) {
            document.getElementById('images-container').className = 'row';
        }
    });
    
    document.getElementById('list-view').addEventListener('change', function() {
        if (this.checked) {
            document.getElementById('images-container').className = 'row list-view';
        }
    });
});

function updateCurrentTime() {
    const now = new Date();
    const timeString = now.toLocaleString();
    document.getElementById('current-time').textContent = timeString;
}

async function loadData() {
    try {
        // Show loading state
        document.getElementById('images-container').innerHTML = '<div class="col-12"><div class="loading"><i class="fas fa-spinner"></i><br>Loading images...</div></div>';
        
        // Load classifications and stats
        const [classificationsResponse, statsResponse] = await Promise.all([
            fetch('/api/classifications'),
            fetch('/api/stats')
        ]);
        
        const classifications = await classificationsResponse.json();
        const stats = await statsResponse.json();
        
        currentClassifications = classifications;
        
        // Update statistics
        updateStats(stats);
        
        // Update classification breakdown
        updateClassificationBreakdown(stats.classification_counts);
        
        // Render images
        renderImages(classifications);
        
    } catch (error) {
        console.error('Error loading data:', error);
        document.getElementById('images-container').innerHTML = '<div class="col-12"><div class="alert alert-danger">Error loading data. Please try again.</div></div>';
    }
}

function updateStats(stats) {
    document.getElementById('total-images').textContent = stats.total_images;
    document.getElementById('total-classified').textContent = stats.total_classified;
    document.getElementById('unclassified').textContent = stats.unclassified;
    document.getElementById('avg-confidence').textContent = stats.average_confidence + '%';
}

function updateClassificationBreakdown(classifications) {
    const legendContainer = document.getElementById('classification-legend');
    
    if (!classifications || Object.keys(classifications).length === 0) {
        legendContainer.innerHTML = `
            <p class="text-muted text-center py-4">
                <i class="fas fa-chart-pie fa-2x mb-3 d-block opacity-50"></i>
                No classifications available
            </p>
        `;
        if (classificationChart) {
            classificationChart.destroy();
            classificationChart = null;
        }
        return;
    }
    
    const total = Object.values(classifications).reduce((sum, count) => sum + count, 0);
    
    // Create pie chart
    createPieChart(classifications, total);
    
    // Create legend
    let legendHtml = '<h6 class="mb-3 text-center">Classification Legend</h6>';
    for (const [classification, count] of Object.entries(classifications)) {
        const percentage = ((count / total) * 100).toFixed(1);
        legendHtml += `
            <div class="classification-item mb-2">
                <div class="d-flex align-items-center">
                    <div class="classification-dot me-2" style="width: 12px; height: 12px; border-radius: 50%; background-color: ${getClassificationColor(classification)};"></div>
                    <span class="classification-name flex-grow-1">${classification}</span>
                    <span class="classification-count">${count}</span>
                </div>
                <small class="text-muted ms-4">${percentage}%</small>
            </div>
        `;
    }
    
    legendContainer.innerHTML = legendHtml;
}

function getClassificationColor(classification) {
    const colors = {
        'plastic': '#3498db',
        'metal': '#95a5a6',
        'paper': '#4a7c59',
        'glass': '#17a2b8',
        'organic': '#f39c12',
        'clothes': '#e91e63',
        'electronics': '#9c27b0',
        'other': '#95a5a6',
        'unknown': '#95a5a6'
    };
    return colors[classification.toLowerCase()] || '#95a5a6';
}

function createPieChart(classifications, total) {
    const ctx = document.getElementById('classificationChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (classificationChart) {
        classificationChart.destroy();
    }
    
    const labels = Object.keys(classifications);
    const data = Object.values(classifications);
    const colors = labels.map(label => getClassificationColor(label));
    
    classificationChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderColor: '#ffffff',
                borderWidth: 2,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false // We'll use custom legend
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '60%',
            animation: {
                animateRotate: true,
                duration: 1000
            }
        }
    });
}

function renderImages(classifications) {
    const container = document.getElementById('images-container');
    
    if (classifications.length === 0) {
        container.innerHTML = '<div class="col-12"><div class="alert alert-info">No images found. Start the auto-capture script to begin collecting images.</div></div>';
        return;
    }
    
    let html = '';
    classifications.forEach(item => {
        const isListMode = document.getElementById('list-view').checked;
        
        html += `
            <div class="col-md-4 col-lg-3 mb-4">
                <div class="card image-card h-100">
                    <div class="position-relative">
                        <img src="${item.image_path}" 
                             class="card-img-top" 
                             alt="Detection ${item.frame_number}"
                             onclick="openImageModal('${item.filename}')">
                        <div class="classification-badge ${item.classification.toLowerCase()}">
                            ${item.classification}
                        </div>
                        <div class="image-overlay">
                            <div class="d-flex justify-content-between align-items-end">
                                <div>
                                    <h6 class="mb-1">Frame #${item.frame_number}</h6>
                                    <small>${item.date}</small>
                                </div>
                                <button class="btn btn-sm btn-outline-light" 
                                        onclick="openClassificationModal('${item.filename}', '${item.image_path}')">
                                    <i class="fas fa-edit"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="card-body">
                        <h6 class="card-title">Detection ${item.frame_number}</h6>
                        <p class="card-text text-muted small">
                            <i class="fas fa-calendar"></i> ${item.date}<br>
                            <i class="fas fa-file"></i> ${item.file_size_mb} MB
                        </p>
                        ${item.classification !== 'Unknown' ? `
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: ${item.confidence}%"></div>
                            </div>
                            <small class="text-muted">Confidence: ${item.confidence}%</small>
                        ` : `
                            <div class="alert alert-warning alert-sm mb-0">
                                <i class="fas fa-exclamation-triangle"></i> Not classified
                            </div>
                        `}
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function openImageModal(filename) {
    // Create a simple image modal
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">${filename}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body text-center">
                    <img src="../detected_images/${filename}" class="img-fluid" alt="${filename}">
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    modal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modal);
    });
}

function openClassificationModal(filename, imagePath) {
    currentFilename = filename;
    document.getElementById('modal-image').src = imagePath;
    document.getElementById('classification-select').value = '';
    document.getElementById('confidence-input').value = '95';
    
    const modal = new bootstrap.Modal(document.getElementById('classificationModal'));
    modal.show();
}

async function saveClassification() {
    const classification = document.getElementById('classification-select').value;
    const confidence = parseFloat(document.getElementById('confidence-input').value);
    
    if (!classification) {
        alert('Please select a classification');
        return;
    }
    
    try {
        const response = await fetch('/api/classify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                filename: currentFilename,
                classification: classification,
                confidence: confidence
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('classificationModal'));
            modal.hide();
            
            // Refresh data
            loadData();
            
            // Show success message
            showAlert('Classification saved successfully!', 'success');
        } else {
            showAlert('Error saving classification: ' + (result.error || 'Unknown error'), 'danger');
        }
    } catch (error) {
        console.error('Error saving classification:', error);
        showAlert('Error saving classification. Please try again.', 'danger');
    }
}

function refreshData() {
    loadData();
    showAlert('Data refreshed!', 'info');
}

function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 3000);
}

// Auto-refresh every 30 seconds
setInterval(loadData, 30000);

// Theme functions
function toggleTheme() {
    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
    applyTheme(currentTheme);
    localStorage.setItem('theme', currentTheme);
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    
    const themeToggle = document.getElementById('theme-toggle');
    if (theme === 'dark') {
        themeToggle.innerHTML = '<i class="fas fa-sun me-2"></i> Light';
    } else {
        themeToggle.innerHTML = '<i class="fas fa-moon me-2"></i> Dark';
    }
}
