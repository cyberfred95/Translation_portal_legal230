document.addEventListener('DOMContentLoaded', function () {
  const root = document.querySelector('.profile-details-page');
  if (!root) return;

  const changeDataUrl = root.getAttribute('data-change-url') || '';

  const tabButtons = {
    info: root.querySelector('#profile-information'),
    security: root.querySelector('#profile-security'),
  };
  const tabContents = {
    info: root.querySelector('#profile-information-content'),
    security: root.querySelector('#profile-security-content'),
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
  const form = root.querySelector('form[name="change-user-data"]');
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
          return;
        }

        // Show success modal
        const modal = root.querySelector('#success-update-user-data');
        if (modal) modal.classList.remove('hidden');
      } catch (err) {
        // Silent error handling
      }
    });
  }

  // Close success modal on button click or overlay click
  const modal = root.querySelector('#success-update-user-data');
  const modalBtn = root.querySelector('#success-update-btn');
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
  function handleLogout(e) {
    e.preventDefault();
    e.stopPropagation();
    
    // Try to get CSRF token from cookie first
    let csrfToken = getCookie('csrftoken');
    
    // If not found in cookie, try to get it from the form's hidden input
    if (!csrfToken) {
      const csrfInput = root.querySelector('[name=csrfmiddlewaretoken]');
      if (csrfInput) {
        csrfToken = csrfInput.value;
      }
    }
    
    if (!csrfToken) {
      return;
    }

    // Get current language prefix from URL (e.g., /fr/ or /en/)
    const currentPath = window.location.pathname;
    const langPrefix = currentPath.split('/')[1] || '';
    const logoutUrl = langPrefix ? `/${langPrefix}/accounts/logout/` : '/accounts/logout/';

    // Create form and submit to logout URL
    const logoutForm = document.createElement('form');
    logoutForm.method = 'POST';
    logoutForm.action = logoutUrl;
    
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = csrfToken;
    logoutForm.appendChild(csrfInput);
    
    document.body.appendChild(logoutForm);
    logoutForm.submit();
  }

  // Attach logout handler using event delegation
  root.addEventListener('click', function(e) {
    const logoutBtn = e.target.closest('#logout-btn');
    if (logoutBtn) {
      handleLogout(e);
    }
  }, true);
});



