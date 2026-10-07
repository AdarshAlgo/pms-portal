document.addEventListener('DOMContentLoaded', function() {
    
    // Simple URL validation
    const urlInputs = document.querySelectorAll('input[type="url"]');
    urlInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if(this.value && !this.value.startsWith('http://') && !this.value.startsWith('https://')) {
                this.value = 'https://' + this.value;
            }
        });
    });

    // Confirmation dialogs for dangerous actions
    const confirmLinks = document.querySelectorAll('[data-confirm]');
    confirmLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if(!confirm(this.getAttribute('data-confirm'))) {
                e.preventDefault();
            }
        });
    });
});
