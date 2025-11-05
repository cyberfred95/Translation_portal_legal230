document.addEventListener('DOMContentLoaded', function () {
  const root = document.querySelector('.profile-details-page');
  if (!root) return;

  const changeDataUrl = root.getAttribute('data-change-url') || '';

  const tabButtons = {
    info: document.getElementById('profile-information'),
    security: document.getElementById('profile-security'),
  };
  const tabContents = {
    info: document.getElementById('profile-information-content'),
    security: document.getElementById('profile-security-content'),
  };

  function showTab(tab) {
    if (!tabButtons.info || !tabButtons.security) return;
    if (!tabContents.info || !tabContents.security) return;

    const isInfo = tab === 'info';
    tabContents.info.classList.toggle('hidden', !isInfo);
    tabContents.security.classList.toggle('hidden', isInfo);

    // Active state on buttons
    tabButtons.info.classList.toggle('is-active', isInfo);
    tabButtons.security.classList.toggle('is-active', !isInfo);
    tabButtons.info.setAttribute('aria-selected', String(isInfo));
    tabButtons.security.setAttribute('aria-selected', String(!isInfo));
  }

  if (tabButtons.info) {
    tabButtons.info.addEventListener('click', () => showTab('info'));
  }
  if (tabButtons.security) {
    tabButtons.security.addEventListener('click', () => showTab('security'));
  }

  // Expose URL if other scripts need it later
  window.profileDetails = window.profileDetails || {};
  window.profileDetails.changeDataUrl = changeDataUrl;

  // Set initial tab state (Information visible by default)
  showTab('info');

  // Handle form submission as PUT to changeDataUrl
  const form = document.querySelector('form[name="change-user-data"]');
  if (form && changeDataUrl) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(form);

      // Extract CSRF token
      const csrfToken = formData.get('csrfmiddlewaretoken') || '';

      try {
        const response = await fetch(changeDataUrl, {
          method: 'PUT',
          headers: {
            'X-CSRFToken': csrfToken,
          },
          body: formData,
          credentials: 'same-origin',
        });

        if (!response.ok) {
          // Optionally handle validation errors
          console.warn('Update failed', await response.text());
          return;
        }

        // Show success modal
        const modal = document.getElementById('success-update-user-data');
        if (modal) modal.classList.remove('hidden');
      } catch (err) {
        console.error('Update error', err);
      }
    });
  }

  // Close success modal on button click or overlay click
  const modal = document.getElementById('success-update-user-data');
  const modalBtn = document.getElementById('success-update-btn');
  if (modalBtn && modal) {
    modalBtn.addEventListener('click', () => {
      modal.classList.add('hidden');
    });
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.add('hidden');
      }
    });
  }

  // Logout functionality
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', function(e) {
      e.preventDefault();
      
      // Get CSRF token
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
      if (!csrfToken) {
        console.error('CSRF token not found');
        return;
      }

      // Create form and submit to logout URL
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = '/accounts/logout/';
      
      const csrfInput = document.createElement('input');
      csrfInput.type = 'hidden';
      csrfInput.name = 'csrfmiddlewaretoken';
      csrfInput.value = csrfToken.value;
      form.appendChild(csrfInput);
      
      document.body.appendChild(form);
      form.submit();
    });
  }
});



