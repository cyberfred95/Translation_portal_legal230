$(document).ready(function () {
    let sourceLanguage = '';
    let targetLanguage = '';
    let selectedDomain = '';
    let selectedSubDomain = '';
    let defaultDomain = false;
    let selectedGlossaryType = 'default';
    let selectedGlossary = '';
    let glossaryFile = '';
    let selectedFiles = [];

    const nextStep = $("#next-step");
    const prevStep = $("#prev-step");


    // ------------- PROGRESS BAT -------------


    let currentStep = 0;

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

        $(".progress-point").parent().find("svg").removeClass("text-green-400").addClass("text-green-250");
        $(".progress-point").parent().find(".text-3\\.25, .text-xs").removeClass("text-green-400").addClass("text-green-200");

        $("#point-1").find("svg").removeClass("text-green-250").addClass("text-green-400");
        $("#point-1").find(".text-3\\.25, .text-xs").removeClass("text-green-200").addClass("text-green-400");

        for (let i = 0; i <= step; i++) {
            $(`#point-${i + 1}`).find("svg").removeClass("text-green-250").addClass("text-green-400");
            $(`#point-${i + 1}`).find(".text-3\\.25, .text-xs").removeClass("text-green-200").addClass("text-green-400");

        }
    }

    function showStep(step) {
        $('.border-line > div').addClass('hidden');
        $(`.border-line > div:eq(${step})`).removeClass('hidden');

        updateProgress(step);

        const $actionList = $(".action-list");

        if (step === 0) {
            prevStep.hide();
            $("#restart").hide();
            $("#restart-text").hide();

            if (selectedFiles.length > 0) {
                nextStep.show().text(language_code === 'en' ? "Next" : "Suivant");
                $actionList.css("justify-content", "flex-end");
            } else {
                nextStep.hide();
            }
        } else if (currentStep === 4) {
            prevStep.hide();
            nextStep.hide();
            $("#restart").show().text(language_code === 'en' ? "New translation" : "Nouveau document");
            $("#restart-text").show();

            $actionList.css("justify-content", "flex-start");
        } else {
            prevStep.show();
            nextStep.show().text(language_code === 'en' ? "Next" : "Suivant");
            $("#restart").hide();
            $("#restart-text").hide();

            $actionList.css("justify-content", "space-between");
        }

        prevStep.toggleClass('hidden', step === 0);
        nextStep.toggleClass('hidden', step === 4);
    }

    nextStep.click(function () {
        if (currentStep === 0 && selectedFiles.length === 0) {
            return;
        }
        if (currentStep === 0) {
            detectLanguageFiles();
            checkLanguagesConsistency()
        }
        if (currentStep === 1) {
            targetLanguage = $('.document-target-language').val();
            getDomainsGroups();
        }
        if (currentStep === 2) {
            if (!defaultDomain) {
                loadDefaultGlossary();
                $(".step-4 .default").addClass('bg-gray-600 text-white');
            } else {
                loadMyGlossaries();
                $(".step-4 .my-glossary").addClass('bg-gray-600 text-white');
            }
            $('.terminology-step').text('default').removeClass('hidden');

        }
        if (currentStep === 3) {
            fileTranslate();
        }
        currentStep++;
        showStep(currentStep);
    });

    prevStep.click(function () {
        if (currentStep > 0) {
            currentStep--;
            showStep(currentStep);
            nextStep.removeClass('border-gray-225 text-gray-225 pointer-events-none').addClass('border-green-700 text-green-700').prop("disabled", false);

            $('.step-container').removeClass('bg-red-100 border-red-200');
        }
    });

    $("#restart").click(function () {
        window.location.reload();
    });

    showStep(currentStep);


    // ------------- STEP-1 -------------


    const allowedTypes = ['.txt', '.pdf', '.docx', '.xlsx', '.pptx'];

    const fileInput = $('<input>', {
        type: 'file',
        multiple: true,
        accept: allowedTypes.join(','),
        style: 'display: none'
    }).appendTo('body');

    const $dropZone = $('.file-upload');
    const $chooseFileButton = $('.choose-file');
    const $fileList = $('.file-list');

    fileInput.on('change', handleFiles);

    $chooseFileButton.on('click', () => fileInput.click());

    $dropZone.on('dragenter dragover', function (e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).addClass('border-green-500');
        $(this).find('.text-gray-600').text('Drop files here');
    });

    $dropZone.on('dragleave drop', function (e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('border-green-500');
        $(this).find('.text-gray-600').text('Drag and drop');
    });

    $dropZone.on('drop', function (e) {
        handleFiles({target: {files: e.originalEvent.dataTransfer.files}});
    });

    function handleFiles(e) {
        const files = Array.from(e.target.files || e.originalEvent.dataTransfer.files).filter(file => {
            const ext = '.' + file.name.split('.').pop().toLowerCase();
            return allowedTypes.includes(ext);
        });

        const newFiles = files.filter(file =>
            !selectedFiles.some(selectedFile =>
                selectedFile.name === file.name && selectedFile.size === file.size
            )
        );

        selectedFiles = [...selectedFiles, ...newFiles];

        checkPDF(selectedFiles);

        displayFiles(selectedFiles);
        toggleFollowingButton();

        e.target.value = '';
    }

    const displayFiles = (files) => {
        $fileList.empty();
        files.forEach((file, index) => {

            const fileId = file.fileId || `file-${Date.now()}-${index}`;
            file.fileId = fileId;

            const $fileItem = $(`
            <div class="file flex gap-4 items-center px-4 py-3 rounded-md bg-green-100 text-green-400 font-normal" data-file-id="${fileId}">

                <span>${file.name}</span>
                <button type="button" class="remove-file" data-file-id="${fileId}">
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
    };

    $(document).on('click', '.remove-file', function () {
        const fileId = $(this).data('file-id');
        removeFile(fileId);
    });

    function toggleFollowingButton() {
        const filesExist = selectedFiles.length > 0;
        const $actionList = $(".action-list");

        if (filesExist && currentStep === 0) {
            prevStep.hide();
            nextStep.show().text(language_code === 'en' ? "Next" : "Suivant");
            $("#restart").hide();
            $("#restart-text").hide();

            $actionList.css("justify-content", "flex-end");
        } else if (currentStep === 0) {
            nextStep.hide();
        }

        $fileList.toggleClass('hidden', !filesExist);
    }

    function checkPDF(files) {
        const isPdf = files.some(file => file.name.toLowerCase().endsWith('.pdf'));
        $(".pdf-document").toggleClass('hidden', !isPdf);
    }

    function removeFile(fileId) {
        selectedFiles = selectedFiles.filter(file => file.fileId !== fileId);

        checkPDF(selectedFiles);

        $(`.file[data-file-id="${fileId}"]`).remove();

        const $detectedFile = $(`.flex.gap-5[data-file-id="${fileId}"]`);
        if ($detectedFile.length) {
            $detectedFile.remove();
        }

        toggleFollowingButton();

        if (currentStep === 1) {
            checkLanguagesConsistency();
        }

        if (selectedFiles.length === 0) {
            currentStep = 0;
            showStep(currentStep);
        }
    }


    // ------------- STEP-2 -------------


    function detectLanguageFiles() {
        if (selectedFiles.length === 0) {
            return;
        }

        const formData = new FormData();
        selectedFiles.forEach((file) => {
            formData.append(`document[]`, file);
        });

        $.ajax({
            url: detect_language,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            success: function (response) {
                const isSameLanguages = response.languages.every(i => i?.abbreviation === response.languages[0]?.abbreviation);

                const detectedFiles = response.languages.map(serverFile => {
                    const matchingFile = selectedFiles.find(f => f.name === serverFile.file_name);
                    return {
                        ...serverFile,
                        fileId: matchingFile ? matchingFile.fileId : `file-${Date.now()}-${serverFile.file_name}`
                    };
                });

                displayDetectLanguageFiles(detectedFiles, isSameLanguages);

                if (!isSameLanguages) {
                    $('.step-container').addClass('bg-red-150 text-red-200');
                } else {
                    sourceLanguage = response.languages[0].abbreviation.toLowerCase();
                }
                checkLanguagesConsistency();
            },
            error: function () {
                errorNotification();
            }
        });
    }

    function displayDetectLanguageFiles(files) {
        const $detectiveLanguageList = $('.detective-language-list');
        $detectiveLanguageList.empty();

        files.forEach((file) => {
            const $fileItem = $(`
            <div class="flex gap-5 items-center" data-file-id="${file.fileId}">
                <div class="flex gap-4 items-center px-4 py-3 rounded-md bg-green-100 text-green-400 detected-file font-normal">

                    <span class="text-3.5 w-50 truncate">${file.file_name}</span>
                    <button type="button" class="remove-detected-file" data-file-id="${file.fileId}">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <g clip-path="url(#clip0_759_4082)">
                                <path d="M10 20C15.5229 20 20 15.5229 20 10C20 4.47716 15.5229 0 10 0C4.47716 0 0 4.47716 0 10C0 15.5229 4.47716 20 10 20Z" fill="currentColor"/>
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
                    <select class="gray-text-select document-source-language" name="source_language" required data-file-id="${file.fileId}" data-default-value="${file.abbreviation.toLowerCase()}">
                        ${getLanguageOptions(file.abbreviation)}
                    </select>
                </div>
            </div>
        `);

            $detectiveLanguageList.append($fileItem);

            $fileItem.find('.document-source-language').select2().each(function () {
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
                        var newText = text + ' <span class="detected-text font-normal">(detected)</span>';

                        $selectedOption.text(text + (language_code === 'en' ? ' (detected)' : ' (détecté)'));
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

    function checkLanguagesConsistency() {
        const sourceSelects = $('.document-source-language');
        const targetLanguageBlock = $('.target-language-container');
        const targetSelect = $('.select-block');
        const detectedFiles = $(".detected-file");

        let isConsistent = true;
        let firstValue = sourceSelects.first().val();
        let targetValue = $('.document-target-language').val();

        sourceLanguage = firstValue;

        sourceSelects.each(function () {
            const currentValue = $(this).val();
            if (currentValue !== firstValue) {
                isConsistent = false;
                return false;
            }
        });


        // ------------- SELECT -------------

        $('.document-target-language').attr("data-placeholder", language_code === 'en' ? "Target language" : "Langue cible");

        $('.document-target-language').select2();
        $('.document-source-language').select2();

        $targetSelect = $(".document-target-language").select2();

        $targetSelect.data('select2').$container.addClass('languages');
        $targetSelect.data('select2').$dropdown.addClass('languages');

        targetLanguageBlock.find('.error-message').remove();

        if (currentStep === 1) {
            if (!isConsistent) {
                $('.document-source-language').select2().each(function () {
                    var $select = $(this);
                    $select.data('select2').$container.addClass('error languages');
                    $select.data('select2').$dropdown.addClass('error languages');
                });

                $('.step-container').addClass('bg-red-150 text-red-200');

                targetSelect.hide();

                targetLanguageBlock.prepend('<div class="error-message text-red-400">One or more files have different language, please fix it.</div>');

                detectedFiles.removeClass('bg-green-150 text-green-500').addClass('bg-red-150 text-red-400 border border-red-400');
            } else {
                $('.document-source-language').select2().each(function () {
                    var $select = $(this);
                    $select.data('select2').$container.addClass('languages');
                    $select.data('select2').$dropdown.addClass('languages');
                    $select.data('select2').$container.removeClass('error');
                    $select.data('select2').$dropdown.removeClass('error');
                });


                $('.step-container').removeClass('bg-red-150 text-red-200');

                targetSelect.show();

                detectedFiles.removeClass('bg-red-150 text-red-400 border border-red-400').addClass('bg-green-150 text-green-500');
            }
        }
        let isSameAsTarget = firstValue === targetValue;

        if (!isConsistent || !targetValue || isSameAsTarget) {
            nextStep.removeClass('border-green-700 text-white text-green-700')
                .addClass('border-gray-225 text-gray-225 pointer-events-none')
                .prop("disabled", true);
        } else {
            nextStep.removeClass('border-gray-225 text-gray-225 pointer-events-none')
                .addClass('border-green-700 text-green-700')
                .prop("disabled", false);
            $('.language-step').removeClass('hidden');
            $('.source').text(firstValue.toUpperCase());
            $('.target').text(targetValue.toUpperCase());

        }
    }


    $(document).on('change', '.document-source-language, .document-target-language', function () {
        checkLanguagesConsistency();
    });

    $(document).on('click', '.remove-detected-file', function () {
        const fileId = $(this).data('file-id');
        removeFile(fileId);
    });

    const getLanguageOptions = (defaultValue) => {
        return languages.map(lang =>
            `<option value="${lang.abbreviation.toLowerCase()}" ${lang.abbreviation === defaultValue ? 'selected' : ''}>
            ${lang.name}
        </option>`
        ).join('');
    }


    // ------------- STEP-3 -------------


    function updateDomainsList(domains) {
        const domainsList = $('.domains-list');
        domainsList.empty();

        domains.forEach((domain, index) => {
            const button = $('<button>', {
                type: 'button',
                class: 'domain-button text-3.5 py-3 px-7.5 bg-gray-100 text-gray-475 hover:bg-gray-600 hover:text-white rounded-md focus:text-white focus:bg-gray-600 transition duration-300 ease-in-out',
                text: domain.name,
                'data-name': domain.name,
                click: function () {
                    $('.domain-button').removeClass('selected bg-gray-600 text-white').addClass('bg-gray-100 text-gray-475');
                    $(this).removeClass('bg-gray-100 text-gray-475').addClass('selected bg-gray-600 text-white');

                    selectedDomain = $(this).data('name');
                    getDomains();
                }
            });

            if (index === 0) {
                button.removeClass('bg-gray-100 text-gray-475').addClass('selected bg-gray-600 text-white');

                selectedDomain = domain.name;
            }

            domainsList.append(button);
        });

        getDomains();
    }

    function updateSubDomainsList(subDomains) {
        const subDomainsList = $('.sub-domain-list');
        subDomainsList.empty();

        subDomains.forEach((subDomain, index) => {
            const button = $('<button>', {
                type: 'button',
                class: 'sub-domain-button text-3.5 py-3 px-7.5 bg-gray-175 text-gray-375 hover:bg-gray-600 hover:text-white rounded-md focus:text-white focus:bg-gray-600 transition duration-300 ease-in-out',
                text: subDomain,
                'data-name': subDomain,
                click: function () {
                    $('.sub-domain-button').removeClass('selected bg-green-500 text-white').addClass('bg-gray-175 text-gray-375');
                    $(this).removeClass('bg-gray-175 text-gray-375').addClass('selected bg-gray-600 text-white');
                    selectedSubDomain = $(this).data('name');
                    $('.domain-step').text(selectedSubDomain).removeClass('hidden');
                }
            });

            if (index === 0) {
                button.removeClass('bg-gray-175 text-gray-375').addClass('selected bg-gray-600 text-white');
                selectedSubDomain = subDomain;
            }

            subDomainsList.append(button);
        });
    }

    const getDomainsGroups = () => {
        $.ajax({
            url: domain_groups,
            type: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            success: function (response) {
                updateDomainsList(response);
            },
            error: function () {
                errorNotification();
            }
        });
    }


    const getDomains = () => {
        $.ajax({
            url: `${get_domains}?source_language=${sourceLanguage}&target_language=${targetLanguage}&domain_group=${selectedDomain}`,
            type: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            success: function (response) {
                defaultDomain = response.default_domain;

                if (response.default_domain) {
                    $(".default").addClass('hidden');
                    $(".my-glossary").addClass('rounded-l-md');
                    selectedGlossaryType = 'my-glossary'
                } else {
                    $(".default").removeClass('hidden');
                    $(".my-glossary").removeClass('rounded-l-md');
                    selectedGlossaryType = 'default'
                }

                if (response.data && response.data.length === 0) {
                    nextStep.removeClass('border-green-700 text-white text-green-700')

                        .addClass('border-gray-225 text-gray-225 pointer-events-none')
                        .prop("disabled", true);
                    $('.domain-step').text(language_code === 'en' ? 'None' : 'Aucun').removeClass('hidden');
                } else {
                    nextStep.removeClass('border-gray-225 text-gray-225 pointer-events-none')
                        .addClass('border-green-700 text-green-700')
                        .prop("disabled", false);
                    $('.domain-step').text(response.data[0]).removeClass('hidden');
                }

                updateSubDomainsList(response.data);
            },
            error: function () {
                errorNotification();
            }
        });
    }


    // ------------- STEP-4 -------------

    $(".step-4 .default").click(function () {
        if (!defaultDomain) {
            selectGlossaryType('default');
            loadDefaultGlossary();
            $('.terminology-step').text('default').removeClass('hidden');
        }
    });

    $(".step-4 .my-glossary").click(function () {
        selectGlossaryType('my-glossary');
        loadMyGlossaries();
    });

    $(".step-4 .none").click(function () {
        selectGlossaryType('none');
        $('.terminology-step').text(language_code === 'en' ? 'none' : 'aucun').removeClass('hidden');
        selectedGlossary = 'none';
        nextStep.removeClass('border-gray-225 text-gray-225 pointer-events-none')
            .addClass('border-green-700 text-green-700')
            .prop("disabled", false);
        clearGlossaryList();
    });

    function selectGlossaryType(type) {
        selectedGlossaryType = type;
        $(".step-4 .glossary-tab").removeClass('bg-gray-600 text-white').addClass('bg-gray-175 text-gray-375');
        $(".step-4 ." + type).removeClass('bg-gray-175 text-gray-375').addClass('bg-gray-600 text-white');

        if (type === 'my-glossary') {
            $(".add-glossary-btn").removeClass('hidden');
        } else {
            $(".add-glossary-btn").addClass('hidden');
        }
    }

    function clearGlossaryList() {
        $(".glossary-list").empty();
    }

    function loadDefaultGlossary() {
        const data = {
            source_language: sourceLanguage,
            target_language: targetLanguage,
            domain_name: selectedSubDomain
        };

        $.ajax({
            url: get_default_glossary,
            type: 'POST',
            data: data,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            success: function (response) {
                updateGlossaryList([response], true);
                selectedGlossary = response?.id;
            },
            error: function () {
                errorNotification();
                nextStep.removeClass('border-gray-225 text-gray-225 pointer-events-none')
                    .addClass('border-green-700 text-green-700')
                    .prop("disabled", false);
            }
        });
    }

    function loadMyGlossaries() {
        const data = {
            source_language: sourceLanguage,
            target_language: targetLanguage,
            domain_name: selectedSubDomain
        };

        $.ajax({
            url: api_list_glossaries,
            type: 'POST',
            data: data,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            success: function (response) {
                updateGlossaryList(response, false);
                selectedGlossary = '';
                $('.terminology-step').text('default').removeClass('hidden');
                nextStep.removeClass('border-green-700 text-white text-green-700')
                    .addClass('border-gray-225 text-gray-225 pointer-events-none')
                    .prop("disabled", true);
            },
            error: function () {
                errorNotification();
            }
        });
    }

    function updateGlossaryList(glossaries, isDefault) {

        const $list = $(".glossary-list");

        $list.empty();

        glossaries.forEach(function (glossary) {
            const $item = $(`<button type="button" class="glossary-item text-3.5 py-3 px-7.5 ${isDefault ? "bg-gray-600 text-white" : "bg-gray-175 text-gray-375"} rounded-md hover:bg-gray-600 hover:text-white transition duration-300 ease-in-out">${glossary.name}</button>`);
            $item.click(function () {
                if (selectedGlossary === glossary.id) {
                    $(this).removeClass('bg-gray-600 text-white').addClass('bg-gray-175 text-gray-375');
                    selectedGlossary = '';
                    $('.terminology-step').text('').removeClass('hidden');
                    if (selectedGlossaryType === 'my-glossary') {
                        nextStep.removeClass('border-green-700 text-white text-green-700')
                            .addClass('border-gray-225 text-gray-225 pointer-events-none')
                            .prop("disabled", true);
                    }
                } else {
                    $(".glossary-item").removeClass('bg-gray-600 text-white').addClass('bg-gray-175 text-gray-375');
                    $(this).removeClass('bg-gray-175 text-gray-375').addClass('bg-gray-600 text-white');
                    selectedGlossary = glossary.id;
                    $('.terminology-step').text(selectedGlossary).removeClass('hidden');

                    if (selectedGlossaryType === 'my-glossary') {
                        nextStep.removeClass('border-gray-225 text-gray-225 pointer-events-none')
                            .addClass('border-green-700 text-green-700')
                            .prop("disabled", false);
                    }
                }
            });
            $list.append($item);
        });

    }

    const $modal = $('#modal');
    const $closeIcon = $('#closeIcon');
    const maxFileSize = 5 * 1024 * 1024; // 5MB

    $('#openModal').on('click', function () {
        $modal.removeClass('hidden');
        $closeIcon.removeClass('hidden');
    });

    $('#closeModal, #closeIcon').on('click', function () {
        $('#uploadButton').removeClass('bg-transparent border border-red-400 text-red-400').addClass('bg-green-700');
        $('#downloadSample').removeClass('bg-transparent border border-gray-200 text-gray-400').addClass('bg-green-700 text-green-700 border border-green-700');
        $('.glossary-container').removeClass('bg-red-150').addClass('bg-gray-25');
        $modal.addClass('hidden');
        $closeIcon.addClass('hidden');
    });

    $(window).on('click', function (event) {
        if (event.target == $modal[0]) {
            $('#uploadButton').removeClass('bg-transparent border border-red-400 text-red-400').addClass('bg-green-700');
            $('#downloadSample').removeClass('bg-transparent border border-gray-200 text-gray-400').addClass('bg-green-700 text-green-700 border border-green-700');
            $('.glossary-container').removeClass('bg-red-150').addClass('bg-gray-25');
            $modal.addClass('hidden');
            $closeIcon.addClass('hidden');
        }
    });

    $('#uploadButton').on('click', function () {
        $('.glossary-file').click();
    });

    $('.glossary-file').on('change', function (e) {
        glossaryFile = e.target.files[0];
        if (glossaryFile) {
            $('#uploadButton').removeClass('bg-transparent border border-red-400 text-red-400').addClass('bg-green-700');
            $('#downloadSample').removeClass('bg-transparent border border-gray-200 text-gray-400').addClass('bg-green-700 text-green-700 border border-green-700');
            $('.glossary-container').removeClass('bg-red-150').addClass('bg-gray-25');
            if (glossaryFile.size <= maxFileSize) {
                showUploadedFile(glossaryFile.name);
            } else {
                alert('File size exceeds 5MB limit.');
                $(this).val('');
            }
        }
    });

    function showUploadedFile(fileName) {
        $('#fileName').text(fileName);
        $('#fileInfo').removeClass('hidden');
        $('#uploadButton').addClass('hidden');
    }

    $(document).on('click', '.remove-file', function () {
        resetUploadArea();
    });

    function resetUploadArea() {
        $('#uploadButton').removeClass('hidden');
        $('#fileInfo').addClass('hidden');
        $('.glossary-file').val('');
    }

    $(document).on('click', '.create-glossary', function (e) {
        e.preventDefault();

        if (!glossaryFile) {
            $('#uploadButton').removeClass('bg-green-700 border border-green-700').addClass('bg-transparent border border-red-400 text-red-400');
            $('#downloadSample').removeClass('bg-green-700 text-green-700 ').addClass('bg-transparent border border-gray-200 text-gray-400');
            $('.glossary-container').removeClass('bg-gray-25').addClass('bg-red-150');
            return;
        }

        const formData = new FormData();

        formData.append('file', glossaryFile);
        formData.append('domain_name', selectedSubDomain);
        formData.append('source_language', sourceLanguage);
        formData.append('target_language', targetLanguage);

        $.ajax({
            url: add_glossary,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            success: function (response) {
                glossaryFile = null;
                $('#fileInfo').addClass('hidden');
                $('#fileName').text('');
                $('.glossary-file').val('');
                $modal.addClass('hidden');
                $closeIcon.addClass('hidden');

                const $list = $(".glossary-list");

                const $item = $(`<button type="button" class="glossary-item text-3.5 py-3 px-7.5 bg-gray-175 text-gray-375 rounded-md hover:bg-gray-600 hover:text-white">${response.name}</button>`);

                $item.click(function () {
                    if (selectedGlossary === response.id) {
                        $(this).removeClass('bg-gray-600 text-white').addClass('bg-gray-175 text-gray-375');
                        selectedGlossary = '';
                        $('.terminology-step').text('').removeClass('hidden');
                        nextStep.removeClass('border-green-700 text-green-700 ')
                            .addClass('border-gray-225 text-gray-225 pointer-events-none')
                            .prop("disabled", true);
                    } else {
                        $(".glossary-item").removeClass('bg-gray-600 text-white').addClass('bg-gray-175 text-gray-375');
                        $(this).removeClass('bg-gray-175 text-gray-375').addClass('bg-gray-600 text-white');
                        selectedGlossary = response.id;
                        $('.terminology-step').text(selectedGlossary).removeClass('hidden');
                        nextStep.removeClass('border-gray-225 text-gray-225 pointer-events-none')
                            .addClass('border-green-700 text-green-700')
                            .prop("disabled", false);
                    }
                });

                $list.append($item);
            },
            error: function () {
                errorNotification();
            }
        });
    });


    // ------------- STEP-5 -------------


    const fileTranslate = () => {
        const formData = new FormData();
        selectedFiles.forEach((file) => {
            formData.append(`document[]`, file);
        });

        formData.append('domain_name', selectedSubDomain);
        formData.append('glossary', selectedGlossary);
        formData.append('source_language', sourceLanguage);
        formData.append('target_language', targetLanguage);
        formData.append('action', 'file_translate');

        $('#loader-row').removeClass('hidden');
        $.ajax({
            url: translate,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            success: function (response) {
                if (response && response.project_ids && response.project_ids.length > 0) {
                    startStatusCheck(response.project_ids);
                }
            },
            error: function () {
                $('#loader-row').addClass('hidden');
                errorNotification();
            },
        });
    };

    const $modalRevision = $('#modal-revision');
    const $closeRevision = $('#close-revision');

    function updateProjectTable(projects) {
        const tableBody = $('.projects tbody');
        tableBody.empty();


        projects.forEach(project => {
            const row = $('<tr></tr>');

            row.append(`
            <td>
                <div class="rounded-md text-green-400 py-3 px-4 md:w-50 2xl:w-80 truncate text-3.25">

                    ${project.source_file_name}
                </div>
            </td>
        `);

            const statusColumn = $('<td></td>');
            const statusSpan = $('<span class="rounded-md py-1.5 px-2.5 text-3.25 font-medium"></span>');


            switch (project.status) {
                case 'Being translated':
                    statusSpan.text('Processing...');
                    statusSpan.addClass('text-green-500');
                    break;
                case 'Translated':
                    statusSpan.text(language_code === 'en' ? 'Translated' : 'Document traduit');
                    statusSpan.addClass('bg-green-100 text-green-400');
                    break;
                case 'Sent to post-editing, not accepted yet':
                    statusSpan.text(language_code === 'en' ? 'Request for quote sent' : 'Demande de devis envoyée');
                    statusSpan.addClass('bg-yellow-100 text-yellow-400');
                    break;
                case 'Sent to post-editing, accepted':
                    statusSpan.text(language_code === 'en' ? 'Request for quote accepted' : 'Demande de devis acceptée');
                    statusSpan.addClass('bg-blue-100 text-blue-400');
                    break;
                case 'Post-edited file uploaded':
                    statusSpan.text(language_code === 'en' ? 'Request for quote accepted' : 'Demande de devis acceptée');
                    statusSpan.addClass('bg-green-50 text-green-300');
                    break;
                case 'Error':
                    statusSpan.text(language_code === 'en' ? 'Error' : 'Erreur');
                    statusSpan.addClass('bg-red-100 text-red-400');
                    break;
                default:
                    statusSpan.text(project.status);
                    statusSpan.addClass('bg-gray-175 text-gray-600');
                    break;
            }
            statusColumn.append(statusSpan);
            row.append(statusColumn);

            const downloadColumn = $('<td></td>');
            const downloadButton = $(`
            <button type=button class="flex gap-2.5 items-center text-green-500 download-file disabled:pointer-events-none disabled:text-gray-225 disabled:border-gray-225" ${project.status !== 'Translated' ? 'disabled' : ''}>
                <svg width="17" height="16" viewBox="0 0 17 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <g clip-path="url(#clip0_759_2185)">
                        <path d="M15.5527 7.21875C15.1215 7.21875 14.7715 7.56875 14.7715 8C14.7715 11.55 11.884 14.4375 8.33398 14.4375C4.78398 14.4375 1.89648 11.55 1.89648 8C1.89648 7.56875 1.54648 7.21875 1.11523 7.21875C0.683984 7.21875 0.333984 7.56875 0.333984 8C0.333984 10.1375 1.16523 12.1469 2.67773 13.6562C4.19023 15.1687 6.19648 16 8.33398 16C10.4715 16 12.4809 15.1687 13.9902 13.6562C15.5027 12.1438 16.334 10.1375 16.334 8C16.334 7.56875 15.984 7.21875 15.5527 7.21875Z" fill="currentColor"/>
                        <path d="M7.26289 10.7375C7.55039 11.025 7.93164 11.1812 8.33477 11.1812C8.74102 11.1812 9.12227 11.0219 9.40664 10.7375L11.3723 8.77187C11.6785 8.46562 11.6785 7.97187 11.3723 7.66562C11.066 7.35937 10.5723 7.35937 10.266 7.66562L9.11602 8.81875V0.78125C9.11602 0.35 8.76602 0 8.33477 0C7.90352 0 7.55352 0.35 7.55352 0.78125V8.81875L6.40039 7.66562C6.09414 7.35937 5.60039 7.35937 5.29414 7.66562C4.98789 7.97187 4.98789 8.46562 5.29414 8.77187L7.26289 10.7375Z" fill="currentColor"/>
                    </g>
                    <defs>
                        <clipPath id="clip0_759_2185">
                            <rect width="16" height="16" fill="white" transform="translate(0.333984)"/>
                        </clipPath>
                    </defs>
                </svg>
                  ${language_code === 'en' ? 'Download' : 'Télécharger'}
            </button>
        `);
            downloadButton.attr('data-translated-file', project.translated_file);
            if (project.reviewed_file) {
                downloadButton.attr('data-reviewed-file', project.reviewed_file);
            }
            downloadColumn.append(downloadButton);
            row.append(downloadColumn);

            const revisionColumn = $('<td class="flex justify-end"></td>');
            const revisionButton = $(`
            <button
                type="button"
                data-translated-file="${project.translated_file}"
                data-id="${project.id}"
                class="flex gap-2.5 items-center text-gray-600 border border-gray-600 rounded-md px-2.5 py-3 text-3.25 disabled:pointer-events-none disabled:text-gray-225 disabled:border-gray-225 expert-revision"
                ${project.status !== 'Translated' ? 'disabled' : ''}
            >
                ${language_code === 'en' ? "Human revision" : "Relecture expert"}
                <div class="relative group">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M10 0C4.47301 0 0 4.4725 0 10C0 15.5269 4.4725 20 10 20C15.527 20 20 15.5275 20 10C20 4.47309 15.5275 0 10 0ZM11.0269 13.9696C11.0269 14.2855 10.5662 14.6014 10.0002 14.6014C9.40785 14.6014 8.98668 14.2855 8.98668 13.9696V8.95445C8.98668 8.5859 9.40789 8.33574 10.0002 8.33574C10.5662 8.33574 11.0269 8.5859 11.0269 8.95445V13.9696ZM10.0002 7.12484C9.39473 7.12484 8.9209 6.6773 8.9209 6.17707C8.9209 5.67687 9.39477 5.2425 10.0002 5.2425C10.5926 5.2425 11.0665 5.67687 11.0665 6.17707C11.0665 6.6773 10.5925 7.12484 10.0002 7.12484Z" fill="currentColor"/>
                    </svg>
                    <div class="invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-opacity duration-300 absolute z-10 w-48 bg-gray-600 text-white text-2.75 rounded-md bottom-30 left-1/2 transform -translate-x-1/2 translate-y-full">
                        <span class="py-4 px-4.5 text-justify text-wrap block">
                                              ${language_code === 'en' ? 'Click the button to see options for improving the quality of the translated file.' : "Cliquez sur ce bouton pour afficher les options de relecture disponibles"}
                        </span>
                        <div class="absolute w-3 h-3 bg-gray-600 transform rotate-45 left-1/2 -translate-x-1/2 -bottom-1.5"></div>
                    </div>
                </div>
            </button>
        `);
            revisionColumn.append(revisionButton);
            row.append(revisionColumn);

            tableBody.append(row);
        });

        initializeDownloadButtons();
        initializeRevisionButtons();
    }


    function initializeDownloadButtons() {
        $('.download-file').off('click').on('click', function (e) {
            e.preventDefault();
            const $button = $(this);
            const translatedFile = $button.data('translated-file');
            const reviewedFile = $button.data('reviewed-file');

            if (reviewedFile) {
                const $tooltip = $(`
                <div class="download-tooltip absolute z-10 bg-white rounded-md shadow-lg p-2 mt-2 right-0">
                    <button type="button" class="download-file-option block w-full text-left px-2 py-1 hover:bg-gray-100 whitespace-nowrap" data-file-url="${translatedFile}">
                        Translated
                    </button>
                    <button type="button" class="download-file-option block w-full text-left px-2 py-1 hover:bg-gray-100 whitespace-nowrap" data-file-url="${reviewedFile}">
                        Post-edited
                    </button>
                </div>
            `);
                $button.parent().append($tooltip);

                $(document).one('click', function closeTooltip(e) {
                    if (!$(e.target).closest('.download-tooltip').length && !$(e.target).closest('.download-file').length) {
                        $tooltip.remove();
                    } else {
                        $(document).one('click', closeTooltip);
                    }
                });
            } else if (translatedFile) {
                window.location.href = translatedFile;
            }
        });

        $(document).on('click', '.download-file-option', function (e) {
            e.preventDefault();
            e.stopPropagation();
            const fileUrl = $(this).data('file-url');
            if (fileUrl) {
                window.location.href = fileUrl;
            }
        });
    }

    function initializeRevisionButtons() {
        $('.expert-revision').off('click').on('click', function () {
            if ($(this).prop('disabled')) return;

            const button = $(this);
            const translatedFile = button.data('translated-file');
            const id = button.data('id');

            $('.expert-revision', $modalRevision)
                .data('translated-file', translatedFile)
                .data('id', id);

            $modalRevision.removeClass('hidden');
            $closeRevision.removeClass('hidden');
        });
    }


    $('#close-revision').on('click', function () {
        $modalRevision.addClass('hidden');
        $closeRevision.addClass('hidden');
    });

    $(window).on('click', function (event) {
        if (event.target == $modalRevision[0]) {
            $modalRevision.addClass('hidden');
            $closeRevision.addClass('hidden');
        }
    });

    $modalRevision.on('click', '.expert-revision', function () {
        const translatedFile = $(this).data('translated-file');
        const id = $(this).data('id');

        let formData = new FormData();
        formData.append('file_url', translatedFile);
        formData.append('project_id', id);

        $.ajax({
            type: 'POST',
            url: expert_revision_file,
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
                'Accept': 'application/json',
            },
            dataType: 'json',
            success: function () {
                const projectRow = $(`button[data-id="${id}"]`).closest('tr');
                const statusSpan = projectRow.find('td:eq(1) span');

                statusSpan.text('Request for post-editing sent');
                statusSpan.removeClass().addClass('rounded-md py-1.5 px-2.5 text-3.25 bg-yellow-100 text-yellow-400');


                projectRow.find('.expert-revision').prop('disabled', true).addClass('disabled:pointer-events-none disabled:text-gray-225 disabled:border-gray-225');

                $modalRevision.addClass('hidden');
                $closeRevision.addClass('hidden');
            },
            error: function () {
                errorNotification();
            }
        });
    });

    const startStatusCheck = (projectIds) => {
        const checkDocumentStatus = () => {
            let params = new URLSearchParams();

            projectIds.forEach(projectId => {
                params.append('project_id[]', projectId);
            });

            $.ajax({
                type: 'GET',
                url: `${single_project}?${params.toString()}`,
                processData: false,
                contentType: false,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                success: function (response) {
                    updateProjectTable(response);
                },
                error: function () {
                    errorNotification();
                },
                complete: function () {
                    $('#loader-row').addClass('hidden');
                }
            });
        };

        checkDocumentStatus();

        setInterval(checkDocumentStatus, 10000);
    };

});
