document.addEventListener('DOMContentLoaded', function() {
    // Optional: Add animation to the "View More" button
    const viewMoreBtn = document.querySelector('.text-center.mt-5 .btn-primary');
    
    if (viewMoreBtn) {
        viewMoreBtn.addEventListener('mouseenter', function() {
            this.querySelector('.fa-arrow-right').style.transform = 'translateX(5px)';
            this.querySelector('.fa-arrow-right').style.transition = 'transform 0.3s ease';
        });
        
        viewMoreBtn.addEventListener('mouseleave', function() {
            this.querySelector('.fa-arrow-right').style.transform = 'translateX(0)';
        });
    }
});