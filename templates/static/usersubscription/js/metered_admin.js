(() => {
    'use strict';

    document.addEventListener('DOMContentLoaded', () => {
        const element = document.getElementById('metered-modal-config');
        const pricesUrl = element?.dataset.apiPricesUrl || '';
        new MeteredModalController(pricesUrl).init();
    });

    class MeteredModalController {
        constructor(pricesUrl) {
            this.pricesUrl = pricesUrl;
            this.modal = document.getElementById('metered-modal');
            this.openButton = document.getElementById('metered-subscription-btn');
            this.closeButton = document.getElementById('close-metered-modal');
            this.subscriptionSelect = document.getElementById('metered-subscription-select');
            this.priceSection = document.getElementById('metered-price-section');
            this.priceSelect = document.getElementById('metered-price-select');
            this.priceLoading = document.getElementById('metered-price-loading');
            this.priceError = document.getElementById('metered-price-error');
            this.checkoutSection = document.getElementById('metered-checkout-section');
            this.checkoutButton = document.getElementById('metered-checkout-button');
            this.boundBackdropHandler = this.handleBackdropClick.bind(this);
        }

        init() {
            if (!this.isReady()) {
                return;
            }
            this.openButton.addEventListener('click', (event) => {
                event.preventDefault();
                this.showModal();
                this.loadPrices();
            });
            this.closeButton.addEventListener('click', () => this.hideModal());
            this.subscriptionSelect.addEventListener('change', () => this.loadPrices());
            if (this.priceSelect) {
                this.priceSelect.addEventListener('change', () => this.updateCheckoutState());
            }
            window.addEventListener('click', this.boundBackdropHandler);
        }

        isReady() {
            return Boolean(this.modal && this.openButton && this.subscriptionSelect);
        }

        handleBackdropClick(event) {
            if (event.target === this.modal) {
                this.hideModal();
            }
        }

        showModal() {
            this.modal.style.display = 'block';
        }

        hideModal() {
            this.modal.style.display = 'none';
            this.resetPriceSection();
        }

        loadPrices() {
            const productId = this.getSelectedProductId();
            if (!productId) {
                this.resetPriceSection();
                return;
            }

            this.showPriceSection();
            this.preparePriceSelect();
            this.showPriceLoading();

            if (!this.pricesUrl) {
                this.showPriceError('Endpoint Stripe Price non configuré.');
                return;
            }

            const url = new URL(this.pricesUrl, window.location.origin);
            url.searchParams.append('product_id', productId);

            fetch(url.toString(), { headers: { Accept: 'application/json' } })
                .then((response) => {
                    if (!response.ok) {
                        throw new Error('Impossible de récupérer les Price ID.');
                    }
                    return response.json();
                })
                .then((data) => {
                    const prices = Array.isArray(data.prices) ? data.prices : [];
                    if (!prices.length) {
                        throw new Error('Aucun Price ID actif pour ce produit.');
                    }
                    this.populatePrices(prices);
                    this.showCheckoutSection();
                })
                .catch((error) => {
                    this.showPriceError(error.message);
                })
                .finally(() => {
                    this.hidePriceLoading();
                });
        }

        getSelectedProductId() {
            const option = this.subscriptionSelect.options[this.subscriptionSelect.selectedIndex];
            return option ? option.getAttribute('data-stripe-product-id') : null;
        }

        showPriceSection() {
            if (this.priceSection) {
                this.priceSection.style.display = 'block';
            }
        }

        preparePriceSelect() {
            if (this.priceSelect) {
                this.priceSelect.innerHTML = '';
                this.priceSelect.disabled = true;
            }
            this.hidePriceError();
            this.hideCheckoutSection();
        }

        showPriceLoading() {
            if (this.priceLoading) {
                this.priceLoading.style.display = 'block';
            }
        }

        hidePriceLoading() {
            if (this.priceLoading) {
                this.priceLoading.style.display = 'none';
            }
        }

        showPriceError(message) {
            this.showPriceSection();
            this.hidePriceLoading();
            if (this.priceError) {
                this.priceError.textContent = message;
                this.priceError.style.display = 'block';
            }
            if (this.priceSelect) {
                this.priceSelect.disabled = true;
                this.priceSelect.innerHTML = '';
            }
            this.hideCheckoutSection();
        }

        hidePriceError() {
            if (this.priceError) {
                this.priceError.textContent = '';
                this.priceError.style.display = 'none';
            }
        }

        resetPriceSection() {
            if (this.priceSection) {
                this.priceSection.style.display = 'none';
            }
            if (this.priceSelect) {
                this.priceSelect.innerHTML = '';
                this.priceSelect.disabled = true;
            }
            this.hidePriceLoading();
            this.hidePriceError();
            this.hideCheckoutSection();
        }

        populatePrices(prices) {
            if (!this.priceSelect) {
                return;
            }
            const fragment = document.createDocumentFragment();
            prices.forEach(({ id, nickname }) => {
                const option = document.createElement('option');
                option.value = id;
                option.textContent = nickname ? `${id} - ${nickname}` : id;
                fragment.appendChild(option);
            });
            this.priceSelect.innerHTML = '';
            this.priceSelect.appendChild(fragment);
            this.priceSelect.disabled = false;
            this.updateCheckoutState();
        }

        showCheckoutSection() {
            if (this.checkoutSection) {
                this.checkoutSection.style.display = 'block';
            }
            this.updateCheckoutState();
        }

        hideCheckoutSection() {
            if (this.checkoutSection) {
                this.checkoutSection.style.display = 'none';
            }
            if (this.checkoutButton) {
                this.checkoutButton.disabled = true;
            }
        }

        updateCheckoutState() {
            if (this.checkoutButton && this.priceSelect) {
                this.checkoutButton.disabled = !this.priceSelect.value;
            }
        }
    }

})();

