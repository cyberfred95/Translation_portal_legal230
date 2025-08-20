$(document).ready(function () {

    // ------------- TABS -------------

    function showTab(tabId) {
        // Masquer tous les contenus de tabs
        $('.tab-content').hide();
        // Afficher le contenu du tab sélectionné
        $(`#${tabId}-content`).show();
        
        // Retirer les styles actifs de tous les boutons
        $('button.tab').removeClass('bg-white text-gray-900 shadow-sm border border-gray-200');
        $('button.tab').addClass('text-gray-900 hover:bg-white/50');
        
        // Ajouter les styles actifs au bouton sélectionné
        $(`#${tabId}`).removeClass('text-gray-900 hover:bg-white/50');
        $(`#${tabId}`).addClass('bg-white text-gray-900 shadow-sm border border-gray-200');
    }

    function setHash(tab) {
        window.location.hash = tab;
    }

    let initialTab = 'profile-information';

    if (window.location.hash) {
        const hash = window.location.hash.substring(1);
        if (hash === 'profile-security') {
            initialTab = 'profile-security';
        }
    }

    showTab(initialTab);
    setHash(initialTab);

    $('#profile-information').click(function () {
        showTab('profile-information');
        setHash('profile-information');
    });

    $('#profile-security').click(function () {
        showTab('profile-security');
        setHash('profile-security');
    });
});
