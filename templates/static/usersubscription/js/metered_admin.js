(() => {
    'use strict';

    document.addEventListener('DOMContentLoaded', () => {
        const config = getMeteredConfig();
        if (!config) {
            console.error('Metered modal configuration introuvable.');
            return;
        }
        new MeteredModalController(config).init();
    });

    function getMeteredConfig() {
        const element = document.getElementById('metered-modal-config');
        if (!element) {
            return null;
        }
        return {
            apiPricesUrl: element.dataset.apiPricesUrl || ''
        };
    }

    class MeteredModalController {
        constructor(config) {
            this.pricesUrl = config.apiPricesUrl;
            this.modal = document.getElementById('metered-modal');
            this.openButton = document.getElementById('metered-subscription-btn');
            this.closeButton = document.getElementById('close-metered-modal');
            this.subscriptionSelect = document.getElementById('metered-subscription-select');
            this.priceSection = document.getElementById('metered-price-section');
            this.priceSelect = document.getElementById('metered-price-select');
            this.priceLoading = document.getElementById('metered-price-loading');
            this.priceError = document.getElementById('metered-price-error');
            this.checkoutSection = document.getElementById('metered-checkout-section');
            this.checkoutButtonWithSerpa = document.getElementById('metered-checkout-button-with-serpa');
            this.checkoutButtonWithoutSerpa = document.getElementById('metered-checkout-button-without-serpa');
            this.withSerpaInput = document.getElementById('with-serpa-input');
            this.checkoutForm = document.getElementById('metered-checkout-form');
            this.boundBackdropHandler = this.handleBackdropClick.bind(this);
        }

        init() {
            if (!this.isReady()) {
                console.error('Metered modal incomplet, initialisation annulée.');
                return;
            }
            this.registerBaseEvents();
            this.registerCheckoutButtons();
            this.updateCheckoutState();
        }

        isReady() {
            return Boolean(
                this.pricesUrl !== undefined &&
                this.modal &&
                this.openButton &&
                this.subscriptionSelect &&
                this.checkoutForm &&
                this.withSerpaInput
            );
        }

        registerBaseEvents() {
            this.openButton.addEventListener('click', (event) => {
                event.preventDefault();
                this.showModal();
                this.loadPrices();
            });

            if (this.closeButton) {
                this.closeButton.addEventListener('click', () => this.hideModal());
            }

            this.subscriptionSelect.addEventListener('change', () => this.loadPrices());

            if (this.priceSelect) {
                this.priceSelect.addEventListener('change', () => this.updateCheckoutState());
            }

            window.addEventListener('click', this.boundBackdropHandler);
        }

        registerCheckoutButtons() {
            this.addCheckoutListener(this.checkoutButtonWithSerpa, true);
            this.addCheckoutListener(this.checkoutButtonWithoutSerpa, false);
        }

        addCheckoutListener(button, withSerpa) {
            if (!button) {
                return;
            }
            button.addEventListener('click', (event) => {
                event.preventDefault();
                this.handleCheckoutClick(withSerpa);
            });
        }

        handleCheckoutClick(withSerpa) {
            if (!this.canSubmit()) {
                console.error('Formulaire de checkout indisponible.');
                return;
            }
            this.setWithSerpa(withSerpa);
            this.checkoutForm.submit();
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
            this.setCheckoutButtonsDisabled(true);
        }

        updateCheckoutState() {
            const shouldDisable = !this.hasPriceSelection() || !this.canSubmit();
            this.setCheckoutButtonsDisabled(shouldDisable);
        }

        hasPriceSelection() {
            return Boolean(this.priceSelect && this.priceSelect.value);
        }

        canSubmit() {
            return Boolean(this.checkoutForm && this.withSerpaInput);
        }

        setCheckoutButtonsDisabled(disabled) {
            if (this.checkoutButtonWithSerpa) {
                this.checkoutButtonWithSerpa.disabled = disabled;
            }
            if (this.checkoutButtonWithoutSerpa) {
                this.checkoutButtonWithoutSerpa.disabled = disabled;
            }
        }

        setWithSerpa(value) {
            this.withSerpaInput.value = value ? 'true' : 'false';
        }
    }
})();
