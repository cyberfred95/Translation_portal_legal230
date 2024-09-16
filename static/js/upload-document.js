$(document).ready(function() {
    var $dropZone = $('.file-upload');
    var $fileInput = $('<input type="file" multiple style="display: none">').appendTo('body');
    var $chooseFileButton = $('.choose-file');
    var $fileList = $('.file-list');
    var $followingButton = $('.upload-document');

    var allowedTypes = ['.txt', '.docx', '.xlsx', '.pptx'];

    $fileInput.on('change', handleFiles);

    $chooseFileButton.on('click', function() {
        $fileInput.click();
    });

    $dropZone.on('dragenter dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).addClass('border-green-700');
        $(this).find('.text-gray-800').text('Drop files here');
    });

    $dropZone.on('dragleave drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('border-green-700');
        $(this).find('.text-gray-800').text('Drag and drop');
    });

    $dropZone.on('drop', function(e) {
        var files = e.originalEvent.dataTransfer.files;
        handleFiles({ target: { files: files } });
    });

    function handleFiles(e) {
        var files = e.target.files;
        var validFiles = [];
        var invalidFiles = [];

        for (var i = 0; i < files.length; i++) {
            var ext = '.' + files[i].name.split('.').pop().toLowerCase();
            if (allowedTypes.indexOf(ext) !== -1) {
                validFiles.push(files[i]);
            } else {
                invalidFiles.push(files[i]);
            }
        }

        if (invalidFiles.length > 0) {
            alert('The following files are not supported and will be ignored: ' +
                invalidFiles.map(f => f.name).join(', '));
        }

        displayFiles(validFiles);
        toggleFollowingButton();
    }

    function displayFiles(files) {
        for (var i = 0; i < files.length; i++) {
            var $fileItem = $(`
                <div class="flex gap-4 items-center px-4 py-3 rounded-md bg-green-200 text-green-700">
                    <span>${files[i].name}</span>
                    <button class="remove-file">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <g clip-path="url(#clip0_759_4082)">
                                <path d="M10 20C15.5229 20 20 15.5229 20 10C20 4.47716 15.5229 0 10 0C4.47716 0 0 4.47716 0 10C0 15.5229 4.47716 20 10 20Z" fill="#176C77"/>
                                <path d="M14.5625 14.5625C14.1875 14.9375 13.5625 14.9375 13.1875 14.5625L9.99998 11.375L6.81249 14.5625C6.43751 14.9375 5.81247 14.9375 5.43749 14.5625C5.0625 14.1875 5.0625 13.5625 5.43749 13.1875L8.62498 9.99998L5.43749 6.81249C5.0625 6.43751 5.0625 5.81247 5.43749 5.43749C5.81247 5.0625 6.43751 5.0625 6.81249 5.43749L9.99998 8.62498L13.1875 5.43749C13.5625 5.0625 14.1875 5.0625 14.5625 5.43749C14.9375 5.81247 14.9375 6.43751 14.5625 6.81249L11.375 9.99998L14.5625 13.1875C14.9375 13.5625 14.9375 14.1874 14.5625 14.5625Z" fill="white"/>
                            </g>
                            <defs>
                                <clipPath id="clip0_759_4082">
                                    <rect width="20" height="20" fill="white"/>
                                </clipPath>
                            </defs>
                        </svg>
                    </button>
                </div>
            `);

            $fileList.append($fileItem);
        }
    }

    $(document).on('click', '.remove-file', function() {
        $(this).closest('.flex.gap-4').remove();
        toggleFollowingButton();
    });

    function toggleFollowingButton() {
        var filesExist = $fileList.children().length > 0;

        if (filesExist) {
            $followingButton.removeClass('hidden').show();
            $fileList.removeClass('hidden').show();
        } else {
            $followingButton.hide();
            $fileList.hide();
        }
    }

    toggleFollowingButton();
});
