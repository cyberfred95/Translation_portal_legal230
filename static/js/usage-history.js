$(document).ready(function () {

    let dateFrom, dateTo;
    const currentUrl = new URL(window.location.href);

    function getMonthDates(year, month) {
        const firstDay = new Date(Date.UTC(year, month, 1));
        const lastDay = new Date(Date.UTC(year, month + 1, 0));
        return {firstDay, lastDay};
    }

    function formatDateForURL(date) {
        return date.toISOString().split('T')[0];
    }

    function updateLabels(isChange = false) {
        const dateOptions = {year: 'numeric', month: 'long', day: 'numeric'};

        if (!isChange) {
            const urlDateFrom = currentUrl.searchParams.get('date_from');
            const urlDateTo = currentUrl.searchParams.get('date_to');

            if (urlDateFrom && urlDateTo) {
                dateFrom = new Date(urlDateFrom);
                dateTo = new Date(urlDateTo);
            } else {
                const today = new Date();
                const {firstDay, lastDay} = getMonthDates(today.getFullYear(), today.getMonth());
                dateFrom = firstDay;
                dateTo = lastDay;
            }

            updateURLParams();
        }

        $("#selected-date-from").text(`${dateFrom.toLocaleDateString('en-EN', dateOptions)} /`);
        $("#selected-date-to").text(dateTo.toLocaleDateString('en-EN', dateOptions));
    }

    function updateURLParams() {
        currentUrl.searchParams.set('date_from', formatDateForURL(dateFrom));
        currentUrl.searchParams.set('date_to', formatDateForURL(dateTo));
        window.history.pushState({}, '', currentUrl.toString());
    }

    function navigateMonth(direction) {
        const currentMonth = dateFrom.getUTCMonth();
        const currentYear = dateFrom.getUTCFullYear();
        const newMonth = direction === 'next' ? currentMonth + 1 : currentMonth - 1;
        const {firstDay, lastDay} = getMonthDates(currentYear, newMonth);

        dateFrom = firstDay;
        dateTo = lastDay;
        currentUrl.searchParams.set('page', '1');
        window.history.pushState({}, '', currentUrl.toString());
        updateURLParams();
        updateLabels(true);
        window.location.reload();
    }

    $("#prev-button").on("click", function () {
        navigateMonth('prev');
    });

    $("#next-button").on("click", function () {
        navigateMonth('next');
    });

    $('#multiLevelDropdownButton').on('click', function (event) {
        event.stopPropagation();
        $('#multi-dropdown').toggleClass('hidden');
    });

    function closeDropdown(event) {
        if (!$(event.target).closest('#multi-dropdown').length) {
            $('#multi-dropdown').addClass('hidden');
        }

        if (!$(event.target).closest('#dropdownSearch').length) {
            $('#dropdownArrow').removeClass('rotate-180');
            $('#dropdownSearch').addClass('hidden');
        }

        if (!$(event.target).closest('#dropdownSearchh').length) {
            $('#dropdownArroww').removeClass('rotate-180');
            $('#dropdownSearchh').addClass('hidden');
        }

        if (!$(event.target).closest('#dropdownSearchhh').length) {
            $('#dropdownArrowww').removeClass('rotate-180');
            $('#dropdownSearchhh').addClass('hidden');
        }
    }

    $(document).on('click', closeDropdown);

    $('#doubleDropdownButton').on('click', function (event) {
        event.stopPropagation();
        $('#dropdownArrow').toggleClass('rotate-180');
        $('#dropdownSearch').toggleClass('hidden');
    });

    $('#doubleDropdownButtonn').on('click', function (event) {
        event.stopPropagation();
        $('#dropdownArroww').toggleClass('rotate-180');
        $('#dropdownSearchh').toggleClass('hidden');
    });

    $('#doubleDropdownButtonnn').on('click', function (event) {
        event.stopPropagation();
        $('#dropdownArrowww').toggleClass('rotate-180');
        $('#dropdownSearchhh').toggleClass('hidden');
    });

    $('#multi-dropdown').on('click', function (event) {
        event.stopPropagation();
    });

    let checkedCheckboxes = {
        user: [],
        group: [],
        file_name: [],
    };

    function initializeFromURL() {
        for (const category in checkedCheckboxes) {
            const params = currentUrl.searchParams.getAll(category);
            checkedCheckboxes[category] = params;

            params.forEach(param => {
                $(`input[type="checkbox"][data-category="${category}"][value="${param}"]`).prop('checked', true);
            });
        }
        updateSelectedLabels();
    }

    $('.checkbox-item input[type="checkbox"]').on('change', function () {
        const label = $(this).next('label').text();
        const category = $(this).data('category');

        if ($(this).is(':checked')) {
            if (!checkedCheckboxes[category].includes(label)) {
                checkedCheckboxes[category].push(label);
            }
        } else {
            checkedCheckboxes[category] = checkedCheckboxes[category].filter(item => item !== label);
        }
    });

    $('#clear-button').on('click', function () {
        $('.checkbox-item input[type="checkbox"]').prop('checked', false).trigger('change');

        checkedCheckboxes = {user: [], group: [], file_name: []};

        ['file_name', 'group', 'user'].forEach(category => {
            currentUrl.searchParams.delete(category);
        });

        window.history.pushState({}, '', currentUrl.toString());

        updateFilterButton(0);
        $('#selected-items').empty().addClass('hidden');

        updateSelectedLabels();

        window.location.reload();
    });

    $('#apply-button').on('click', function () {
        const selectedCount = Object.values(checkedCheckboxes).flat().length;
        if (selectedCount > 0) {
            updateFilterButton(selectedCount);
            updateSelectedLabels();
            window.location.reload();
        }
    });

    function updateSelectedLabels() {
        const selectedItemsLabel = $('#selected-items');
        selectedItemsLabel.empty();

        ['file_name', 'group', 'user'].forEach(category => {
            currentUrl.searchParams.delete(category);
        });

        for (const category in checkedCheckboxes) {
            if (checkedCheckboxes[category].length > 0) {
                let categoryLabel;
                if (category === 'file_name') {
                    categoryLabel = 'File name';
                } else if (category === 'group') {
                    categoryLabel = 'Groups';
                } else if (category === 'user') {
                    categoryLabel = 'Users';
                }

                checkedCheckboxes[category].forEach(item => {
                    currentUrl.searchParams.append(category, item);
                });

                const itemsStr = `${categoryLabel}: ${checkedCheckboxes[category].join(", ")}`;

                const labelElement = $('<span class="bg-gray-100 rounded-2.5 px-2 py-1.5 text-3.25 whitespace-nowrap mr-2.5 flex items-center"></span>')
                    .text(itemsStr);

                selectedItemsLabel.append(labelElement);

                const removeBtn = $('<span>')
                    .append(
                        $('<svg width="10" height="10" viewBox="0 0 10 10" fill="none" xmlns="http://www.w3.org/2000/svg" class="cursor-pointer ml-2.5 text-black flex items-center">' +
                            '<path d="M0.947952 9.93744C0.70278 9.9517 0.461663 9.87019 0.275444 9.71011C-0.0918148 9.34067 -0.0918148 8.74399 0.275444 8.37455L8.31722 0.332744C8.6992 -0.0246894 9.29859 -0.00481991 9.65603 0.377162C9.97924 0.722587 9.99808 1.25351 9.70013 1.62096L1.61098 9.71011C1.42716 9.86788 1.18991 9.94923 0.947952 9.93744Z" fill="#0D2B40"/>' +
                            '<path d="M8.98023 9.93746C8.73175 9.9364 8.4936 9.83777 8.31717 9.66278L0.275368 1.62095C-0.0648786 1.22362 -0.0186203 0.625662 0.378708 0.285384C0.733335 -0.0183051 1.25634 -0.0183051 1.61093 0.285384L9.70009 8.32719C10.082 8.68472 10.1017 9.28414 9.74419 9.66603C9.72997 9.68122 9.71528 9.69591 9.70009 9.71013C9.50201 9.88238 9.24134 9.9647 8.98023 9.93746Z" fill="#0D2B40"/>' +
                            '</svg>')
                    )
                    .on('click', function () {
                        checkedCheckboxes[category] = [];
                        $(`input[type="checkbox"][data-category="${category}"]`).prop('checked', false);
                        updateSelectedLabels();
                        window.location.reload();
                    });

                labelElement.append(removeBtn);
            }
        }

        window.history.pushState({}, '', currentUrl.toString());

        const selectedCount = Object.values(checkedCheckboxes).flat().length;
        updateFilterButton(selectedCount);

        if (selectedCount === 0) {
            selectedItemsLabel.addClass('hidden');
        } else {
            selectedItemsLabel.removeClass('hidden');
        }
    }

    function updateFilterButton(count) {
        const filterButton = $('#filter-button');
        const dropdownButton = $('#multiLevelDropdownButton');

        if (count > 0) {
            $('#selected-items').removeClass('hidden');
            filterButton.html('Filter <span class="filter-count bg-white text-black text-3 rounded-full flex items-center justify-center w-5 h-5">' + count + '</span>');

            dropdownButton.css('width', 'auto');
        } else {
            filterButton.text('Filter');

            dropdownButton.css('width', '64px');
        }
    }

    $('#input-user-search').on('keyup', function () {
        filterItems($(this), 'user-list');
    });
    $('#input-group-search').on('keyup', function () {
        filterItems($(this), 'group-list');
    });
    $('#input-file-search').on('keyup', function () {
        filterItems($(this), 'file-list');
    });

    function filterItems(searchInput, listId) {
        var filter = searchInput.val().toLowerCase();
        var list = $('#' + listId).find('li');

        list.each(function () {
            var label = $(this).find('label').eq(0);
            var textValue = label.text();

            if (textValue.toLowerCase().indexOf(filter) > -1) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    }

    initializeFromURL();
    updateLabels(false);
});
