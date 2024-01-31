document.addEventListener('DOMContentLoaded', function () {

    var pagination = document.querySelector('.pagination');
    var arrowsPagination = document.querySelectorAll('.page-arrow');

    var totalPages = parseInt(pagination.getAttribute('data-value'), 10);
    var currentPage = getCurrentPage();

    var maxPagesToShow = 3;

    createPageNumber(currentPage);

    function getCurrentPage() {
        var urlParams = new URLSearchParams(window.location.search);
        return parseInt(urlParams.get('page')) || 1;
    }

    arrowsPagination.forEach((arrow) => {
        arrow.addEventListener('click', function () {
            var direction = arrow.getAttribute('data-direction');
            if (direction === 'next' && currentPage < totalPages) {
                currentPage += 1;
            } else if (direction === 'previous' && currentPage !== 1) {
                currentPage -= 1;
            } else if (direction === 'end') {
                currentPage = totalPages;
            } else if (direction === 'start') {
                currentPage = 1;
            }

            updatePagination();
            window.location.href = '/project-history/?page=' + currentPage + '#tabs-4';
        });

    });


    var numbersContainer = document.createElement('div');
    numbersContainer.className = 'numbers-container';

    function createPageNumber(pageNum) {
        var pageNumber = document.createElement('div');
        pageNumber.className = 'page-number' + (pageNum === currentPage ? ' active' : '');
        pageNumber.textContent = pageNum;

        pageNumber.addEventListener('click', function () {
            document.querySelectorAll('.page-number').forEach(function (page) {
                page.classList.remove('active');
            });

            pageNumber.classList.add('active');

            window.location.href = '/project-history/?page=' + pageNum + '#tabs-4';
        });

        return pageNumber;
    }

    function updatePagination() {

        if (totalPages < 7) {

            document.querySelectorAll('.page-number').forEach(function (page) {
                page.classList.remove('active');
            });

            var startPage = Math.max(Math.min(currentPage, totalPages - maxPagesToShow + 1), 1);
            var endPage = Math.min(startPage + maxPagesToShow - 1, totalPages);

            numbersContainer.innerHTML = '';

            for (var i = startPage; i <= endPage; i++) {
                numbersContainer.appendChild(createPageNumber(i));
            }
        } else {
            numbersContainer.innerHTML = ''; // Очищаємо попередні номери сторінок

            for (var i = 1; i <= 3; i++) {
                numbersContainer.appendChild(createPageNumber(i));
            }

            if (currentPage > 4) {
                numbersContainer.appendChild(createEllipsis());
            }

            var startPage = Math.max(currentPage - 1, 4);
            var endPage = Math.min(currentPage + 1, totalPages - 3);

            for (var i = startPage; i <= endPage; i++) {
                numbersContainer.appendChild(createPageNumber(i));
            }

            if (currentPage < totalPages - 3) {
                numbersContainer.appendChild(createEllipsis());
            }

            for (var i = totalPages - 2; i <= totalPages; i++) {
                numbersContainer.appendChild(createPageNumber(i));
            }

            var previousArrow = pagination.querySelector('.page-arrow[data-direction="previous"]');
            pagination.insertBefore(numbersContainer, previousArrow.nextSibling);
        }
    }

    function createEllipsis() {
        var ellipsis = document.createElement('div');
        ellipsis.className = 'page-dots';
        ellipsis.textContent = '...';
        return ellipsis;
    }

    updatePagination(); // Перший виклик для ініціалізації пагінації

    if (totalPages > maxPagesToShow) {
        var startPage = Math.max(currentPage - 2, 1);
        var endPage = Math.min(startPage + maxPagesToShow - 1, totalPages);

        for (var i = startPage; i <= endPage; i++) {
            numbersContainer.appendChild(createPageNumber(i));
        }
    } else {
        for (var i = 1; i <= totalPages; i++) {
            numbersContainer.appendChild(createPageNumber(i));
        }
    }

    if (totalPages > 1) {
        var endArrow = pagination.querySelector('.page-arrow[data-direction="next"]');
        pagination.insertBefore(numbersContainer, endArrow);

        updatePagination();
    } else {
        pagination.style.display = 'none';
    }
});
