$(document).ready(function () {
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
});
