$(document).ready(function () {


    // ------------- PROGRESS BAT -------------


    let currentStep = 0;
    const totalSteps = 4;

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
        const files = Array.from(e.target.files).filter(file => {
            const ext = '.' + file.name.split('.').pop().toLowerCase();
            return allowedTypes.includes(ext);
        });

        displayFiles(files);
        toggleFollowingButton();
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


    // ------------- SELECT -------------


    $('.js-example-basic-single').select2();

    $('.js-example-basic-single.target-select-language').each(function () {
        var $select = $(this);
        $select.next('.select2-container').addClass('target-select-language');
    });

    $('.js-example-basic-single.gray-text-select').each(function () {
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
