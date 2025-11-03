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

    // Initialize usage bars with animation and tooltips
    function formatDots(n) {
      const s = String(n);
      return s.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    }

    function initUsageBars() {
      document.querySelectorAll('.usage-bars').forEach(container => {
        const sym = Number(container.dataset.sym || 0);
        const symMax = Number(container.dataset.symMax || 0);
        const words = Number(container.dataset.words || 0);
        const wordsMax = Number(container.dataset.wordsMax || 0);
        const files = Number(container.dataset.files || 0);
        const filesMax = Number(container.dataset.filesMax || 0);

        const entries = [
            { value: sym, max: symMax },
            { value: words, max: wordsMax },
            { value: files, max: filesMax },
        ];

        container.querySelectorAll('.bar-wrapper').forEach((wrapper, idx) => {
            const barEl = wrapper.querySelector('.bar');
            const fill = barEl.querySelector('.bar-fill');
            const tooltip = wrapper.querySelector('.bar-tooltip');
            const name = barEl.dataset.name || '';
            const { value, max } = entries[idx] || { value: 0, max: 0 };
            const unlimited = max === -1;
            let pct = 0;
            if (unlimited) {
                pct = 100; // plein pour illimité
                barEl.classList.add('unlimited');
            } else if (max > 0) {
                pct = Math.round((value / max) * 100);
                if (value >= max) pct = 100;
                if (pct < 0) pct = 0;
                if (pct > 100) pct = 100;
            } else {
                pct = 0;
            }
            // Tooltip content (∞ pour illimité)
            if (unlimited) {
                tooltip.textContent = `${name}: ∞`;
            } else {
                const maxLabel = formatDots(max);
                const valLabel = formatDots(value);
                tooltip.textContent = `${name}: ${valLabel}/${maxLabel} (${pct}%)`;
            }
            // Animate bar fill and position tooltip
          requestAnimationFrame(() => {
            fill.style.width = pct + '%';
            // position tooltip by percentage (wrapper and bar have same width due to grid)
            tooltip.style.left = pct + '%';
          });
        });
      });
    }

    initUsageBars();
    window.addEventListener('resize', initUsageBars);
});
