$(document).ready(function () {


    // ------------- TABS -------------


    function showTab(tabId) {
        $('.tab-content').hide();
        $(`#${tabId}-content`).show();
        $('button.tab').removeClass('bg-gray-800 text-white border-gray-800 hover:bg-gray-800 hover:text-white hover:border-gray-800');
        $('#expert-revision').addClass('hidden');
        $(`#${tabId}`).addClass('bg-gray-800 text-white border-gray-800 hover:bg-gray-800 hover:text-white hover:border-gray-800');
    }

    function setHash(tab) {
        window.location.hash = tab;
    }

    let initialTab = 'text-translate';

    if (window.location.hash) {
        const hash = window.location.hash.substring(1);
        console.log('hash', hash)
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
