document.addEventListener('DOMContentLoaded', function() {
    console.log('manage_users.js loaded and DOMContentLoaded');
    const openModalBtn = document.getElementById('openModalBtn');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const userModal = document.getElementById('userModal');
    const modalContent = document.getElementById('modalContent');

    if (openModalBtn && closeModalBtn && userModal && modalContent) {
        openModalBtn.addEventListener('click', function() {
            userModal.classList.remove('hidden');
            setTimeout(() => {
                modalContent.classList.remove('scale-95', 'opacity-0');
                modalContent.classList.add('scale-100', 'opacity-100');
            }, 50);
        });

        closeModalBtn.addEventListener('click', function() {
            modalContent.classList.remove('scale-100', 'opacity-100');
            modalContent.classList.add('scale-95', 'opacity-0');
            setTimeout(() => {
                userModal.classList.add('hidden');
            }, 300); // Match transition duration
        });

        // Close modal when clicking outside of it
        userModal.addEventListener('click', function(event) {
            if (event.target === userModal) {
                modalContent.classList.remove('scale-100', 'opacity-100');
                modalContent.classList.add('scale-95', 'opacity-0');
                setTimeout(() => {
                    userModal.classList.add('hidden');
                }, 300); // Match transition duration
            }
        });
    }
});