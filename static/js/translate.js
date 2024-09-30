$(document).ready(function () {


    // ------------- TABS -------------


    function showTab(tabId) {
        $('.tab-content').hide();
        $(`#${tabId}-content`).show();
        $('button.tab').removeClass('bg-gray-800 text-white border-gray-800 hover:bg-gray-800 hover:text-white hover:border-gray-800');
        $('#expert-revision').addClass('hidden');
        $(`#${tabId}`).addClass('bg-gray-800 text-white border-gray-800 hover:bg-gray-800 hover:text-white hover:border-gray-800');
    }

    function setHash(step) {
        window.location.hash = `step-${step}`;
    }

    let initialTab = 'text-translate';
    let initialStep = 1;

    if (window.location.hash) {
        const hash = window.location.hash.substring(1);
        if (hash === 'step-2') {
            initialTab = 'document-translate';
            initialStep = 2;
        } else if (hash === 'step-3') {
            initialTab = 'writing';
            initialStep = 3;
        }
    }

    showTab(initialTab);
    setHash(initialStep);

    $('#text-translate').click(function () {
        showTab('text-translate');
        setHash(1);
    });

    $('#document-translate').click(function () {
        showTab('document-translate');
        setHash(2);
    });

    $('#writing').click(function () {
        showTab('writing');
        setHash(3);

    });
});

const errorNotification = () => {
    const $modalError = $('#modal-error');
    const $closeModalError = $('#close-modal-error');

    $modalError.removeClass('hidden');
    $closeModalError.removeClass('hidden');

    $closeModalError.on('click', function () {
        $modalError.addClass('hidden');
        $closeModalError.addClass('hidden');
    });

    $(window).on('click', function (event) {
        if ($(event.target).is($modalError)) {
            $modalError.addClass('hidden');
            $closeModalError.addClass('hidden');
        }
    });

    $(document).on('click', '.reload', function () {
        window.location.reload();
    });
};
