document.addEventListener('DOMContentLoaded', function() {
    const editModal = document.getElementById('edit-user-modal');
    const editForm = document.getElementById('edit-user-form');
    const closeModalBtn = document.getElementById('close-edit-modal');
    const cancelBtn = document.getElementById('cancel-edit');
    const emailInput = document.getElementById('edit-email');
    const emailWarningActive = document.getElementById('email-change-warning-active');
    const emailWarningInactive = document.getElementById('email-change-warning-inactive');
    let originalEmail = '';
    let hasActiveSubscription = false;

    document.querySelectorAll('.mail-user').forEach(button => {
        button.addEventListener('click', function() {
            const email = this.dataset.email;
            window.location.href = `mailto:${email}`;
        });
    });

    document.querySelectorAll('.edit-user').forEach(button => {
        button.addEventListener('click', function() {
            const userId = this.dataset.userId;
            const username = this.dataset.username;
            const email = this.dataset.email || '';
            const isAdmin = this.dataset.isAdmin === 'true';
            hasActiveSubscription = this.dataset.hasActiveSubscription === 'true';
            
            // Store original email
            originalEmail = email;
            
            // Populate modal fields
            document.getElementById('edit-user-id').value = userId;
            document.getElementById('edit-username').value = username;
            document.getElementById('edit-email').value = email;
            document.getElementById('edit-is-admin').checked = isAdmin;
            
            // Hide warnings initially
            if (emailWarningActive) {
                emailWarningActive.classList.add('hidden');
            }
            if (emailWarningInactive) {
                emailWarningInactive.classList.add('hidden');
            }
            
            // Show modal
            editModal.classList.remove('hidden');
        });
    });

    // Check email change and show/hide warning
    if (emailInput && emailWarningActive && emailWarningInactive) {
        emailInput.addEventListener('input', function() {
            const currentEmail = this.value.trim();
            
            // Show warning if email has changed and new email is not empty
            if (currentEmail !== originalEmail && currentEmail !== '') {
                if (hasActiveSubscription) {
                    emailWarningActive.classList.remove('hidden');
                    emailWarningInactive.classList.add('hidden');
                } else {
                    emailWarningActive.classList.add('hidden');
                    emailWarningInactive.classList.remove('hidden');
                }
            } else {
                emailWarningActive.classList.add('hidden');
                emailWarningInactive.classList.add('hidden');
            }
        });
    }

    // Close modal handlers
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', function() {
            editModal.classList.add('hidden');
            if (emailWarningActive) {
                emailWarningActive.classList.add('hidden');
            }
            if (emailWarningInactive) {
                emailWarningInactive.classList.add('hidden');
            }
        });
    }

    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            editModal.classList.add('hidden');
            if (emailWarningActive) {
                emailWarningActive.classList.add('hidden');
            }
            if (emailWarningInactive) {
                emailWarningInactive.classList.add('hidden');
            }
        });
    }

    // Close modal on background click
    editModal?.addEventListener('click', function(e) {
        if (e.target === editModal) {
            editModal.classList.add('hidden');
            if (emailWarningActive) {
                emailWarningActive.classList.add('hidden');
            }
            if (emailWarningInactive) {
                emailWarningInactive.classList.add('hidden');
            }
        }
    });
});
