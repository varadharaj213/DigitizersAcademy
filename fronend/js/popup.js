document.addEventListener('DOMContentLoaded', function() {
    const popupOverlay = document.getElementById('popup-overlay');
    const popupClose = document.querySelector('.popup-close');
    const leadForm = document.getElementById('lead-form');
    let hasShownPopup = false;

    function showPopup() {
        if (!hasShownPopup) {
            popupOverlay.classList.add('active');
            hasShownPopup = true;
        }
    }

    // Show after 10 seconds
    setTimeout(showPopup, 10000);

    // Show on scroll
    window.addEventListener('scroll', () => {
        const scrollY = window.scrollY || document.documentElement.scrollTop;
        const docHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        if ((scrollY / docHeight) > 0.35 && !hasShownPopup) {
            showPopup();
        }
    });

    // Close popup
    popupClose.addEventListener('click', () => popupOverlay.classList.remove('active'));
    popupOverlay.addEventListener('click', (e) => {
        if (e.target === popupOverlay) {
            popupOverlay.classList.remove('active');
        }
    });

    // Form submit
    leadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        window.location.href = 'http://127.0.0.1:5000/all-courses';
    });
});