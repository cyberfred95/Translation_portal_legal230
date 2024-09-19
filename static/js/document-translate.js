$(document).ready(function () {



    // ------------- SELECT -------------


    $('.js-example-basic-single').select2();

    $('.js-example-basic-single.target-select-language').each(function () {
        var $select = $(this);
        $select.next('.select2-container').addClass('target-select-language');
    });


    // ------------- PROGRESS BAT -------------


    let currentStep = 0;
    const totalSteps = 4;
    let selectedFiles = [];

    function updateProgress(step) {
        let percentage;
        switch (step) {
            case 0:
                percentage = 0;
                break;
            case 1:
                percentage = 26;
                break;
            case 2:
                percentage = 52;
                break;
            case 3:
                percentage = 76;
                break;
            case 4:
                percentage = 100;
                break;
            default:
                percentage = 1;
        }

        $("#progress-bar").css("width", percentage + "%");

        $(".progress-point").parent().find("svg").removeClass("text-green-700").addClass("text-green-400");

        for (let i = 0; i <= step; i++) {
            $(`#point-${i + 1}`).find("svg").removeClass("text-green-400").addClass("text-green-700");
        }
    }

    function showStep(step) {
        $('.border-dashed > div').addClass('hidden');

        $(`.border-dashed > div:eq(${step})`).removeClass('hidden');

        updateProgress(step);

        $("#prev-step").toggleClass('hidden', step === 0);
        $("#next-step").toggleClass('hidden', step === totalSteps);
    }

    $("#next-step").click(function () {
        if (currentStep < totalSteps) {
            if (currentStep === 0) {
                uploadFiles(); // Завантажуємо файли при переході з першого кроку
            }
            currentStep++;
            showStep(currentStep);
        }
    });

    $("#prev-step").click(function () {
        if (currentStep > 0) {
            currentStep--;
            showStep(currentStep);
        }
    });

    showStep(currentStep);

    // ------------- TABS -------------

    $('.tab-content').hide();
    $('#text-translate-content').show();
    $('#text-translate').addClass('bg-gray-800 text-white border-gray-800');

    $('#text-translate, #document-translate, #writing').click(function () {
        $('.tab-content').hide();
        $(`#${this.id}-content`).show();
        $('button').removeClass('bg-gray-800 text-white border-gray-800');
        $(this).addClass('bg-gray-800 text-white border-gray-800');
    });


    // ------------- STEP-1 -------------


    const allowedTypes = ['.txt', '.docx', '.xlsx', '.pptx'];

    const fileInput = $('<input>', {
        type: 'file',
        multiple: true,
        accept: allowedTypes.join(','),
        style: 'display: none'
    }).appendTo('body');

    const $dropZone = $('.file-upload');
    const $chooseFileButton = $('.choose-file');
    const $fileList = $('.file-list');
    const $followingButton = $('.upload-document');

    fileInput.on('change', handleFiles);

    $chooseFileButton.on('click', () => fileInput.click());

    $dropZone.on('dragenter dragover', function (e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).addClass('border-green-700');
        $(this).find('.text-gray-800').text('Drop files here');
    });

    $dropZone.on('dragleave drop', function (e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('border-green-700');
        $(this).find('.text-gray-800').text('Drag and drop');
    });

    $dropZone.on('drop', function (e) {
        handleFiles({target: {files: e.originalEvent.dataTransfer.files}});
    });

    function handleFiles(e) {
        const files = Array.from(e.target.files || e.originalEvent.dataTransfer.files).filter(file => {
            const ext = '.' + file.name.split('.').pop().toLowerCase();
            return allowedTypes.includes(ext);
        });

        selectedFiles = files; // Зберігаємо вибрані файли
        displayFiles(files);
        toggleFollowingButton();
    }

    function uploadFiles() {
        if (selectedFiles.length === 0) {
            console.log("No files selected");
            return;
        }

        const formData = new FormData();
        selectedFiles.forEach((file) => {
            console.log(123);
            formData.append(`document[]`, file);
        });

        $.ajax({
            url: '/en/detect_language/',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            success: function (response) {
                displayDetectLanguageFiles(response.languages);
                console.log("Files uploaded successfully", response.languages);
            },
            error: function (xhr, status, error) {
                console.error("Error uploading files", error);
            }
        });
    }

    function displayFiles(files) {
        files.forEach(file => {
            const $fileItem = $(`
            <div class="flex gap-4 items-center px-4 py-3 rounded-md bg-green-200 text-green-700">
                <span>${file.name}</span>
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
        });
    }

    function displayDetectLanguageFiles(files) {
        const $detectiveLanguageList = $('.detective-language-list');
        $detectiveLanguageList.empty();

        files.forEach(file => {
            const $fileItem = $(`
            <div class="flex gap-5 items-center">
                <div class="flex gap-4 items-center px-4 py-3 rounded-md bg-green-200 text-green-700">
                    <span class="text-3.5 w-50 truncate">${file.file_name}</span>
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
                <div class="flex gap-3 items-center">
                    <svg width="6" height="10" viewBox="0 0 6 10" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M5.71393 4.28962C5.6637 4.23904 5.6081 4.19635 5.55034 4.15922L1.67443 0.283488C1.29615 -0.0944361 0.683075 -0.0946154 0.304613 0.283667C-0.0736695 0.66177 -0.0736695 1.27502 0.304613 1.65348L3.64279 4.9913L0.287753 8.3467C-0.0907092 8.72462 -0.0907092 9.33805 0.287753 9.71651C0.476983 9.90539 0.724687 9.99991 0.972392 9.99991C1.2201 9.99991 1.46834 9.90539 1.65703 9.71615L5.55034 5.82338C5.6081 5.78625 5.66352 5.74374 5.71393 5.69298C5.90764 5.49926 6.00055 5.24492 5.99625 4.9913C6.00073 4.7375 5.90764 4.4828 5.71393 4.28962Z" fill="#9EAAB3"/>
                    </svg>
                    <select class="js-example-basic-single gray-text-select" name="source_language" required data-default-value="${file.abbreviation.toLowerCase()}">
                        ${getLanguageOptions(file.abbreviation)}
                    </select>
                </div>
            </div>
        `);

            $detectiveLanguageList.append($fileItem);

            $fileItem.find('.js-example-basic-single').select2().each(function() {
                var $select = $(this);
                var defaultValue = $select.data('default-value');

                $select.next('.select2-container').addClass('gray-text-select');

                if (defaultValue) {
                    $select.val(defaultValue).trigger('change');
                }

                function updateDetectedText() {
                    var $selectedOption = $select.find('option:selected');
                    var text = $selectedOption.text().replace(' (detected)', '');

                    $select.find('option').each(function () {
                        $(this).text($(this).text().replace(' (detected)', ''));
                    });

                    if (defaultValue && $selectedOption.val() === defaultValue) {
                        var newText = text + ' <span class="detected-text">(detected)</span>';
                        $selectedOption.text(text + ' (detected)');
                        $select.next('.select2-container').find('.select2-selection__rendered').html(newText);
                    } else {
                        $select.next('.select2-container').find('.select2-selection__rendered').text(text);
                    }
                }

                updateDetectedText();

                $select.on('select2:select', function (e) {
                    updateDetectedText();
                });
            });
        });
    }

    function getLanguageOptions(defaultValue) {
        console.log('languages', languages);
        return languages.map(lang =>
            `<option value="${lang.abbreviation.toLowerCase()}" ${lang.abbreviation === defaultValue ? 'selected' : ''}>
            ${lang.name}
        </option>`
        ).join('');
    }

    $(document).on('click', '.remove-file', function () {
        $(this).closest('.flex.gap-4').remove();
        toggleFollowingButton();
    });

    function toggleFollowingButton() {
        const filesExist = $fileList.children().length > 0;
        $followingButton.toggleClass('hidden', !filesExist);
        $fileList.toggleClass('hidden', !filesExist);
    }

    toggleFollowingButton();
});
