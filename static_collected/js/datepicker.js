$(document).ready(function () {
    let currentDate = new Date();
    let startDate = null;
    let endDate = null;
    const monthsToRender = 24;
    let initialRender = true;
    const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

    function closeCalendar(event) {
        if (!$(event.target).closest('#datepicker, .calendar label').length) {
            $('#datepicker').addClass('hidden');
        }
    }

    $(document).on('click', closeCalendar);

    $('.calendar label').on('click', function (event) {
        event.stopPropagation();
        $('#datepicker').toggleClass('hidden');
    });

    function getUrlParameter(name) {
        name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
        var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
        var results = regex.exec(location.search);
        return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
    }

    function updateUrlWithDates() {
        var searchParams = new URLSearchParams(window.location.search);
        if (startDate) searchParams.set('date_from', formatDateForUrl(startDate));
        if (endDate) searchParams.set('date_to', formatDateForUrl(endDate));
        if (endDate) searchParams.set('page', '1');
        var newRelativePathQuery = window.location.pathname + '?' + searchParams.toString();
        history.pushState(null, '', newRelativePathQuery);
    }

    function formatDateForUrl(date) {
        return date.getFullYear() + '-' + padZero(date.getMonth() + 1) + '-' + padZero(date.getDate());
    }

    function setDefaultDateRange() {
        var fromDateStr = getUrlParameter('date_from');
        var toDateStr = getUrlParameter('date_to');

        if (fromDateStr && toDateStr) {
            startDate = new Date(fromDateStr);
            endDate = new Date(toDateStr);
            currentDate = new Date(startDate);
        } else {
            startDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
            endDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
        }
        updateInputs();
    }

    function renderCalendar() {
        let calendarHTML = '';
        const selectedYear = currentDate.getFullYear();
        const selectedMonth = currentDate.getMonth();

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
                        <span class="text-4 font-semibold text-gray-575">${firstDay.toLocaleString('default', { month: 'long', year: 'numeric' })}</span>
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
                    const dateWithoutTime = date.setHours(0, 0, 0, 0);
                    const startDateWithoutTime = startDate ? new Date(startDate).setHours(0, 0, 0, 0) : null;
                    const endDateWithoutTime = endDate ? new Date(endDate).setHours(0, 0, 0, 0) : null;

                    const isInRange = startDateWithoutTime && endDateWithoutTime &&
                        dateWithoutTime >= startDateWithoutTime &&
                        dateWithoutTime <= endDateWithoutTime;
                    const isStartDate = startDateWithoutTime && dateWithoutTime === startDateWithoutTime;
                    const isEndDate = endDateWithoutTime && dateWithoutTime === endDateWithoutTime;
                    const isRangeEnd = isStartDate || isEndDate;

                    calendarHTML += `
    <div class="h-10 relative flex items-center justify-center cursor-pointer bg-white overflow-hidden"
         data-date="${date.toISOString()}">
        <div class="absolute inset-x-0 top-1/2 transform -translate-y-1/2 h-3/4 ${isStartDate ? 'w-1/2 right-0 translate-x-full' : ''} ${isEndDate ? 'w-1/2 left-0' : ''} ${isInRange ? 'bg-green-150' : ''}"></div>
        ${isRangeEnd ? `<div class="absolute inset-0 bg-green-350 rounded-4"></div>` : ''}
        <span class="z-10 relative px-2 py-1 rounded-4 ${isInRange && !isRangeEnd ? 'text-green-350' : ''} 
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

    function updateMonthYearDisplay() {
        $('#currentMonth').text(months[currentDate.getMonth()]);
        $('#currentYear').text(currentDate.getFullYear());
    }

    function initializeMonthYearNavigation() {
        updateMonthYearDisplay();

        $('#prevMonth').click(function () {
            currentDate.setMonth(currentDate.getMonth() - 1);
            updateMonthYearDisplay();
            renderCalendar();
        });

        $('#nextMonth').click(function () {
            currentDate.setMonth(currentDate.getMonth() + 1);
            updateMonthYearDisplay();
            renderCalendar();
        });

        $('#prevYear').click(function () {
            currentDate.setFullYear(currentDate.getFullYear() - 1);
            updateMonthYearDisplay();
            renderCalendar();
        });

        $('#nextYear').click(function () {
            currentDate.setFullYear(currentDate.getFullYear() + 1);
            updateMonthYearDisplay();
            renderCalendar();
        });
    }

    setDefaultDateRange();
    renderCalendar();
    initializeMonthYearNavigation();

    $(document).on('click', '#calendarContent .cursor-pointer', function (event) {
        event.stopPropagation();
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
        updateUrlWithDates();

        if (startDate && endDate) {
            renderCalendar();
            window.location.reload();
        } else {
            renderCalendar();
        }
    });

    $('#fromDate, #toDate').on('input', function () {
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
                updateMonthYearDisplay();
                updateUrlWithDates();
                window.location.reload();
            }
        }
    });

    $('#calendarContainer').on('scroll', function () {
        const $this = $(this);
        const scrollThreshold = 0;

        if ($this.scrollTop() + $this.innerHeight() >= $this[0].scrollHeight - scrollThreshold) {
            const lastMonth = new Date(currentDate);
            lastMonth.setMonth(lastMonth.getMonth() + monthsToRender);
            currentDate = new Date(lastMonth);
            updateMonthYearDisplay();
            renderCalendar();
            $this.scrollTop($this.scrollTop() - 100);
        } else if ($this.scrollTop() <= scrollThreshold) {
            const firstMonth = new Date(currentDate);
            firstMonth.setMonth(firstMonth.getMonth() - 1);
            if (firstMonth >= new Date(currentDate.getFullYear() - 10, 0, 1)) {
                currentDate = new Date(firstMonth);
                updateMonthYearDisplay();
                renderCalendar();
                $this.scrollTop($this.scrollTop() + 100);
            }
        }
    });
});
