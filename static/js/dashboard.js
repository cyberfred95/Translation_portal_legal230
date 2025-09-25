'use strict';

function filterTable() {
    const typeFilter = document.getElementById('type-filter').value.toLowerCase();
    const statusFilter = document.getElementById('statusFilter').value;
    const languageFilter = document.getElementById('languageFilter').value;
    const tableRows = document.querySelectorAll('tbody tr[data-type]');
    let visibleCount = 0;

    tableRows.forEach(function (row) {
        const rowType = row.getAttribute('data-type');
        const rowStatus = row.getAttribute('data-status');
        const rowLanguage = row.getAttribute('data-language');
        let showRow = true;

        // Filtrage par type
        if (typeFilter && typeFilter !== '') {
            if (typeFilter === 'text' && rowType !== 'text') {
                showRow = false;
            } else if (typeFilter === 'document' && rowType !== 'document') {
                showRow = false;
            }
        }

        // Filtrage par statut
        if (statusFilter && statusFilter !== '' && showRow) {
            if (rowStatus !== statusFilter) {
                showRow = false;
            }
        }

        // Filtrage par langue
        if (languageFilter && languageFilter !== '' && showRow) {
            if (rowLanguage !== languageFilter) {
                showRow = false;
            }
        }

        if (showRow) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });

    // Mettre à jour le compteur de la carte
    updateTranslationCounter(visibleCount, typeFilter, statusFilter, languageFilter);

    // Afficher/masquer le message "aucun résultat"
    const noResultsRow = document.querySelector('tbody tr:not([data-type])');
    if (noResultsRow) {
        if (visibleCount === 0 && tableRows.length > 0) {
            noResultsRow.style.display = '';
            noResultsRow.innerHTML = `
                <td colspan="5" style="text-align: center; padding: 2rem; color: #6b7280;">
                    <div style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" style="opacity: 0.5;">
                            <circle cx="11" cy="11" r="8"></circle>
                            <path d="m21 21-4.35-4.35"></path>
                        </svg>
                        <p style="font-weight: 600;">No results found</p>
                        <p style="font-size: 0.875rem;">No translations match the selected filters.</p>
                    </div>
                </td>
            `;
        } else if (visibleCount > 0) {
            noResultsRow.style.display = 'none';
        }
    }

    // Masquer la pagination quand on filtre
    const pagination = document.querySelector('.pagination, [style*="pagination"]');
    if (pagination) {
        if ((typeFilter && typeFilter !== '') || (statusFilter && statusFilter !== '') || (languageFilter && languageFilter !== '')) {
            pagination.style.display = 'none';
        } else {
            pagination.style.display = '';
        }
    }
}

function updateTranslationCounter(visibleCount, filterType, filterStatus, filterLanguage) {
    const counterElement = document.querySelector('.stat-value');
    const titleElement = document.querySelector('.stat-title');
    const originalCount = parseInt(counterElement.getAttribute('data-original-count')) || 0;

    if ((filterType && filterType !== '') || (filterStatus && filterStatus !== '') || (filterLanguage && filterLanguage !== '')) {
        // Si un filtre est appliqué, afficher le nombre visible
        counterElement.textContent = visibleCount;

        // Déterminer le titre en fonction des filtres appliqués
        let title = 'FILTERED TRANSLATIONS';
        if (filterType && filterStatus) {
            if (filterType === 'text') {
                title = 'TEXT TRANSLATIONS';
            } else if (filterType === 'document') {
                title = 'DOCUMENT TRANSLATIONS';
            }
        } else if (filterType) {
            if (filterType === 'text') {
                title = 'TEXT TRANSLATIONS';
            } else if (filterType === 'document') {
                title = 'DOCUMENT TRANSLATIONS';
            }
        } else if (filterStatus) {
            if (filterStatus === 'completed') {
                title = 'COMPLETED TRANSLATIONS';
            } else if (filterStatus === 'in-progress') {
                title = 'IN PROGRESS TRANSLATIONS';
            } else if (filterStatus === 'error') {
                title = 'ERROR TRANSLATIONS';
            } else if (filterStatus === 'needs-attention') {
                title = 'ATTENTION TRANSLATIONS';
            }
        }
        titleElement.textContent = title;
    } else {
        // Si aucun filtre, revenir au compteur original
        counterElement.textContent = originalCount;
        titleElement.textContent = 'TRANSLATED DOCUMENTS';
    }
}

// Fonction pour effacer tous les filtres
function clearAllFilters() {
    // Remettre tous les filtres à leur valeur par défaut
    document.getElementById('type-filter').value = '';
    document.getElementById('statusFilter').value = '';
    document.getElementById('languageFilter').value = '';

    // Afficher toutes les lignes
    const tableRows = document.querySelectorAll('tbody tr[data-type]');
    tableRows.forEach(function (row) {
        row.style.display = '';
    });

    // Masquer le message "aucun résultat" s'il est affiché
    const noResultsRow = document.querySelector('tbody tr:not([data-type])');
    if (noResultsRow) {
        noResultsRow.style.display = 'none';
    }

    // Remettre le compteur à sa valeur originale
    const counterElement = document.querySelector('.stat-value');
    const titleElement = document.querySelector('.stat-title');
    const originalCount = parseInt(counterElement.getAttribute('data-original-count')) || 0;

    counterElement.textContent = originalCount;
    titleElement.textContent = 'TRANSLATED DOCUMENTS';

    // Réafficher la pagination
    const pagination = document.querySelector('.pagination, [style*="pagination"]');
    if (pagination) {
        pagination.style.display = '';
    }

    // Rediriger vers la page sans paramètres de filtre
    const baseUrl = window.location.pathname;
    window.history.pushState({}, '', baseUrl);
}

// Initialiser le filtrage au chargement de la page
document.addEventListener('DOMContentLoaded', function () {
    // Conserver la sélection des filtres si la page est rechargée
    const urlParams = new URLSearchParams(window.location.search);
    const typeParam = urlParams.get('type');
    const statusParam = urlParams.get('status');
    const languageParam = urlParams.get('language');

    if (typeParam) {
        document.getElementById('type-filter').value = typeParam;
    }
    if (statusParam) {
        document.getElementById('statusFilter').value = statusParam;
    }
    if (languageParam) {
        document.getElementById('languageFilter').value = languageParam;
    }

    // Appliquer les filtres s'ils existent
    if (typeParam || statusParam || languageParam) {
        filterTable();
    }

    // Le mapping des status est géré par status-management.js
});