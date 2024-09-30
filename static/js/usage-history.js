$(document).ready(function () {

    let dateFrom, dateTo;
    
    function updateLabels() {
        const months = ["January", "February", "March", "April", "May", "June", 
                        "July", "August", "September", "October", "November", "December"];
    
        if (dateFrom) {
            const fromMonth = months[dateFrom.getMonth()];
            $("#selected-date-from").text(`${fromMonth} ${dateFrom.getDate()}, ${dateFrom.getFullYear()} /`);
        } else {
            $("#selected-date-from").text('Date from /');
        }
    
        if (dateTo) {
            const toMonth = months[dateTo.getMonth()];
            $("#selected-date-to").text(`${toMonth} ${dateTo.getDate()}, ${dateTo.getFullYear()}`);
        } else {
            $("#selected-date-to").text('Date to');
        }
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
            updateLabels();
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
    
    
        // Toggle dropdown for multiLevelDropdownButton
        $('#multiLevelDropdownButton').on('click', function () {
            $('#multi-dropdown').toggleClass('hidden');
        });
    
        function toggleDropdown(buttonId, dropdownId) {
            $('#' + dropdownId).toggleClass('hidden');
        }
    
        $('#doubleDropdownButton').on('click', function () {
            toggleDropdown('doubleDropdownButton', 'dropdownSearch');
            $('#dropdownArrow').toggleClass('rotate-180');
        });
    
        $('#doubleDropdownButtonn').on('click', function () {
            toggleDropdown('doubleDropdownButtonn', 'dropdownSearchh');
            $('#dropdownArroww').toggleClass('rotate-180');
        });
    
        $('#doubleDropdownButtonnn').on('click', function () {
            toggleDropdown('doubleDropdownButtonnn', 'dropdownSearchhh');
            $('#dropdownArrowww').toggleClass('rotate-180');
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
    
    function updateFilterButton(count) {
        const filterButton = $('#filter-button');
        if (count > 0) {
            filterButton.html('Filter <span class="filter-count" style="color: black; border: 2px solid white; background-color: white; border-radius: 50%; display: flex; justify-content: center; align-items: center; width: 17px; height: 17px;">' + count + '</span>');
        } else {
            filterButton.text('Filter');
        }
    }
    
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

                const itemsStr = checkedCheckboxes[category].join(", ");
    
                const label = $('<span></span>')
                    .text(`${capitalizeFirstLetter(category)}: ${itemsStr}`)
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
    
                selectedItemsLabel.append(label);
    
                const removeBtn = $('<span></span>')
                    .text(' X')
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
    
                label.append(removeBtn);
            }
        }
    
        const selectedCount = Object.values(checkedCheckboxes).flat().length;
        updateFilterButton(selectedCount);
    }
    
    function capitalizeFirstLetter(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
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
            
});
    