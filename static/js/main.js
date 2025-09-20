// Main JavaScript for Tourism Booking System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Date validation for booking forms
    const checkInInput = document.getElementById('check_in');
    const checkOutInput = document.getElementById('check_out');
    
    if (checkInInput && checkOutInput) {
        // Set minimum date to today
        const today = new Date().toISOString().split('T')[0];
        checkInInput.setAttribute('min', today);
        
        checkInInput.addEventListener('change', function() {
            const checkInDate = new Date(this.value);
            const nextDay = new Date(checkInDate);
            nextDay.setDate(nextDay.getDate() + 1);
            checkOutInput.setAttribute('min', nextDay.toISOString().split('T')[0]);
        });
    }

    // Search functionality
    const searchInput = document.getElementById('search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const hotelCards = document.querySelectorAll('.hotel-card');
            
            hotelCards.forEach(card => {
                const hotelName = card.querySelector('.card-title').textContent.toLowerCase();
                const hotelCity = card.querySelector('.hotel-location').textContent.toLowerCase();
                
                if (hotelName.includes(searchTerm) || hotelCity.includes(searchTerm)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

    // Room availability check
    function checkRoomAvailability() {
        const roomsInput = document.getElementById('rooms');
        const availableRooms = parseInt(document.getElementById('available_rooms').textContent);
        
        if (roomsInput) {
            roomsInput.addEventListener('input', function() {
                const requestedRooms = parseInt(this.value);
                
                if (requestedRooms > availableRooms) {
                    this.setCustomValidity(`Only ${availableRooms} rooms available`);
                    this.reportValidity();
                } else {
                    this.setCustomValidity('');
                }
            });
        }
    }

    // Price calculation
    function calculatePrice() {
        const checkInInput = document.getElementById('check_in');
        const checkOutInput = document.getElementById('check_out');
        const roomsInput = document.getElementById('rooms');
        const pricePerNight = parseFloat(document.getElementById('price_per_night').textContent);
        const totalPriceElement = document.getElementById('total_price');
        
        if (checkInInput && checkOutInput && roomsInput && totalPriceElement) {
            function updatePrice() {
                const checkIn = new Date(checkInInput.value);
                const checkOut = new Date(checkOutInput.value);
                const rooms = parseInt(roomsInput.value) || 0;
                
                if (checkIn && checkOut && checkOut > checkIn && rooms > 0) {
                    const nights = Math.ceil((checkOut - checkIn) / (1000 * 60 * 60 * 24));
                    const totalPrice = nights * rooms * pricePerNight;
                    totalPriceElement.textContent = `$${totalPrice.toFixed(2)}`;
                } else {
                    totalPriceElement.textContent = '$0.00';
                }
            }
            
            checkInInput.addEventListener('change', updatePrice);
            checkOutInput.addEventListener('change', updatePrice);
            roomsInput.addEventListener('input', updatePrice);
        }
    }

    // Initialize functions
    checkRoomAvailability();
    calculatePrice();

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add loading state to forms
    const submitButtons = document.querySelectorAll('button[type="submit"]');
    submitButtons.forEach(button => {
        button.addEventListener('click', function() {
            if (this.form && this.form.checkValidity()) {
                this.innerHTML = '<span class="loading"></span> Processing...';
                this.disabled = true;
            }
        });
    });

    // Image lazy loading
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));

    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    const cardObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                cardObserver.unobserve(entry.target);
            }
        });
    });

    cards.forEach(card => cardObserver.observe(card));
});

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

// Export functions for global use
window.TourismHub = {
    formatDate,
    formatCurrency,
    showNotification
};
