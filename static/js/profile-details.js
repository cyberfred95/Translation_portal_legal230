$(document).ready(function () {
    // Gestion du modal de succès pour la mise à jour des informations
    $('#success-update-btn').on('click', function (event) {
        event.stopPropagation();
        $('#success-update-user-data').addClass('hidden');
        window.location.reload();
    });

    // Gestion de la soumission du formulaire de mise à jour des informations
    $('form[name="change-user-data"]').on('submit', function (e) {
        e.preventDefault();

        const formData = new FormData(this);

        $.ajax({
            url: change_data_url,
            type: 'PUT',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            success: function () {
                $('#success-update-user-data').removeClass('hidden');
            },
            error: function (error) {
                errorNotification(error?.status, error?.responseJSON?.detail);
            }
        });
    });


    // ------------- TABS -------------

    function showTab(tabId) {
        // Masquer tous les contenus de tabs
        $('.tab-content').hide();
        // Afficher le contenu du tab sélectionné
        $(`#${tabId}-content`).show();

        // Retirer les styles actifs de tous les boutons
        $('button.tab').removeClass('bg-white text-gray-900 font-bold');
        $('button.tab').addClass('text-gray-900 hover:text-gray-900 text-gray-300');

        // Ajouter les styles actifs au bouton sélectionné
        $(`#${tabId}`).removeClass('text-gray-900 hover:text-gray-900 text-gray-300');
        $(`#${tabId}`).addClass('bg-white text-gray-900 font-bold');
    }

    let initialTab = 'profile-information';

    showTab(initialTab);

    $('#profile-information').click(function () {
        showTab('profile-information');
    });

    $('#profile-security').click(function () {
        showTab('profile-security');
    });

});
