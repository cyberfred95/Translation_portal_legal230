$(document).ready(function () {

    let dateFrom, dateTo;

    function updateLabels() {
        const dateOptions = { year: 'numeric', month: 'long', day: 'numeric' };
        const today = new Date();
        const oneMonthAgo = new Date(today);
        oneMonthAgo.setMonth(today.getMonth() - 1);

        if (!dateFrom) {
            dateFrom = oneMonthAgo;
        }
        if (!dateTo) {
            dateTo = today;
        }

        const formattedDateFrom = dateFrom.toLocaleDateString('en-EN', dateOptions);
        const formattedDateTo = dateTo.toLocaleDateString('en-EN', dateOptions);

        $("#selected-date-from").text(`${formattedDateFrom} /`);
        $("#selected-date-to").text(formattedDateTo);
    }

    $("#datepicker_from").datepicker({
        dateFormat: "mm/dd/yy",
        onSelect: function(dateText) {
            dateFrom = new Date(dateText);
            updateLabels();
            $("#datepicker_to").datepicker("show");
        }
    });

    $("#datepicker_to").datepicker({
        dateFormat: "mm/dd/yy",
        onSelect: function(dateText) {
            dateTo = new Date(dateText);
            if (dateFrom && dateTo < dateFrom) {
                alert('Date to cannot be less than date from.');
                dateTo = null;
                $("#selected-date-to").text('Date to');
            } else {
                updateLabels();
            }
        }
    });

    $("#selected-date-from").on("click", function() {
        $("#datepicker_from").datepicker("show");
    });

    $("#selected-date-to").on("click", function() {
        $("#datepicker_to").datepicker("show");
    });


    $("#prev-button").on("click", function() {
        if (dateFrom) {
            dateFrom.setMonth(dateFrom.getMonth() - 1);
            updateLabels();
        } else {
            dateFrom = new Date();
            dateFrom.setMonth(dateFrom.getMonth() - 1);
            updateLabels();
        }
    });

    $("#next-button").on("click", function() {
        if (dateTo) {
            dateTo.setMonth(dateTo.getMonth() + 1);
            updateLabels();
        } else {
            dateTo = new Date();
            dateTo.setMonth(dateTo.getMonth() + 1);
            updateLabels();
        }
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
            $('#dropdownSearch').addClass('hidden');
        }
        if (!$(event.target).closest('#dropdownSearchh').length) {
            $('#dropdownSearchh').addClass('hidden');
        }
        if (!$(event.target).closest('#dropdownSearchhh').length) {
            $('#dropdownSearchhh').addClass('hidden');
        }
    }

    $(document).on('click', closeDropdown);

    $('#doubleDropdownButton').on('click', function (event) {
        event.stopPropagation();
        $('#dropdownSearch').toggleClass('hidden');
    });

    $('#doubleDropdownButtonn').on('click', function (event) {
        event.stopPropagation();
        $('#dropdownSearchh').toggleClass('hidden');
    });

    $('#doubleDropdownButtonnn').on('click', function (event) {
        event.stopPropagation();
        $('#dropdownSearchhh').toggleClass('hidden');
    });

    $('#multi-dropdown').on('click', function (event) {
        event.stopPropagation();
    });

    let checkedCheckboxes = {
        users: [],
        groups: [],
        files: []
    };

    $('.checkbox-item input[type="checkbox"]').on('change', function () {
        const checkboxId = $(this).attr('id');
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

    // Clear button
    $('#clear-button').on('click', function () {
        $('.checkbox-item input[type="checkbox"]').each(function () {
            $(this).prop('checked', false).trigger('change');
        });

        checkedCheckboxes = { users: [], groups: [], files: [] };
        updateFilterButton(0);
        $('#selected-items').empty().addClass('hidden');
    });

    // Apply button
    $('#apply-button').on('click', function () {
        const selectedCount = Object.values(checkedCheckboxes).flat().length;
        updateFilterButton(selectedCount);
        updateSelectedLabels();
        $('#selected-items').removeClass('hidden');
    });


    function updateSelectedLabels() {
        const selectedItemsLabel = $('#selected-items');
    selectedItemsLabel.empty();

    for (const category in checkedCheckboxes) {
        if (checkedCheckboxes[category].length > 0) {
            let categoryLabel;
            if (category === 'files') {
                categoryLabel = 'File name';
            } else if (category === 'groups') {
                categoryLabel = 'Groups';
            } else if (category === 'users') {
                categoryLabel = 'Users';
            }

            const itemsStr = `${categoryLabel}: ${checkedCheckboxes[category].join(", ")}`;

            const labelElement = $('<span></span>')
                .text(itemsStr)
                .css({
                    display: 'inline-block',
                    border: '1px solid #F2F3F5',
                    borderRadius: '8px',
                    padding: '5px 10px',
                    margin: '5px',
                    backgroundColor: '#F2F3F5',
                    color: 'black',
                    fontFamily: 'Montserrat',
                    fontSize: '13px',
                    whiteSpace: 'nowrap'
                });

            selectedItemsLabel.append(labelElement);

            const removeBtn = $('<span>')
                .append(
                    $('<svg width="10" height="10" viewBox="0 0 10 10" fill="none" xmlns="http://www.w3.org/2000/svg">' +
                        '<path d="M0.947952 9.93744C0.70278 9.9517 0.461663 9.87019 0.275444 9.71011C-0.0918148 9.34067 -0.0918148 8.74399 0.275444 8.37455L8.31722 0.332744C8.6992 -0.0246894 9.29859 -0.00481991 9.65603 0.377162C9.97924 0.722587 9.99808 1.25351 9.70013 1.62096L1.61098 9.71011C1.42716 9.86788 1.18991 9.94923 0.947952 9.93744Z" fill="#0D2B40"/>' +
                        '<path d="M8.98023 9.93746C8.73175 9.9364 8.4936 9.83777 8.31717 9.66278L0.275368 1.62095C-0.0648786 1.22362 -0.0186203 0.625662 0.378708 0.285384C0.733335 -0.0183051 1.25634 -0.0183051 1.61093 0.285384L9.70009 8.32719C10.082 8.68472 10.1017 9.28414 9.74419 9.66603C9.72997 9.68122 9.71528 9.69591 9.70009 9.71013C9.50201 9.88238 9.24134 9.9647 8.98023 9.93746Z" fill="#0D2B40"/>' +
                        '</svg>')
                )
                .css({
                    cursor: 'pointer',
                    marginLeft: '10px',
                    color: 'black',
                    fontSize: '12px',
                    display: 'inline-block'
                })
                .on('click', function () {
                    checkedCheckboxes[category] = [];
                    updateSelectedLabels();

                    $(`input[type="checkbox"][data-category="${category}"]`).prop('checked', false).trigger('change');

                    updateFilterButton(0);
                });

            labelElement.append(removeBtn);
        }
    }

    const selectedCount = Object.values(checkedCheckboxes).flat().length;
    updateFilterButton(selectedCount);
    }

    function updateFilterButton(count) {
        const filterButton = $('#filter-button');
        const dropdownButton = $('#multiLevelDropdownButton');

        if (count > 0) {
            filterButton.html('Filter <span class="filter-count" style="color: black; border: 2px solid white; background-color: white; border-radius: 50%; display: flex; justify-content: center; align-items: center; width: 17px; height: 17px;">' + count + '</span>');

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

    updateLabels();
});
