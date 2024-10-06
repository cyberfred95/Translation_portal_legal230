$(document).ready(function() {
    $('.calendar label').on('click', function() {
        $('#datepicker').toggleClass('hidden');
    });


    $(document).on('click', function(event) {
        if (!$(event.target).closest('#datepicker, .calendar').length) {
            $('#datepicker').addClass('hidden');
        }
    });

    let currentDate = new Date();
    let startDate = null;
    let endDate = null;
    const monthsToRender = 24; // Кількість місяців для рендерингу (2 роки)
    let initialRender = true;

    function initializeSelects() {
        const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
        const currentYear = currentDate.getFullYear();
        const currentMonth = currentDate.getMonth();

        $('#monthSelect').html(months.map((month, index) =>
            `<option value="${index}" ${index === currentMonth ? 'selected' : ''}>${month}</option>`
        ));

        for (let year = currentYear - 10; year <= currentYear + 10; year++) {
            $('#yearSelect').append(`<option value="${year}" ${year === currentYear ? 'selected' : ''}>${year}</option>`);
        }

        setDefaultDateRange();
    }

    function setDefaultDateRange() {
        const year = parseInt($('#yearSelect').val());
        const month = parseInt($('#monthSelect').val());
        startDate = new Date(year, month, 1);
        endDate = new Date(year, month + 1, 0);
        updateInputs();
    }

    function renderCalendar() {
        let calendarHTML = '';
        const selectedYear = parseInt($('#yearSelect').val());
        const selectedMonth = parseInt($('#monthSelect').val());

        for (let i = 0; i < monthsToRender; i++) {
            const currentMonthDate = new Date(selectedYear, selectedMonth + i, 1);
            const year = currentMonthDate.getFullYear();
            const month = currentMonthDate.getMonth();
            const firstDay = new Date(year, month, 1);
            const lastDay = new Date(year, month + 1, 0);
            const daysInMonth = lastDay.getDate();
            const startingDay = firstDay.getDay();

            calendarHTML += `
                <div>
                    <div class="text-left mb-2">
                        <span class="text-4 font-semibold text-gray-750">${firstDay.toLocaleString('default', { month: 'long', year: 'numeric' })}</span>
                    </div>
                    <div class="grid grid-cols-7">
            `;

            let dayCount = 1;
            const totalSlots = 42;

            for (let j = 0; j < totalSlots; j++) {
                if (j < startingDay || dayCount > daysInMonth) {
                    calendarHTML += `<div class="h-10 bg-white"></div>`;
                } else {
                    const date = new Date(year, month, dayCount);
                    const isInRange = startDate && endDate && date >= startDate && date <= endDate;
                    const isRangeEnd = (date.getTime() === startDate?.getTime() || date.getTime() === endDate?.getTime());

                    calendarHTML += `
    <div class="h-10 relative flex items-center justify-center cursor-pointer bg-white overflow-hidden"
         data-date="${date.toISOString()}">
        <div class="absolute inset-x-0 top-1/2 transform -translate-y-1/2 h-3/4 ${isInRange ? 'bg-green-200' : ''}"></div>
        ${isRangeEnd ? `<div class="absolute inset-0 bg-green-380 rounded-4"></div>` : ''}
        <span class="z-10 relative px-2 py-1 rounded-4 ${isInRange && !isRangeEnd ? 'text-green-380' : ''} 
                     ${isRangeEnd ? '!text-white' : ''} text-4">
            ${dayCount}
        </span>
    </div>
`;
                    dayCount++;
                }
            }

            calendarHTML += '</div></div>';
        }

        $('#calendarContent').html(calendarHTML);

        if (initialRender) {
            const $container = $('#calendarContainer');
            $container.scrollTop(0);
            initialRender = false;
        }
    }

    function updateSelects() {
        $('#monthSelect').val(currentDate.getMonth());
        $('#yearSelect').val(currentDate.getFullYear());
    }

    function updateInputs() {
        $('#fromDate').val(startDate ? formatDate(startDate) : '');
        $('#toDate').val(endDate ? formatDate(endDate) : '');
    }

    function formatDate(date) {
        return `${padZero(date.getDate())}/${padZero(date.getMonth() + 1)}/${date.getFullYear()}`;
    }

    function padZero(num) {
        return num.toString().padStart(2, '0');
    }

    function parseInputDate(inputValue) {
        const parts = inputValue.split('/');
        if (parts.length === 3) {
            return new Date(parts[2], parts[1] - 1, parts[0]);
        }
        return null;
    }

    initializeSelects();
    renderCalendar();

    $('#monthSelect, #yearSelect').on('change', function() {
        currentDate = new Date($('#yearSelect').val(), $('#monthSelect').val(), 1);
        setDefaultDateRange();
        renderCalendar();
    });

    $(document).on('click', '#calendarContent .cursor-pointer', function() {
        const clickedDate = new Date($(this).data('date'));
        if (!startDate || (startDate && endDate)) {
            startDate = clickedDate;
            endDate = null;
        } else if (clickedDate < startDate) {
            endDate = startDate;
            startDate = clickedDate;
        } else {
            endDate = clickedDate;
        }
        updateInputs();
        renderCalendar();
    });

    $('#fromDate, #toDate').on('input', function() {
        const fromValue = $('#fromDate').val();
        const toValue = $('#toDate').val();

        if (fromValue && toValue) {
            startDate = parseInputDate(fromValue);
            endDate = parseInputDate(toValue);
            if (startDate && endDate) {
                if (startDate > endDate) {
                    [startDate, endDate] = [endDate, startDate];
                    updateInputs();
                }
                currentDate = new Date(startDate);
                updateSelects();
                renderCalendar();
            }
        }
    });

    $('#calendarContainer').on('scroll', function() {
        const $this = $(this);
        const scrollThreshold = 50;

        if ($this.scrollTop() + $this.innerHeight() >= $this[0].scrollHeight - scrollThreshold) {
            const lastMonth = new Date(currentDate);
            lastMonth.setMonth(lastMonth.getMonth() + monthsToRender);
            currentDate = new Date(lastMonth);
            updateSelects();
            renderCalendar();
            $this.scrollTop($this.scrollTop() - 100);
        } else if ($this.scrollTop() <= scrollThreshold) {
            const firstMonth = new Date(currentDate);
            firstMonth.setMonth(firstMonth.getMonth() - 1);
            if (firstMonth >= new Date(currentDate.getFullYear() - 10, 0, 1)) {
                currentDate = new Date(firstMonth);
                updateSelects();
                renderCalendar();
                $this.scrollTop($this.scrollTop() + 100);
            }
        }
    });
});
