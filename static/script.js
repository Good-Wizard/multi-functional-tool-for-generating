function showError(message) {
    var errorContainer = document.getElementById('error-container');
    var errorMessage = document.getElementById('error-message');
    
    errorMessage.textContent = message;
    errorContainer.style.display = 'block';
}
