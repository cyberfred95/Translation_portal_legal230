/**
 * Subscription Error Overlay Handler
 * 
 * Manages the pricing button in the subscription error overlay.
 * Handles API calls to get pricing page URL with Stripe customer session.
 */
(function() {
  'use strict';

  const API_ENDPOINT = '/api/v1/stripe-pricing-page-url/';
  const LOADING_TEXT = 'Chargement...';
  const DEFAULT_ERROR_MESSAGE = 'Une erreur est survenue. Veuillez réessayer plus tard.';

  /**
   * Set button loading state.
   * 
   * @param {HTMLElement} button - Button element
   * @param {boolean} isLoading - Whether button is loading
   * @param {string} originalText - Original button text
   */
  function setButtonLoadingState(button, isLoading, originalText) {
    button.disabled = isLoading;
    button.textContent = isLoading ? LOADING_TEXT : originalText;
  }

  /**
   * Display error message using available notification system.
   * 
   * @param {string} message - Error message to display
   */
  function showError(message) {
    if (window.Toast && typeof window.Toast.error === 'function') {
      window.Toast.error(message);
    } else {
      alert(message);
    }
  }

  /**
   * Extract error message from API response.
   * 
   * @param {Response} response - Fetch API response
   * @returns {Promise<string>} Error message
   */
  async function extractErrorMessage(response) {
    try {
      const errorData = await response.json();
      return errorData.detail || DEFAULT_ERROR_MESSAGE;
    } catch (e) {
      return DEFAULT_ERROR_MESSAGE;
    }
  }

  /**
   * Fetch pricing page URL from API.
   * 
   * @returns {Promise<string>} Pricing page URL
   * @throws {Error} If API call fails
   */
  async function fetchPricingUrl() {
    const response = await fetch(API_ENDPOINT, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'same-origin',
    });

    if (!response.ok) {
      const errorMessage = await extractErrorMessage(response);
      throw new Error(errorMessage);
    }

    const data = await response.json();
    
    if (!data.url) {
      throw new Error('URL non disponible');
    }

    return data.url;
  }

  /**
   * Handle pricing button click event.
   * 
   * @param {HTMLElement} button - Button element
   */
  async function handlePricingButtonClick(button) {
    const originalText = button.textContent;
    
    try {
      setButtonLoadingState(button, true, originalText);
      const pricingUrl = await fetchPricingUrl();
      window.location.href = pricingUrl;
    } catch (error) {
      console.error('Erreur lors de la récupération de l\'URL des tarifs:', error);
      showError(error.message || DEFAULT_ERROR_MESSAGE);
      setButtonLoadingState(button, false, originalText);
    }
  }

  /**
   * Initialize pricing button handler.
   */
  function init() {
    const pricingButton = document.getElementById('subscription-pricing-button');
    
    if (!pricingButton) {
      return;
    }

    pricingButton.addEventListener('click', function() {
      handlePricingButtonClick(pricingButton);
    });
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

