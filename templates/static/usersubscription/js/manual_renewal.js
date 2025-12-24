(() => {
    'use strict';

    document.addEventListener('DOMContentLoaded', () => {
        const element = document.getElementById('manual-renewal-config');
        const config = {
            activeWithoutStripe: Number(element?.dataset.activeWithoutStripe || 0),
            manualRenewalUrl: element?.dataset.manualRenewalUrl || '',
        };

        new ManualRenewalController(config.manualRenewalUrl).init();
        injectManualCounter(document.querySelector('.actions'), config.activeWithoutStripe);
    });

    class ManualRenewalController {
        constructor(manualRenewalUrl) {
            this.manualRenewalUrl = manualRenewalUrl;
            this.modal = document.getElementById('renewal-modal');
            this.openButton = document.getElementById('manual-renewal-btn');
            this.confirmButton = document.getElementById('confirm-renewal');
            this.cancelButton = document.getElementById('cancel-renewal');
            this.loadingIndicator = document.getElementById('loading-indicator');
            this.modalButtons = document.getElementById('modal-buttons');
            this.boundBackdropHandler = this.handleBackdropClick.bind(this);
        }

        init() {
            if (!this.isReady()) {
                return;
            }
            this.openButton.addEventListener('click', (event) => {
                event.preventDefault();
                this.showModal();
            });
            this.cancelButton.addEventListener('click', () => this.hideModal());
            this.confirmButton.addEventListener('click', () => this.submit());
            window.addEventListener('click', this.boundBackdropHandler);
        }

        isReady() {
            return Boolean(
                this.manualRenewalUrl &&
                this.modal &&
                this.openButton &&
                this.confirmButton &&
                this.cancelButton
            );
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
            if (this.loadingIndicator) {
                this.loadingIndicator.style.display = 'none';
            }
            if (this.modalButtons) {
                this.modalButtons.style.display = 'block';
            }
        }

        submit() {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            if (!csrfToken) {
                console.error('CSRF token introuvable pour lancer le renouvellement manuel.');
                return;
            }
            if (this.loadingIndicator) {
                this.loadingIndicator.style.display = 'block';
            }
            if (this.modalButtons) {
                this.modalButtons.style.display = 'none';
            }
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = this.manualRenewalUrl;

            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrfmiddlewaretoken';
            csrfInput.value = csrfToken.value;
            form.appendChild(csrfInput);

            document.body.appendChild(form);
            form.submit();
        }
    }

    function injectManualCounter(container, count) {
        if (!container || Number.isNaN(count)) {
            return;
        }
        const counterSpan = document.createElement('span');
        counterSpan.id = 'manual-counter';
        counterSpan.textContent = 'Abonnement manuel : ' + count;
        container.appendChild(counterSpan);
    }
})();

