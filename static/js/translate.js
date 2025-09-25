$(document).ready(function () {


    // ------------- TABS -------------


    function showTab(tabId) {
        $('.tab-content').hide();
        $(`#${tabId}-content`).show();
        $('button.tab').removeClass('bg-white text-gray-900 font-bold');
        $('button.tab').addClass('text-gray-900 hover:text-gray-900 text-gray-300');
        $('#expert-revision').addClass('hidden');
        $(`#${tabId}`).removeClass('text-gray-900 hover:text-gray-900 text-gray-300');
        $(`#${tabId}`).addClass('bg-white text-gray-900 font-bold');
    }

    function setHash(tab) {
        window.location.hash = tab;
    }

    let initialTab = 'text-translate';

    if (window.location.hash) {
        const hash = window.location.hash.substring(1);

        if (hash === 'document-translate') {
            initialTab = 'document-translate';
        } else if (hash === 'writing') {
            initialTab = 'writing';
        }
    }

    showTab(initialTab);
    setHash(initialTab);

    $('#text-translate').click(function () {
        showTab('text-translate');
        setHash('text-translate');
    });

    $('#document-translate').click(function () {
        showTab('document-translate');
        setHash('document-translate');
    });

    $('#writing').click(function () {
        showTab('writing');
        setHash('writing');
    });
});
