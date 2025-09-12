$(document).ready(function () {
    var $fileInput = $('#file-input');
    var $fileUploadZone = $('#file-upload-zone');
    var $warningAlert = $('#warning-alert');
    var $fileList = $('#file-list');
    var $nextButton = $('#next-step');
    var $blockButtons = $('.block-buttons');
    var uploadedFiles = [];

    // Filtre toutes les langues visibles selon la recherche
    $('#search-input').on('input keyup change', function () {
        var val = $(this).val().toLowerCase();
        $('.language-item').each(function () {
            var text = $(this).text().toLowerCase();
            $(this).toggle(text.indexOf(val) > -1);
        });
    });

    // Sélection d'une langue, coloration verte sur tous les blocs concernés
    // Filtre toutes les langues visibles selon la recherche
    $('#search-input').on('input keyup change', function () {
        var val = $(this).val().toLowerCase();
        $('.language-item').each(function () {
            var text = $(this).text().toLowerCase();
            $(this).toggle(text.indexOf(val) > -1);
        });
    });

// Sélection d'une langue, coloration verte sur tous les blocs concernés et gestion de l'icône + select2
    $(document).on('click', '.language-item', function () {
        // Récupère la valeur de la langue
        var selectedLang = $(this).data('value');

        // Désélectionne partout la couleur
        $('.language-item').removeClass('text-green-800 bg-green-100');
        // Cache toutes les icônes ph-check
        $('.language-item .ph-check').parent().addClass('hidden').removeClass('visible');

        // Sélectionne la ligne cliquée
        $(this).addClass('text-green-800 bg-green-100');
        // Affiche l'icone dans la ligne cliquée
        $(this).find('.ph-check').parent().removeClass('hidden').addClass('visible');

        // Met à jour le select2 si présent
        $('.document-target-language').val(selectedLang).trigger('change');
    });


    // File input change handler
    $fileInput.on('change', function (e) {
        handleFiles(Array.from(e.target.files));
        $(this).val(''); // Reset input
    });

    // Drag and drop handlers
    $fileUploadZone.on('dragover', function (e) {
        e.preventDefault();
        $(this).addClass('bg-black/[0.05]');
        $(this).removeClass('bg-black/[0.03]');
    });

    $fileUploadZone.on('dragleave', function (e) {
        e.preventDefault();
        $(this).removeClass('bg-black/[0.05]');
        $(this).addClass('bg-black/[0.03]');
    });

    $fileUploadZone.on('drop', function (e) {
        e.preventDefault();
        $(this).removeClass('bg-black/[0.05]');
        $(this).addClass('bg-black/[0.03]');

        var files = Array.from(e.originalEvent.dataTransfer.files);
        handleFiles(files);
    });

    function getFileType(filename) {
        var extension = filename.toLowerCase().split('.').pop();
        if (extension === 'pdf') return 'pdf';
        if (extension === 'docx') return 'docx';
        if (extension === 'pptx') return 'pptx';
        return 'pdf'; // default
    }

    // Pour bouton suppression dynamique
    window.removeFile = function (fileId) {
        uploadedFiles = uploadedFiles.filter(function (file) {
            return file.id !== fileId;
        });
        updateUI();
    }


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

    function showStep(step) {
        const $actionList = $(".action-list");

        if (step === 0) {
            prevStep.hide();
            $blockButtons.removeClass('justify-between').addClass('justify-end');
            $("#restart").hide();
            $("#restart-text").hide();

            if (selectedFiles.length > 0) {
                nextStep.show();
                $actionList.css("justify-content", "flex-end");
            } else {
                nextStep.hide();
            }

            $('.step-1').removeClass('hidden').show();
            $('.step-2').addClass('hidden').hide();
            $('.step-indicator-2').removeClass('border-0.5 border-[#166534]');
            $('.step-indicator-3').removeClass('border-0.5 border-[#166534]');
            $('.step-indicator-4').removeClass('border-0.5 border-[#166534]');
        } else if (currentStep === 1) {
            $('.step-1').addClass('hidden').hide();
            $('.step-2').removeClass('hidden').show();
            $blockButtons.addClass('justify-between').removeClass('justify-end');
            prevStep.show();
            prevStep.css('display', 'flex');
            prevStep.prop("disabled", false);
            $('.step-indicator-2').addClass('border-0.5 border-[#166534]');
            $('.step-indicator-3').removeClass('border-0.5 border-[#166534]');
            $('.step-indicator-4').removeClass('border-0.5 border-[#166534]');
        } else if (currentStep === 2) {
            $('.step-2').addClass('hidden');
            $('.step-3').removeClass('hidden').show();
            $blockButtons.addClass('justify-between').removeClass('justify-end');
            prevStep.show();
            $('.step-indicator-2').addClass('border-0.5 border-[#166534]');
            $('.step-indicator-3').addClass('border-0.5 border-[#166534]');
            $('.step-indicator-4').removeClass('border-0.5 border-[#166534]');
        } else if (currentStep === 3) {
            $('.step-3').addClass('hidden');
            $('.step-4').removeClass('hidden').show();
            $blockButtons.addClass('justify-between').removeClass('justify-end');
            prevStep.show();
            $('span', $nextButton).text($('span', $nextButton).data('confirm'));
            $('.step-indicator-2').addClass('border-0.5 border-[#166534]');
            $('.step-indicator-3').addClass('border-0.5 border-[#166534]');
            $('.step-indicator-4').addClass('border-0.5 border-[#166534]');
        } else if (currentStep === 4) {
            $('.step-4').addClass('hidden');
            $('.step-5').removeClass('hidden').show();
            $("#restart").show().text(language_code === 'en' ? "New translation" : "Nouveau document");
            $("#restart-text").show();

            $actionList.css("justify-content", "flex-start");
        } else {
            prevStep.show();
            $blockButtons.removeClass('justify-end').addClass('justify-between');

            nextStep.show();
            $("#restart").hide();
            $("#restart-text").hide();

            $actionList.css("justify-content", "space-between");
        }

        prevStep.toggleClass('hidden', step === 0);
        nextStep.toggleClass('hidden', step === 4);
    }

    $(document).on('click', nextStep, function (e) {
        if ($(e.target).hasClass('nextStep') || $(e.target).children().hasClass('nextStep')) {

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
                if (!defaultDomain && access_to_default_glossaries) {
                    loadDefaultGlossary();
                    $(".add-glossary-btn").addClass('hidden');
                    $(".step-4 .default").addClass('bg-gray-600 text-white');
                } else {
                    loadMyGlossaries();
                    $(".add-glossary-btn").removeClass('hidden');
                    $(".step-4 .my-glossary").addClass('bg-gray-600 text-white');
                }
            }

            console.log('currentStep : ' + currentStep);
            if (currentStep === 3) {
                fileTranslate();
            }

            currentStep++;
            showStep(currentStep);

        }
    });

    $(document).on('click', prevStep, function (e) {
        if ($(e.target).hasClass('prevStep')) {
            console.log('currentStep from prevStep : ' + currentStep)
            if (currentStep > 0) {
                currentStep--;
                showStep(currentStep);
                nextStep.removeClass('border-gray-225 text-gray-225 pointer-events-none').addClass('border-green-700 text-green-700').prop("disabled", false);

                $('.step-container').removeClass('bg-red-100 border-red-200');
            }
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

    fileInput.on('change', function (e) {
        handleFiles(Array.from(e.target.files));
        e.target.value = ''; // Reset input
    });

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

    function updateUI() {
        if ($fileList.length > 0) {
            $('#warning-alert').removeClass('hidden');
            $('#file-list').removeClass('hidden');
            $('#next-step').prop('disabled', false).removeClass('opacity-50 cursor-not-allowed');
        } else {
            $('#warning-alert').addClass('hidden');
            $('#file-list').addClass('hidden');
            $('#next-step').prop('disabled', true).addClass('opacity-50 cursor-not-allowed');
        }
    }

    $nextButton.on('click', function () {
        if (!$(this).prop('disabled')) {
            // Handle next step logic here
            console.log('Proceeding to next step with files:', uploadedFiles);
            // You can redirect to the next step or trigger the next step logic
        }
    });

    function handleFiles(e) {
        // Extraire les fichiers selon le type d'événement (input ou drop)
        var filesArray = Array.isArray(e) ? e : Array.from(e.target.files || e.originalEvent.dataTransfer.files);

        // Filtrer fichiers selon extension autorisée
        var filteredFiles = filesArray.filter(function (file) {
            var ext = '.' + file.name.split('.').pop().toLowerCase();
            return allowedTypes.includes(ext);
        });

        // Filtrer les fichiers déjà présents (par nom et taille)
        var newFiles = filteredFiles.filter(function (file) {
            return !selectedFiles.some(function (selectedFile) {
                return selectedFile.name === file.name && selectedFile.size === file.size;
            });
        });

        // Construire les objets fichiers enrichis
        var enrichedFiles = $.map(newFiles, function (file, index) {
            return {
                id: 'file-' + Date.now() + '-' + index,
                name: file.name,
                size: (file.size / 1024 / 1024).toFixed(1) + ' MB',
                timeAgo: '1 minute ago',
                type: getFileType(file.name),
                file: file
            };
        });

        // Ajouter les nouveaux fichiers enrichis à la liste sélectionnée
        selectedFiles = selectedFiles.concat(enrichedFiles);

        checkPDF(selectedFiles);
        displayFiles(selectedFiles);
        updateUI();
        toggleFollowingButton();

        // Réinitialiser la valeur input si c'est un event input (pas un array)
        if (!Array.isArray(e)) {
            e.target.value = '';
        }
    }


    const displayFiles = (files) => {
        $fileList.empty();
        files.forEach((file, index) => {

            const fileId = file.fileId || `file-${Date.now()}-${index}`;
            file.fileId = fileId;

            const $fileItem = $(`
            <div class="flex items-center gap-8 flex-1">
                <div class="flex items-center gap-2">
                    <div class="w-8 h-10 relative">
                        <svg class="w-8 h-10 shrink-0 fill-[#BFDBFE] absolute left-0 top-0" width="32" height="40" viewBox="0 0 32 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M0 36V4C0 1.79086 1.79086 0 4 0H19.9C20.9271 0 21.9149 0.395099 22.6586 1.10345L30.7586 8.81773C31.5513 9.57271 32 10.6196 32 11.7143V36C32 38.2091 30.2091 40 28 40H4C1.79086 40 0 38.2091 0 36Z" fill="#BFDBFE"/>
                        </svg>
                        <div class="inline-flex px-1 items-center gap-2 rounded-sm bg-[#3B82F6] absolute -left-1 top-[18px] w-[26px] h-4">
                            <span class="font-inter text-[9px] font-bold leading-4 tracking-[0.144px] text-white uppercase">
                                ${file.type}
                            </span>
                        </div>
                    </div>
                    <div class="flex flex-col justify-center items-start">
                        <div class="font-poppins text-base font-normal leading-6 tracking-[-0.176px] text-[#181932]">
                            ${file.name}
                        </div>
                        <div class="font-poppins text-sm font-normal leading-6 tracking-[-0.084px] text-[#5A5A78]">
                            ${file.size} • Downloaded ${file.timeAgo}
                        </div>
                    </div>
                </div>
                <button onclick="removeFile('${file.id}')" class="w-6 h-6 text-black/80 hover:text-red-600 transition-colors">
                    <svg class="w-6 h-6" width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M3 6H5H21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M19 6V20C19 20.5304 18.7893 21.0391 18.4142 21.4142C18.0391 21.7893 17.5304 22 17 22H7C6.46957 22 5.96086 21.7893 5.58579 21.4142C5.21071 21.0391 5 20.5304 5 20V6M8 6V4C8 3.46957 8.21071 2.96086 8.58579 2.58579C8.96086 2.21071 9.46957 2 10 2H14C14.5304 2 15.0391 2.21071 15.4142 2.58579C15.7893 2.96086 16 3.46957 16 4V6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M10 11V17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M14 11V17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </button>
            </div>
        `);

            $fileList.append($fileItem);
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
            $blockButtons.removeClass('justify-between').addClass('justify-end');

            nextStep.show();
            $("#restart").hide();
            $("#restart-text").hide();

            $actionList.css("justify-content", "flex-end");
        } else if (currentStep === 0) {
            // nextStep.hide();
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

        startLoading();

        const formData = new FormData();
        selectedFiles.forEach((file) => {
            formData.append(`document[]`, file.file);
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
            error: function (error) {
                errorNotification(error?.status, error?.responseJSON?.detail);
            },
            complete: function () {
                stopLoading();
            },
        });
    }

    function displayDetectLanguageFiles(files) {
        const $detectiveLanguageList = $('.detective-language-list');
        $detectiveLanguageList.empty();

        files.forEach((file) => {
            console.log(file);
            file.type = file.file_name.split('.').pop();

            const $fileItem = $(`
              <div class="flex items-center gap-8 flex-1" data-file-id="${file.fileId}">
                <div class="flex items-center gap-2">
                  <div class="w-8 h-10 relative">
                    <svg class="w-8 h-10 shrink-0 fill-[#BFDBFE] absolute left-0 top-0" width="32" height="40" viewBox="0 0 32 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M0 36V4C0 1.79086 1.79086 0 4 0H19.9C20.9271 0 21.9149 0.395099 22.6586 1.10345L30.7586 8.81773C31.5513 9.57271 32 10.6196 32 11.7143V36C32 38.2091 30.2091 40 28 40H4C1.79086 40 0 38.2091 0 36Z" fill="#BFDBFE"/>
                    </svg>
                    <div class="inline-flex px-1 items-center gap-2 rounded-sm bg-[#3B82F6] absolute -left-1 top-[18px] w-[26px] h-4">
                      <span class="font-inter text-[9px] font-bold leading-4 tracking-[0.144px] text-white uppercase">
                        ${file.type}
                      </span>
                    </div>
                  </div>
                  <div class="flex flex-col justify-center items-start">
                    <div class="font-poppins text-base font-normal leading-6 tracking-[-0.176px] text-[#181932]">
                      ${file.file_name}
                    </div>
                    <!-- 
                    @TODO: récupérer les infos dans l'appel ajax pour les afficher 
                    <div class="font-poppins text-sm font-normal leading-6 tracking-[-0.084px] text-[#5A5A78]">
                      ${file.size} • Downloaded ${file.timeAgo}
                    </div> -->
                  </div>
                </div>
                <!-- @TODO : delete an item
                 <button onclick="removeFile('${file.id}')" class="w-6 h-6 text-black/80 hover:text-red-600 transition-colors remove-detected-file" data-file-id="${file.fileId}">
                  <svg class="w-6 h-6" width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M3 6H5H21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M19 6V20C19 20.5304 18.7893 21.0391 18.4142 21.4142C18.0391 21.7893 17.5304 22 17 22H7C6.46957 22 5.96086 21.7893 5.58579 21.4142C5.21071 21.0391 5 20.5304 5 20V6M8 6V4C8 3.46957 8.21071 2.96086 8.58579 2.58579C8.96086 2.21071 9.46957 2 10 2H14C14.5304 2 15.0391 2.21071 15.4142 2.58579C15.7893 2.96086 16 3.46957 16 4V6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M10 11V17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M14 11V17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button> -->
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

        if (null !== firstValue) {
            sourceLanguage = firstValue;
        }

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

        $targetSelect = $(".document-target-language");

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

                targetLanguageBlock.prepend(language_code === 'en' ? '<div class="error-message text-red-400">One or more files have different language, please fix it.</div>' : '<div class="error-message text-red-400">Vous ne pouvez pas importer des documents ayant des langues différentes</div>');

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
            // $('.source').text(firstValue.toUpperCase());
            // $('.target').text(targetValue.toUpperCase());

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
                class: 'border border-gray-300 domain-button text-3.5 py-3 px-7.5 bg-gray-100 text-gray-475 hover:bg-green-700 hover:text-white rounded-md focus:text-white focus:bg-green-700 transition duration-300 ease-in-out truncate',
                text: domain.name,
                'data-name': domain.name,
                click: function () {
                    $('.domain-button').removeClass('selected bg-green-700 text-white').addClass('bg-gray-100 text-gray-475');
                    $(this).removeClass('bg-gray-100 text-gray-475').addClass('selected bg-green-700 text-white');

                    selectedDomain = $(this).data('name');
                    getDomains();
                }
            });

            if (index === 0) {
                button.removeClass('bg-gray-100 text-gray-475').addClass('selected bg-green-700 text-white');

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
                class: 'sub-domain-button text-3.5 py-3 px-7.5 bg-gray-100 text-gray-475 hover:bg-green-700 hover:text-white rounded-md focus:text-white focus:bg-green-700 transition duration-300 ease-in-out truncate',
                text: subDomain,
                'data-name': subDomain,
                click: function () {
                    $('.sub-domain-button').removeClass('selected bg-green-700 text-white').addClass('bg-gray-175 text-gray-375');
                    $(this).removeClass('bg-gray-175 text-gray-375').addClass('selected bg-green-700 text-white');
                    selectedSubDomain = $(this).data('name');
                    $('.domain-step').text(selectedSubDomain).removeClass('hidden');
                }
            });

            if (index === 0) {
                button.removeClass('bg-gray-175 text-gray-375').addClass('selected bg-green-700 text-white');
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
            error: function (error) {
                errorNotification(error?.status, error?.responseJSON?.detail);
            },
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
                if (response.default_domain || !access_to_default_glossaries) {
                    $(".default").addClass('hidden');
                    $(".my-glossary").addClass('rounded-l-md');
                    $(".add-glossary-btn").removeClass('hidden');
                    selectedGlossaryType = 'my-glossary'
                } else {
                    $(".default").removeClass('hidden');
                    $(".add-glossary-btn").addClass('hidden');
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
            error: function (error) {
                errorNotification(error?.status, error?.responseJSON?.detail);
            },
        });
    }


    // ------------- STEP-4 -------------

    $(".step-4 .default").click(function () {
        if (!defaultDomain || access_to_default_glossaries) {
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
                $('.terminology-step').text('default').removeClass('hidden');
                nextStep.removeClass('border-gray-225 text-gray-225 pointer-events-none')
                    .addClass('border-green-700 text-green-700')
                    .prop("disabled", false);
            },
            error: function (error) {
                errorNotification(error?.status, error?.responseJSON?.detail);
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
                $('.terminology-step').text('').removeClass('hidden');
                nextStep.removeClass('border-green-700 text-white text-green-700')
                    .addClass('border-gray-225 text-gray-225 pointer-events-none')
                    .prop("disabled", true);
            },
            error: function (error) {
                errorNotification(error?.status, error?.responseJSON?.detail);
            },
        });
    }

    function updateGlossaryList(glossaries, isDefault) {

        const $list = $(".glossary-list");

        $list.empty();

        glossaries.forEach(function (glossary) {
            const $item = $(`<button type="button" class="border border-gray-300  glossary-item text-3.5 py-3 px-7.5 ${isDefault ? "bg-green-700 text-white" : "bg-gray-175 text-gray-375"} rounded-md hover:bg-green-700 hover:text-white transition duration-300 ease-in-out">${glossary.name}</button>`);
            $item.click(function () {
                if (selectedGlossary === glossary.id) {
                    $(this).removeClass('bg-green-700 text-white').addClass('bg-gray-175 text-gray-375');
                    selectedGlossary = '';
                    $('.terminology-step').text('').removeClass('hidden');
                    if (selectedGlossaryType === 'my-glossary') {
                        nextStep.removeClass('border-green-700 text-white text-green-700')
                            .addClass('border-gray-225 text-gray-225 pointer-events-none')
                            .prop("disabled", true);
                    }
                } else {
                    $(".glossary-item").removeClass('bg-green-700 text-white').addClass('bg-gray-175 text-gray-375');
                    $(this).removeClass('bg-gray-175 text-gray-375').addClass('bg-green-700 text-white');
                    selectedGlossary = glossary.id;
                    $('.terminology-step').text(glossary.name).removeClass('hidden');

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

    const $modal = $('#modalGlossary');
    const $closeIcon = $('#closeIcon');
    const maxFileSize = 5 * 1024 * 1024; // 5MB

    $(document).on('click', '.openGlossary', function(event) {
        event.preventDefault(); // Empêche clic par défaut si besoin (par ex lien)
        $modal.removeClass('hidden');
        $closeIcon.removeClass('hidden');
        $('input[name=openGlossary]').prop('checked', 'checked');
    });

    $('#closeModal, #closeIcon').on('click', function () {
        // Réinitialise les styles des boutons comme avant
        $('#uploadButton').removeClass('bg-transparent border border-red-400 text-red-400').addClass('bg-green-700');
        $('#downloadSample').removeClass('bg-transparent border border-gray-200 text-gray-400').addClass('bg-green-700 text-green-700 border border-green-700');
        $('.glossary-container').removeClass('bg-red-150').addClass('bg-gray-25');

        $modal.addClass('hidden');
        $closeIcon.addClass('hidden');

        // Désactive la checkbox et le style "peer-checked"
        $('input[name=openGlossary]').prop('checked', false).trigger('change');
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

                const $item = $(`<button type="button" class="border border-gray-300  border border-gray-300 glossary-item text-3.5 py-3 px-7.5 bg-gray-175 text-gray-375 rounded-md hover:bg-green-700 hover:text-white">${response.name}</button>`);

                $item.click(function () {
                    if (selectedGlossary === response.id) {
                        $(this).removeClass('bg-green-700 text-white').addClass('bg-gray-175 text-gray-375');
                        selectedGlossary = '';
                        $('.terminology-step').text('').removeClass('hidden');
                        nextStep.removeClass('border-green-700 text-green-700 ')
                            .addClass('border-gray-225 text-gray-225 pointer-events-none')
                            .prop("disabled", true);
                    } else {
                        $(".glossary-item").removeClass('bg-green-700 text-white').addClass('bg-gray-175 text-gray-375');
                        $(this).removeClass('bg-gray-175 text-gray-375').addClass('bg-green-700 text-white');
                        selectedGlossary = response.id;
                        $('.terminology-step').text(response.name).removeClass('hidden');
                        nextStep.removeClass('border-gray-225 text-gray-225 pointer-events-none')
                            .addClass('border-green-700 text-green-700')
                            .prop("disabled", false);
                    }
                });

                $list.append($item);
            },
            error: function (error) {
                errorNotification(error?.status, error?.responseJSON?.detail);
            },
        });
    });


    // ------------- STEP-5 -------------


    const fileTranslate = () => {
        const formData = new FormData();
        selectedFiles.forEach((file) => {
            formData.append(`document[]`, file.file);
        });

        formData.append('domain_name', selectedSubDomain);
        /**
         * @TODO 11/09/2025 : Le système de sélection du glossaire étant totalement à revoir
         * en js pour récupérer l'id du glossaire sélectionné dans la popup
         * je ne l'intègre pas dans les paramètres de l'appel ajax volontairement
         */
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
            error: function (error) {
                errorNotification(error?.status, error?.responseJSON?.detail);
            },
            complete: function () {
                $('#loader-row').addClass('hidden');
            }
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
                <div class="border border-gray-300  border border-gray-300 glossary-item py-3 px-7.5 bg-gray-60 text-gray-600 rounded-md md:w-50 2xl:w-80 truncate text-3.25">

                    ${project.source_file_name}
                </div>
            </td>
        `);

            const statusColumn = $('<td></td>');
            const statusSpan = $('<span class="border border-gray-300 glossary-item py-3 px-7.5 bg-gray-175 rounded-md text-gray-600 font-medium"></span>');


            switch (project.status) {
                case 'Being translated':
                    statusSpan.text('Processing...');
                    statusSpan.addClass('text-green-500');
                    break;
                case 'Translated':
                    statusSpan.text(language_code === 'en' ? 'Translated' : 'Document traduit');
                    statusSpan.addClass('text-green-400');
                    break;
                case 'Sent to post-editing, not accepted yet':
                    statusSpan.text(language_code === 'en' ? 'Request for quote sent' : 'Demande de devis envoyée');
                    statusSpan.addClass('text-yellow-400');
                    break;
                case 'Sent to post-editing, accepted':
                    statusSpan.text(language_code === 'en' ? 'Request for quote accepted' : 'Demande de devis acceptée');
                    statusSpan.addClass('text-blue-400');
                    break;
                case 'Post-edited file uploaded':
                    statusSpan.text(language_code === 'en' ? 'Request for quote accepted' : 'Demande de devis acceptée');
                    statusSpan.addClass('text-green-300');
                    break;
                case 'Error':
                    statusSpan.text(language_code === 'en' ? 'Error' : 'Erreur');
                    statusSpan.addClass('text-red-400');
                    break;
                default:
                    statusSpan.text(project.status);
                    statusSpan.addClass('text-gray-600');
                    break;
            }
            statusColumn.append(statusSpan);
            row.append(statusColumn);

            const downloadColumn = $('<td></td>');
            const downloadButton = $(`
            <button type=button class="bg-gray-600 disabled:bg-gray-225 flex gap-2.5 items-center text-white px-7.5 py-3 rounded-md download-file disabled:pointer-events-none" ${project.status !== 'Translated' ? 'disabled' : ''}>
                 ${language_code === 'en' ? 'Download' : 'Télécharger'}
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
                class="text-white flex gap-2.5 items-center bg-green-700 border border-green-700 rounded-md px-2.5 py-3 text-3.25 disabled:pointer-events-none expert-revision"
                ${project.status !== 'Translated' ? 'disabled' : ''}
            >
                ${language_code === 'en' ? "Human revision" : "Relecture expert"}
                <div class="relative group">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M10 0C4.47301 0 0 4.4725 0 10C0 15.5269 4.4725 20 10 20C15.527 20 20 15.5275 20 10C20 4.47309 15.5275 0 10 0ZM11.0269 13.9696C11.0269 14.2855 10.5662 14.6014 10.0002 14.6014C9.40785 14.6014 8.98668 14.2855 8.98668 13.9696V8.95445C8.98668 8.5859 9.40789 8.33574 10.0002 8.33574C10.5662 8.33574 11.0269 8.5859 11.0269 8.95445V13.9696ZM10.0002 7.12484C9.39473 7.12484 8.9209 6.6773 8.9209 6.17707C8.9209 5.67687 9.39477 5.2425 10.0002 5.2425C10.5926 5.2425 11.0665 5.67687 11.0665 6.17707C11.0665 6.6773 10.5925 7.12484 10.0002 7.12484Z" fill="currentColor"/>
                    </svg>
                    <div class="invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-opacity duration-300 absolute z-10 w-48 bg-green-700 text-white text-2.75 rounded-md bottom-30 left-1/2 transform -translate-x-1/2 translate-y-full">
                        <span class="py-4 px-4.5 text-justify text-wrap block">
                                              ${language_code === 'en' ? 'Click the button to see options for improving the quality of the translated file.' : "Cliquez sur ce bouton pour afficher les options de relecture disponibles"}
                        </span>
                        <div class="absolute w-3 h-3 bg-green-700 transform rotate-45 left-1/2 -translate-x-1/2 -bottom-1.5"></div>
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
            url: expert_revision_file_url,
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
                statusSpan.addClass('text-yellow-400');

                statusSpan.text(language_code === 'en' ? 'Request for quote sent' : 'Demande de devis envoyée');
                projectRow.find('.expert-revision').prop('disabled', true).addClass('disabled:pointer-events-none disabled:text-gray-225 disabled:border-gray-225');

                $modalRevision.addClass('hidden');
                $closeRevision.addClass('hidden');
            },
            error: function (error) {
                errorNotification(error?.status, error?.responseJSON?.detail);
            },
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
                    if (response[0].display_popup) {
                        $('.show-modal-false').removeClass('hidden');
                    } else {
                        $('.show-modal-true').removeClass('hidden');
                    }
                    updateProjectTable(response);
                },
                error: function (error) {
                    errorNotification(error?.status, error?.responseJSON?.detail);
                },
                complete: function () {
                    $('#loader-row').addClass('hidden');
                }
            });
        };

        checkDocumentStatus();

        setInterval(checkDocumentStatus, 10000);
    };

    function showTab(tabId) {
        // Masquer tous les contenus de tabs
        $('#step2-tab-default-content').hide();
        $('#step2-tab-no-lexicon-content').hide();
        $('#step2-tab-my-lexicon-content').hide();

        // Afficher le contenu du tab sélectionné
        $(`#step2-tab-${tabId}-content`).show();

        // Retirer les styles actifs de tous les boutons
        $('button.tab-button').removeClass('border-b-0.5 border-b-black');
        $(`#step2-${tabId}`).addClass('border-b-0.5 border-b-black');
    }

    setTimeout(() => showTab('default'), 1000);
    $('#step2-default').click(function () {
        showTab('default');
    });

    $('#step2-my-lexicon').click(function () {
        showTab('my-lexicon');
    });

    $('#step2-no-lexicon').click(function () {
        showTab('no-lexicon');
    });

    // Gestion du clic sur les blocs radio
    $('ul.flex li > div.flex.items-center.mr-2').click(function() {
        // Décoche et enlève le fond bleu sur tous
        $('ul.flex li > div.flex.items-center.mr-2').removeClass('bg-blue-50');
        $('ul.flex li > div.flex.items-center.mr-2 input[type=radio]').prop('checked', false);

        // Coche la radio du bloc cliqué et ajoute fond bleu
        $(this).addClass('bg-blue-50');
        $(this).find('input[type=radio]').prop('checked', true);
    });

    // Fonction pour cliquer automatiquement sur le bouton .domain-button avec data-name
    function clickDomainButton(domainName) {
        // Retire classes de sélection sur tous les boutons
        $('.domain-button').removeClass('selected bg-green-700 text-white').addClass('bg-gray-100 text-gray-475');

        // Cherche le bouton à sélectionner
        var $btn = $('.domain-button[data-name="' + domainName + '"]');
        if ($btn.length) {
            // Déclenche clic sur ce bouton
            $btn.click();

            // Applique classes sélection sur ce bouton
            $btn.addClass('selected bg-green-700 text-white').removeClass('bg-gray-100 text-gray-475');
        }
    }

    // Exemple d’appel : sélectionner automatiquement le bouton "Corporate"
    clickDomainButton('Corporate');
});

// Close warning alert
function closeWarning() {
    $('#warning-alert').addClass('hidden');
}

