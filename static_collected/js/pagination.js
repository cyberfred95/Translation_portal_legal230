$(document).ready(function () {
    var $pagination = $('.pagination');

    var totalItems = parseInt($pagination.data('total-items'));

    var itemsPerPage = parseInt($pagination.data('items-per-page'));

    var currentPage = parseInt($pagination.data('current-page'));

    var totalPages = Math.ceil(totalItems / itemsPerPage);

    function updatePagination() {
        if (totalPages <= 1) {
            $pagination.addClass('hidden');
            return;
        } else {
            $pagination.removeClass('hidden');
        }

        var $pageNumbers = $('#page-numbers');
        $pageNumbers.empty();

        var startPage = Math.max(1, currentPage - 2);
        var endPage = Math.min(totalPages, startPage + 4);

        if (startPage > 1) {
            $pageNumbers.append('<a href="#" class="page-number text-gray-225">1</a>');
            if (startPage > 2) {
                $pageNumbers.append('<span class="text-gray-225">...</span>');
            }
        }

        for (var i = startPage; i <= endPage; i++) {
            if (i === currentPage) {
                $pageNumbers.append('<span class="current-page text-gray-600 rounded">' + i + '</span>');
            } else {
                $pageNumbers.append('<a href="#" class="page-number text-gray-225">' + i + '</a>');
            }
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                $pageNumbers.append('<span class="text-gray-225">...</span>');
            }
            $pageNumbers.append('<a href="#" class="page-number text-gray-225">' + totalPages + '</a>');
        }

        $('#prev-page').toggleClass('text-gray-225 pointer-events-none', currentPage === 1)
            .toggleClass('text-gray-600', currentPage !== 1)
            .prop('disabled', currentPage === 1);
        $('#next-page').toggleClass('text-gray-225 pointer-events-none', currentPage === totalPages)
            .toggleClass('text-gray-600', currentPage !== totalPages)
            .prop('disabled', currentPage === totalPages);
    }

    function loadPage(page) {
        let currentUrl = new URL(window.location.href);

        currentUrl.searchParams.set('page', page);

        window.history.pushState({}, '', currentUrl.toString());

        window.location.reload();
    }

    $(document).on('click', '.page-number', function (e) {
        e.preventDefault();
        var page = parseInt($(this).text());
        loadPage(page);
    });

    $('#prev-page').click(function (e) {
        e.preventDefault();
        if (currentPage > 1) {
            loadPage(currentPage - 1);
        }
    });

    $('#next-page').click(function (e) {
        e.preventDefault();
        if (currentPage < totalPages) {
            loadPage(currentPage + 1);
        }
    });

    updatePagination();
});
