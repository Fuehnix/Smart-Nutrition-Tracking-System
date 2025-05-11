// Add this function to your scan.html JavaScript
function showNotification(message, isSuccess = true) {
    // Remove any existing notification
    const existingNotification = document.querySelector('.custom-notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `custom-notification ${isSuccess ? 'success' : 'error'}`;
    
    notification.innerHTML = `
        <div class="notification-icon">
            ${isSuccess ? 
                '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>' : 
                '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>'
            }
        </div>
        <div class="notification-message">${message}</div>
        <button class="notification-close">×</button>
    `;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Add event listener for close button
    notification.querySelector('.notification-close').addEventListener('click', function() {
        notification.remove();
    });
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        if (document.body.contains(notification)) {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 500);
        }
    }, 5000);
}

const style = document.createElement('style');
style.innerHTML = `
    .custom-notification {
        position: fixed;
        top: 20px;
        right: 20px;
        display: flex;
        align-items: center;
        padding: 15px 20px;
        border-radius: 8px;
        max-width: 350px;
        z-index: 9999;
        animation: slide-in 0.3s ease-out;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .success {
        background-color: #dff8e5;
        color: #2e7d32;
        border-left: 4px solid #2e7d32;
    }
    
    .error {
        background-color: #fee8e7;
        color: #d32f2f;
        border-left: 4px solid #d32f2f;
    }
    
    .notification-icon {
        margin-right: 15px;
    }
    
    .notification-message {
        flex: 1;
        font-weight: 500;
    }
    
    .notification-close {
        background: none;
        border: none;
        font-size: 24px;
        cursor: pointer;
        color: inherit;
        padding: 0 0 0 15px;
        opacity: 0.7;
    }
    
    .notification-close:hover {
        opacity: 1;
    }
    
    .fade-out {
        animation: fade-out 0.5s ease-out forwards;
    }
    
    @keyframes slide-in {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes fade-out {
        from { opacity: 1; }
        to { opacity: 0; }
    }
`;
document.head.appendChild(style);

// Then replace alert calls in your event listeners with showNotification:
document.getElementById('scale-btn').addEventListener('click', function() {
    document.getElementById('loading').classList.remove('hidden');
    fetch('/api/trigger_scale')
        .then(response => response.json())
        .then(data => {
            document.getElementById('loading').classList.add('hidden');
            if (data.status === 'success') {
                showNotification(`Weight detected: ${data.weight}${data.unit}`, true);
            } else {
                showNotification('Could not connect to scale. Please try again.', false);
            }
        })
        .catch(error => {
            document.getElementById('loading').classList.add('hidden');
            showNotification('Error connecting to scale', false);
        });
});

document.getElementById('camera-btn').addEventListener('click', function () {
    document.getElementById('loading').classList.remove('hidden');

    fetch('/api/trigger_camera')
        .then(response => response.json())
        .then(data => {
            document.getElementById('loading').classList.add('hidden');

            // Always show image if returned
            const imgEl = document.getElementById('captured-image');
            if (data.image_url && imgEl) {
                imgEl.src = data.image_url + '?t=' + new Date().getTime(); // prevent caching
                imgEl.style.display = 'block';
            }

            // Always show panel
            document.getElementById('food-selection-panel').classList.add('active');

            if (data.status === 'success') {
                document.getElementById('food-name-input').value = data.food_name;
                document.getElementById('selected-food-info').innerText = data.food_name;
                showNotification(`Detected: ${data.food_name}`, true);

                setTimeout(() => {
                    window.location.href = data.redirect_url;
                }, 2000);
            } else {
                document.getElementById('selected-food-info').innerText = "No food recognized.";
                showNotification(data.message || 'Could not recognize food.', false);
            }
        })
        .catch(error => {
            document.getElementById('loading').classList.add('hidden');
            showNotification('Error connecting to camera', false);
        });
});

