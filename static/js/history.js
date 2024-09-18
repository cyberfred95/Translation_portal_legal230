$(document).ready(function () {
    var $pagination = $('.pagination');
    var totalItems = parseInt($pagination.data('total-items'));
    console.log('totalItems', totalItems)
    var itemsPerPage = parseInt($pagination.data('items-per-page'));
    console.log('itemsPerPage', itemsPerPage)
    var currentPage = parseInt($pagination.data('current-page'));
    console.log('currentPage', currentPage)
    var totalPages = Math.ceil(totalItems / itemsPerPage);

       function updatePagination() {
        var $pageNumbers = $('#page-numbers');
        $pageNumbers.empty();

        var startPage = Math.max(1, currentPage - 2);
        var endPage = Math.min(totalPages, startPage + 4);

        if (startPage > 1) {
            $pageNumbers.append('<a href="#" class="page-number text-gray-300">1</a>');
            if (startPage > 2) {
                $pageNumbers.append('<span class="text-gray-300">...</span>');
            }
        }

        for (var i = startPage; i <= endPage; i++) {
            if (i === currentPage) {
                $pageNumbers.append('<span class="current-page text-gray-800 rounded">' + i + '</span>');
            } else {
                $pageNumbers.append('<a href="#" class="page-number text-gray-300">' + i + '</a>');
            }
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                $pageNumbers.append('<span class="text-gray-300">...</span>');
            }
            $pageNumbers.append('<a href="#" class="page-number text-gray-300">' + totalPages + '</a>');
        }

        $('#prev-page').toggleClass('disabled', currentPage === 1);
        $('#next-page').toggleClass('disabled', currentPage === totalPages);
    }

    function loadPage(page) {
        $.ajax({
            url: window.location.pathname,
            data: {page: page},
            success: function (data) {
                $('tbody').html(data.results);
                currentPage = page;
                updatePagination();
            }
        });
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

    $('td').each(function () {
        var statusElement = $(this).find('.status');
        var statusText = statusElement.text().trim();
        switch (statusText) {
            case 'Being translated':
                statusElement.text('Being translated');
                statusElement.addClass('bg-gray-200 text-gray-800');
                break;
            case 'Translated':
                statusElement.text('Translated');
                statusElement.addClass('bg-gray-200 text-gray-800');
                break;
            case 'Sent to post-editing, not accepted yet':
                statusElement.text('Request for post-editing sent');
                statusElement.addClass('bg-yellow-100 text-yellow-400');
                break;
            case 'Sent to post-editing, accepted':
                statusElement.text('Request for post-editing accepted');
                statusElement.addClass('bg-blue-100 text-blue-400');
                break;
            case 'Post-edited file uploaded':
                statusElement.text('Post-edited file uploaded');
                statusElement.addClass('bg-green-200 text-green-700');
                break;
            case 'Error':
                statusElement.text('Error');
                statusElement.addClass('bg-red-100 text-red-400');
                break;
            default:
                break;
        }
    });

    $('td.created-at').each(function () {
        var dateString = $(this).text().trim();
        var date = new Date(dateString);

        if (!isNaN(date.getTime())) {
            var day = ('0' + date.getDate()).slice(-2);
            var month = ('0' + (date.getMonth() + 1)).slice(-2);
            var year = date.getFullYear();

            var formattedDate = day + '/' + month + '/' + year;

            $(this).text(formattedDate);
        }
    });

    document.getElementById('multiLevelDropdownButton').addEventListener('click', function() {
        var dropdown = document.getElementById('multi-dropdown');
        dropdown.classList.toggle('hidden');
    });
});