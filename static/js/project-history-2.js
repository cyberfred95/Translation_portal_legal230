// project-history-2.js - JavaScript pour la nouvelle page project_history_2.html

// Variables globales
let currentPage = 1;
let totalPages = 1;
let filteredProjects = [];
let allProjects = [];

document.addEventListener('DOMContentLoaded', function() {
    // Initialisation
    initializeData();
    setupEventListeners();
    setupPagination();
});

function initializeData() {
    // Récupérer tous les projets depuis le DOM
    const rows = document.querySelectorAll('.project-row');
    allProjects = Array.from(rows).map(row => ({
        element: row,
        document: row.dataset.document || '',
        type: row.dataset.type || '',
        status: row.dataset.status || '',
        language: row.dataset.language || ''
    }));
    filteredProjects = [...allProjects];
}

function setupEventListeners() {
    // Filtres de recherche
    const searchInput = document.getElementById('search-input');
    const typeFilter = document.getElementById('type-filter');
    const statusFilter = document.getElementById('status-filter');
    const languageFilter = document.getElementById('language-filter');
    
    if (searchInput) searchInput.addEventListener('input', filterTable);
    if (typeFilter) typeFilter.addEventListener('change', filterTable);
    if (statusFilter) statusFilter.addEventListener('change', filterTable);
    if (languageFilter) languageFilter.addEventListener('change', filterTable);
    
    // Actions des boutons
    setupDownloadButtons();
    setupExpertRevisionButtons();
    setupModalHandlers();
    setupDeleteButtons();
}

function filterTable() {
    const searchInput = document.getElementById('search-input');
    const typeFilter = document.getElementById('type-filter');
    const statusFilter = document.getElementById('status-filter');
    const languageFilter = document.getElementById('language-filter');
    
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    const selectedType = typeFilter ? typeFilter.value : '';
    const selectedStatus = statusFilter ? statusFilter.value : '';
    const selectedLanguage = languageFilter ? languageFilter.value : '';
    
    filteredProjects = allProjects.filter(project => {
        const matchesSearch = project.document.includes(searchTerm);
        const matchesType = !selectedType || project.type === selectedType;
        const matchesStatus = !selectedStatus || project.status.includes(selectedStatus);
        const matchesLanguage = !selectedLanguage || project.language === selectedLanguage;
        
        return matchesSearch && matchesType && matchesStatus && matchesLanguage;
    });
    
    // Afficher/masquer les lignes
    allProjects.forEach(project => {
        const isVisible = filteredProjects.includes(project);
        project.element.style.display = isVisible ? '' : 'none';
    });
    
    // Mettre à jour la pagination
    updatePagination();
}

function setupDownloadButtons() {
    document.querySelectorAll('.download-file').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const translatedFile = this.dataset.translatedFile;
            const reviewedFile = this.dataset.reviewedFile;
            
            if (reviewedFile && translatedFile) {
                showDownloadOptions(this, translatedFile, reviewedFile);
            } else if (translatedFile) {
                downloadFile(translatedFile);
            }
        });
    });
}

function showDownloadOptions(button, translatedFile, reviewedFile) {
    // Créer un menu déroulant pour choisir le fichier
    const existingTooltip = button.parentNode.querySelector('.download-tooltip');
    if (existingTooltip) {
        existingTooltip.remove();
        return;
    }
    
    const tooltip = document.createElement('div');
    tooltip.className = 'download-tooltip absolute z-10 bg-white rounded-md shadow-lg p-2 mt-2 right-0 border border-gray-200';
    tooltip.innerHTML = `
        <button type="button" class="download-file-option block w-full text-left px-2 py-1 hover:bg-gray-100 whitespace-nowrap text-sm" data-file-url="${translatedFile}">
            ${language_code === 'fr' ? 'Traduit' : 'Translated'}
        </button>
        <button type="button" class="download-file-option block w-full text-left px-2 py-1 hover:bg-gray-100 whitespace-nowrap text-sm" data-file-url="${reviewedFile}">
            ${language_code === 'fr' ? 'Post-édité' : 'Post-edited'}
        </button>
    `;
    
    button.parentNode.appendChild(tooltip);
    
    // Event listeners pour les options
    tooltip.querySelectorAll('.download-file-option').forEach(option => {
        option.addEventListener('click', function() {
            downloadFile(this.dataset.fileUrl);
            tooltip.remove();
        });
    });
    
    // Fermer au clic extérieur
    setTimeout(() => {
        document.addEventListener('click', function closeTooltip(e) {
            if (!tooltip.contains(e.target) && !button.contains(e.target)) {
                tooltip.remove();
                document.removeEventListener('click', closeTooltip);
            }
        });
    }, 100);
}

function downloadFile(fileUrl) {
    // Créer un lien temporaire pour télécharger
    const link = document.createElement('a');
    link.href = fileUrl;
    link.download = '';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function setupExpertRevisionButtons() {
    document.querySelectorAll('.expert-revision').forEach(button => {
        button.addEventListener('click', function(e) {
            if (this.disabled) {
                e.preventDefault();
                return;
            }
            
            const projectId = this.dataset.id;
            const displayPopup = this.dataset.display === 'true';
            const translatedFile = this.dataset.translatedFile;
            
            if (displayPopup) {
                showQuoteModal();
            } else {
                requestExpertRevision(projectId, translatedFile);
            }
        });
    });
}

function showQuoteModal() {
    const modal = document.getElementById('modal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.style.display = 'flex';
    }
}

function hideQuoteModal() {
    const modal = document.getElementById('modal');
    if (modal) {
        modal.classList.add('hidden');
        modal.style.display = 'none';
    }
}

function requestExpertRevision(projectId, translatedFile) {
    // Faire une requête AJAX pour la révision experte
    fetch(expert_revision_file_url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            project_id: projectId,
            translated_file: translatedFile
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Expert revision request sent successfully', 'success');
        } else {
            showNotification('Error sending expert revision request', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error sending expert revision request', 'error');
    });
}

function setupModalHandlers() {
    const modal = document.getElementById('modal');
    const closeIcon = document.getElementById('closeIcon');
    
    if (closeIcon) {
        closeIcon.addEventListener('click', hideQuoteModal);
    }
    
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                hideQuoteModal();
            }
        });
    }
    
    // Escape key pour fermer la modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            hideQuoteModal();
        }
    });
}

function setupDeleteButtons() {
    document.querySelectorAll('.delete-project').forEach(button => {
        button.addEventListener('click', function() {
            const projectId = this.dataset.projectId;
            if (confirm(language_code === 'fr' ? 'Êtes-vous sûr de vouloir supprimer ce projet ?' : 'Are you sure you want to delete this project?')) {
                deleteProject(projectId);
            }
        });
    });
}

function deleteProject(projectId) {
    // Implementer la suppression de projet
    fetch(`/api/projects/${projectId}/delete/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => {
        if (response.ok) {
            // Supprimer la ligne du tableau
            const row = document.querySelector(`[data-project-id="${projectId}"]`).closest('tr');
            if (row) {
                row.remove();
            }
            showNotification('Project deleted successfully', 'success');
        } else {
            showNotification('Error deleting project', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error deleting project', 'error');
    });
}

function setupPagination() {
    const prevButton = document.getElementById('prev-page');
    const nextButton = document.getElementById('next-page');
    
    if (prevButton) {
        prevButton.addEventListener('click', function(e) {
            e.preventDefault();
            if (currentPage > 1) {
                currentPage--;
                updatePagination();
            }
        });
    }
    
    if (nextButton) {
        nextButton.addEventListener('click', function(e) {
            e.preventDefault();
            if (currentPage < totalPages) {
                currentPage++;
                updatePagination();
            }
        });
    }
}

function updatePagination() {
    const itemsPerPage = 10;
    const totalItems = filteredProjects.length;
    totalPages = Math.ceil(totalItems / itemsPerPage);
    
    // Mettre à jour les boutons
    const prevButton = document.getElementById('prev-page');
    const nextButton = document.getElementById('next-page');
    
    if (prevButton) {
        prevButton.disabled = currentPage <= 1;
        prevButton.classList.toggle('opacity-50', currentPage <= 1);
        prevButton.classList.toggle('cursor-not-allowed', currentPage <= 1);
    }
    
    if (nextButton) {
        nextButton.disabled = currentPage >= totalPages;
        nextButton.classList.toggle('opacity-50', currentPage >= totalPages);
        nextButton.classList.toggle('cursor-not-allowed', currentPage >= totalPages);
    }
    
    // Mettre à jour les numéros de page
    updatePageNumbers();
}

function updatePageNumbers() {
    const pageNumbersContainer = document.getElementById('page-numbers');
    if (!pageNumbersContainer) return;
    
    pageNumbersContainer.innerHTML = '';
    
    // Logique pour afficher les numéros de page
    const maxVisible = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    
    // Ajuster le début si nous sommes près de la fin
    if (endPage - startPage < maxVisible - 1) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }
    
    // Page précédente avec ...
    if (startPage > 1) {
        addPageButton(1);
        if (startPage > 2) {
            addEllipsis();
        }
    }
    
    // Pages visibles
    for (let i = startPage; i <= endPage; i++) {
        addPageButton(i);
    }
    
    // Page suivante avec ...
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            addEllipsis();
        }
        addPageButton(totalPages);
    }
}

function addPageButton(pageNumber) {
    const pageNumbersContainer = document.getElementById('page-numbers');
    const button = document.createElement('button');
    button.textContent = pageNumber;
    button.className = `px-3 py-2 text-sm rounded-md ${
        pageNumber === currentPage 
            ? 'bg-black/5 text-gray-900' 
            : 'text-gray-900 hover:bg-black/5'
    }`;
    
    button.addEventListener('click', function() {
        currentPage = pageNumber;
        updatePagination();
    });
    
    pageNumbersContainer.appendChild(button);
}

function addEllipsis() {
    const pageNumbersContainer = document.getElementById('page-numbers');
    const ellipsis = document.createElement('span');
    ellipsis.textContent = '...';
    ellipsis.className = 'px-3 py-2 text-sm text-gray-900';
    pageNumbersContainer.appendChild(ellipsis);
}

// Fonctions utilitaires
function getCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

function showNotification(message, type = 'info') {
    // Créer une notification temporaire
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 p-4 rounded-md shadow-lg ${
        type === 'success' ? 'bg-green-100 text-green-800 border border-green-200' :
        type === 'error' ? 'bg-red-100 text-red-800 border border-red-200' :
        'bg-blue-100 text-blue-800 border border-blue-200'
    }`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Supprimer après 3 secondes
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Gérer le redimensionnement de la fenêtre
window.addEventListener('resize', function() {
    // Fermer les tooltips ouverts
    document.querySelectorAll('.download-tooltip').forEach(tooltip => {
        tooltip.remove();
    });
});
