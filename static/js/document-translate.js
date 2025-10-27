$(document).ready(function () {
    var $fileInput = $('#file-input');
    var $fileUploadZone = $('#file-upload-zone');
    var $warningAlert = $('#warning-alert');
    var $fileList = $('#file-list');
    var $nextButton = $('#next-step');
    var $blockButtons = $('.block-buttons');
    var uploadedFiles = [];

    // Filtre les langues sources selon la recherche
    $('#source-search-input').on('input keyup change', function () {
        var val = $(this).val().toLowerCase();
        $('.source-language-item').each(function () {
            var text = $(this).text().toLowerCase();
            $(this).toggle(text.indexOf(val) > -1);
        });
    });

    // Filtre les langues cibles selon la recherche
    $('#target-search-input').on('input keyup change', function () {
        var val = $(this).val().toLowerCase();
        $('.target-language-item').each(function () {
            var text = $(this).text().toLowerCase();
            $(this).toggle(text.indexOf(val) > -1);
        });
    });

    // Sélection d'une langue source
    $(document).on('click', '.source-language-item', function () {
        var selectedLang = $(this).data('value');

        // Désélectionne toutes les langues sources
        $('.source-language-item').removeClass('text-green-800 bg-green-100');

        // Sélectionne la ligne cliquée
        $(this).addClass('text-green-800 bg-green-100');

        // Met à jour la variable globale
        sourceLanguage = selectedLang;
        
        // Si sélection pendant la détection, marquer comme annulé et afficher message
        const $status = $('#language-detection-status');
        if (!$status.hasClass('hidden') && $status.find('span').text().includes(language_code === 'en' ? 'Detecting' : 'Détection')) {
            detectionCancelled = true;
            const cancelMessage = language_code === 'en' ? 'Detection cancelled' : 'Détection annulée';
            showLanguageDetectionStatus(cancelMessage, true, '#F59E0B');
        }
        
        // Vérifier la cohérence après sélection
        checkLanguagesConsistency();
    });

    // Sélection d'une langue cible
    $(document).on('click', '.target-language-item', function () {
        var selectedLang = $(this).data('value');

        // Désélectionne toutes les langues cibles
        $('.target-language-item').removeClass('text-green-800 bg-green-100');

        // Sélectionne la ligne cliquée
        $(this).addClass('text-green-800 bg-green-100');

        // Met à jour la variable globale
        targetLanguage = selectedLang;
        
        // Sauvegarder dans le localStorage
        localStorage.setItem('document_translate_target_language', selectedLang);
        
        // Vérifier la cohérence après sélection
        checkLanguagesConsistency();
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
        if (extension === 'xlsx') return 'xlsx';
        if (extension === 'txt') return 'txt';
        return 'pdf'; // default
    }

    function getFileColors(type) {
        const colors = {
            'pdf': { bg: '#FCA5A5', badge: '#DC2626' },      // Rouge (PDF)
            'docx': { bg: '#93C5FD', badge: '#2563EB' },     // Bleu (Word)
            'xlsx': { bg: '#86EFAC', badge: '#16A34A' },     // Vert (Excel)
            'pptx': { bg: '#FDBA74', badge: '#EA580C' },     // Orange (PowerPoint)
            'txt': { bg: '#D1D5DB', badge: '#6B7280' }       // Gris (Texte)
        };
        return colors[type] || colors['pdf'];
    }

    // Pour bouton suppression dynamique
    window.removeFile = function (fileId) {
        selectedFiles = selectedFiles.filter(function (file) {
            return file.fileId !== fileId;
        });
        
        checkPDF(selectedFiles);
        displayFiles(selectedFiles);
        
        // Retirer aussi les éléments du DOM si présents
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


    let sourceLanguage = '';
    let targetLanguage = '';
    let selectedDomain = '';
    let selectedSubDomain = '';
    let defaultDomain = false;
    let selectedGlossaryType = 'default';
    let selectedGlossary = 'none';
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

            // Toujours afficher le bouton suivant
            nextStep.show().css('display', 'flex');
            $actionList.css("justify-content", "flex-end");
            
            // Activer/désactiver selon les fichiers
            if (selectedFiles.length > 0) {
                nextStep.prop('disabled', false).removeClass('opacity-50 cursor-not-allowed');
            } else {
                nextStep.prop('disabled', true).addClass('opacity-50 cursor-not-allowed');
            }

            $("div[class^='step-']").addClass('hidden').hide();
            $('.step-1').removeClass('hidden').show();
            $('.stepindicator-1').removeClass('border border-gray-300').addClass('border-[1.5px] border-[#166534]');
            $('.stepindicator-2').removeClass('border-[1.5px] border-[#166534]').addClass('border border-gray-300');
            $('.stepindicator-3').removeClass('border-[1.5px] border-[#166534]').addClass('border border-gray-300');
            $('.stepindicator-4').removeClass('border-[1.5px] border-[#166534]').addClass('border border-gray-300');
        } else if (currentStep === 1) {
            $("div[class^='step-']").addClass('hidden').hide();
            $('.step-2').removeClass('hidden').show();
            $blockButtons.addClass('justify-between').removeClass('justify-end');
            prevStep.show();
            prevStep.css('display', 'flex');
            prevStep.prop("disabled", false);
            $('.stepindicator-1').removeClass('border border-gray-300').addClass('border-[1.5px] border-[#166534]');
            $('.stepindicator-2').removeClass('border border-gray-300').addClass('border-[1.5px] border-[#166534]');
            $('.stepindicator-3').removeClass('border-[1.5px] border-[#166534]').addClass('border border-gray-300');
            $('.stepindicator-4').removeClass('border-[1.5px] border-[#166534]').addClass('border border-gray-300');
            
            // Réinitialiser les sélections de langues et variables
            sourceLanguage = '';
            targetLanguage = '';
            $('.source-language-item').removeClass('text-green-800 bg-green-100');
            $('.target-language-item').removeClass('text-green-800 bg-green-100');
            
            // Charger la langue cible depuis le localStorage si elle existe
            const savedTargetLanguage = localStorage.getItem('document_translate_target_language');
            if (savedTargetLanguage) {
                targetLanguage = savedTargetLanguage;
                const $savedTargetItem = $(`.target-language-item[data-value="${savedTargetLanguage}"]`);
                if ($savedTargetItem.length) {
                    $savedTargetItem.addClass('text-green-800 bg-green-100');
                }
            }
            
            // Cacher le warning au départ
            $('#language-warning-alert').addClass('hidden');
            
            // Désactiver le bouton Suivant jusqu'à sélection des langues
            nextStep.addClass('opacity-50 cursor-not-allowed').prop('disabled', true);
            
            // Lancer la détection de langue
            detectLanguageFiles();
            
            // Appeler checkLanguagesConsistency pour initialiser l'état
            checkLanguagesConsistency();
        } else if (currentStep === 2) {
            $("div[class^='step-']").addClass('hidden').hide();
            $('.step-3').removeClass('hidden').show();
            $blockButtons.addClass('justify-between').removeClass('justify-end');
            prevStep.show();
            $('span', $nextButton).text(language_code === 'en' ? 'Next' : 'Suivant');
            $('.stepindicator-1').removeClass('border border-gray-300').addClass('border-[1.5px] border-[#166534]');
            $('.stepindicator-2').removeClass('border border-gray-300').addClass('border-[1.5px] border-[#166534]');
            $('.stepindicator-3').removeClass('border border-gray-300').addClass('border-[1.5px] border-[#166534]');
            $('.stepindicator-4').removeClass('border-[1.5px] border-[#166534]').addClass('border border-gray-300');
            
            // Activer le bouton Suivant par défaut sur step 3 (glossaire optionnel)
            nextStep.removeClass('border-gray-225 text-gray-225 opacity-50 cursor-not-allowed')
                .addClass('border-green-700 text-green-700')
                .prop("disabled", false);
            
            // Charger automatiquement les groupes de domaines
            getDomainsGroups();
            
            // Charger automatiquement les glossaires My glossaries si les langues sont définies
            if (sourceLanguage && targetLanguage) {
                loadMyGlossaries();
            }
        } else if (currentStep === 3) {
            $("div[class^='step-']").addClass('hidden').hide();
            $('.step-4').removeClass('hidden').show();
            $blockButtons.addClass('justify-between').removeClass('justify-end');
            prevStep.show();
            $('span', $nextButton).text(language_code === 'en' ? 'Finish' : 'Terminé');
            $('.stepindicator-1').removeClass('border border-gray-300').addClass('border-[1.5px] border-[#166534]');
            $('.stepindicator-2').removeClass('border border-gray-300').addClass('border-[1.5px] border-[#166534]');
            $('.stepindicator-3').removeClass('border border-gray-300').addClass('border-[1.5px] border-[#166534]');
            $('.stepindicator-4').removeClass('border border-gray-300').addClass('border-[1.5px] border-[#166534]');
            
            // Déclencher la requête de traduction à l'arrivée sur step_4
            fileTranslate();
        } else if (currentStep === 4) {
            $("div[class^='step-']").addClass('hidden').hide();
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

            // Empêcher le clic si le bouton est désactivé
            if (nextStep.prop('disabled')) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }

            if (currentStep === 0 && selectedFiles.length === 0) {
                return;
            }
            if (currentStep === 0) {
                // Pas de détection automatique - l'utilisateur choisit manuellement
                checkLanguagesConsistency()
            }
            if (currentStep === 1) {
                // Vérifier que les langues sont bien sélectionnées et différentes
                const hasSourceLanguage = sourceLanguage && sourceLanguage !== '';
                const hasTargetLanguage = targetLanguage && targetLanguage !== '';
                const languagesAreDifferent = sourceLanguage !== targetLanguage;
                
                if (!hasSourceLanguage || !hasTargetLanguage || !languagesAreDifferent) {
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                }
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

            if (currentStep === 3) {
                // Rediriger vers le dashboard quand on clique sur "Terminé"
                window.location.href = '/fr/dashboard/';
                return;
            }

            console.log('currentStep : ' + currentStep);

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
        const hasFiles = selectedFiles.length > 0;
        
        if (hasFiles) {
            $('#file-list').removeClass('hidden');
            $('#next-step').prop('disabled', false).removeClass('opacity-50 cursor-not-allowed');
        } else {
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
            // Calculer la taille appropriée (KB ou MB)
            var fileSize;
            var sizeInMB = file.size / 1024 / 1024;
            if (sizeInMB < 0.1) {
                // Afficher en KB si moins de 0.1 MB
                fileSize = (file.size / 1024).toFixed(1) + ' KB';
            } else {
                // Afficher en MB
                fileSize = sizeInMB.toFixed(1) + ' MB';
            }
            
            return {
                id: 'file-' + Date.now() + '-' + index,
                name: file.name,
                size: fileSize,
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
            
            const colors = getFileColors(file.type);

            const $fileItem = $(`
            <div class="flex items-center justify-between gap-2 p-3 rounded-lg border border-black/10 bg-white w-full sm:w-[calc(50%-0.5rem)] md:w-[calc(33.333%-0.667rem)] lg:w-[calc(25%-0.75rem)] xl:w-[calc(20%-0.8rem)]" style="min-width: 200px;">
                <div class="flex items-center gap-2 flex-1 min-w-0">
                    <div class="w-8 h-10 relative flex-shrink-0">
                        <svg class="w-8 h-10 shrink-0 absolute left-0 top-0" width="32" height="40" viewBox="0 0 32 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M0 36V4C0 1.79086 1.79086 0 4 0H19.9C20.9271 0 21.9149 0.395099 22.6586 1.10345L30.7586 8.81773C31.5513 9.57271 32 10.6196 32 11.7143V36C32 38.2091 30.2091 40 28 40H4C1.79086 40 0 38.2091 0 36Z" fill="${colors.bg}"/>
                        </svg>
                        <div class="inline-flex px-1 items-center justify-center rounded-sm absolute -left-1 top-[18px] h-4 min-w-[26px]" style="background-color: ${colors.badge};">
                            <span class="font-inter text-[9px] font-bold leading-4 tracking-[0.144px] text-white uppercase whitespace-nowrap">
                                ${file.type}
                            </span>
                        </div>
                    </div>
                    <div class="flex flex-col justify-center items-start min-w-0 flex-1">
                        <div class="font-poppins text-base font-normal leading-6 tracking-[-0.176px] text-[#181932] truncate w-full">
                            ${file.name}
                        </div>
                        <div class="font-poppins text-sm font-normal leading-6 tracking-[-0.084px] text-[#5A5A78]">
                            ${file.size}
                        </div>
                    </div>
                </div>
                <button onclick="removeFile('${fileId}')" class="w-6 h-6 text-black/80 hover:text-red-600 transition-colors flex-shrink-0">
                    <i class="ph ph-trash" style="font-size: 24px;"></i>
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

        if (currentStep === 0) {
            prevStep.hide();
            $blockButtons.removeClass('justify-between').addClass('justify-end');

            // Toujours afficher le bouton suivant
            nextStep.show().css('display', 'flex');
            $("#restart").hide();
            $("#restart-text").hide();

            $actionList.css("justify-content", "flex-end");
            
            // Activer/désactiver selon les fichiers
            if (filesExist) {
                nextStep.prop('disabled', false).removeClass('opacity-50 cursor-not-allowed');
            } else {
                nextStep.prop('disabled', true).addClass('opacity-50 cursor-not-allowed');
            }
        }

        $fileList.toggleClass('hidden', !filesExist);
    }

    function checkPDF(files) {
        const isPdf = files.some(file => file.name.toLowerCase().endsWith('.pdf'));
        $(".pdf-document").toggleClass('hidden', !isPdf);
        // Afficher le warning uniquement si au moins un PDF est présent
        $('#warning-alert').toggleClass('hidden', !isPdf);
    }



    // ------------- STEP-2 -------------

    // Fonction pour afficher le statut de détection de langue
    function showLanguageDetectionStatus(message, autoHide = false, color = '#5A5A78', showSpinner = false) {
        const $status = $('#language-detection-status');
        const $span = $status.find('span');
        
        // Ajouter spinner si détection en cours
        if (showSpinner) {
            $span.html(`<i class="ph ph-circle-notch" style="font-size: 16px; margin-right: 8px; display: inline-block; animation: rotation 1s linear infinite;"></i>${message}`).css('color', color);
        } else {
            $span.text(message).css('color', color);
        }
        
        // Afficher avec fondu
        $status.removeClass('hidden').css('opacity', '1');
        
        if (autoHide) {
            setTimeout(() => {
                // Disparition en fondu
                $status.css('transition', 'opacity 0.5s ease-out');
                $status.css('opacity', '0');
                
                // Cacher complètement après l'animation
                setTimeout(() => {
                    $status.addClass('hidden');
                }, 1000);
            }, 5000);
        }
    }
    
    function hideLanguageDetectionStatus() {
        $('#language-detection-status').addClass('hidden');
    }

    let detectionCancelled = false;
    
    function detectLanguageFiles() {
        if (selectedFiles.length === 0) {
            return;
        }

        // Si l'utilisateur a déjà sélectionné une langue source, ignorer la détection
        if (sourceLanguage && sourceLanguage !== '') {
            return;
        }

        // Réinitialiser le flag d'annulation
        detectionCancelled = false;

        // Afficher le message de détection en cours avec spinner
        const detectionMessage = language_code === 'en' ? 'Detecting language...' : 'Détection de la langue en cours...';
        showLanguageDetectionStatus(detectionMessage, false, '#5A5A78', true);

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
                // Si détection annulée, ne rien faire
                if (detectionCancelled) {
                    return;
                }
                
                // Si l'utilisateur a sélectionné une langue pendant le chargement, marquer comme annulé
                if (sourceLanguage && sourceLanguage !== '') {
                    detectionCancelled = true;
                    const cancelMessage = language_code === 'en' ? 'Detection cancelled' : 'Détection annulée';
                    showLanguageDetectionStatus(cancelMessage, true, '#F59E0B');
                    return;
                }
                
                // Compter les occurrences de chaque langue
                const languageCounts = {};
                response.languages.forEach(lang => {
                    const abbr = lang.abbreviation.toLowerCase();
                    languageCounts[abbr] = (languageCounts[abbr] || 0) + 1;
                });
                
                // Trouver la langue la plus fréquente
                let mostCommonLang = null;
                let maxCount = 0;
                for (const [lang, count] of Object.entries(languageCounts)) {
                    if (count > maxCount) {
                        maxCount = count;
                        mostCommonLang = lang;
                    }
                }
                
                const isSameLanguages = Object.keys(languageCounts).length === 1;
                
                if (mostCommonLang) {
                    // Sélectionner la langue la plus commune
                    sourceLanguage = mostCommonLang;
                    
                    // Mettre en surbrillance dans le tableau
                    const $sourceLangItem = $(`.source-language-item[data-value="${mostCommonLang}"]`);
                    $sourceLangItem.addClass('text-green-800 bg-green-100');
                    
                    // Afficher le warning si langues différentes
                    if (!isSameLanguages) {
                        $('#language-warning-alert').removeClass('hidden');
                    } else {
                        $('#language-warning-alert').addClass('hidden');
                    }
                    
                    // Afficher message de succès
                    const successMessage = language_code === 'en' ? 'Language detected' : 'Langue détectée';
                    showLanguageDetectionStatus(successMessage, true, '#16A34A');
                }
                
                checkLanguagesConsistency();
            },
            error: function (error) {
                // Si détection annulée, ne rien faire
                if (detectionCancelled) {
                    return;
                }
                
                // En cas d'erreur, afficher un message d'erreur
                const errorMessage = language_code === 'en' ? 'Language detection error' : 'Erreur lors de détection de langue';
                showLanguageDetectionStatus(errorMessage, true, '#DC2626');
            },
            complete: function () {
                // Ne rien faire ici, les messages gèrent leur propre disparition
            },
        });
    }


    function checkLanguagesConsistency() {
        // Vérifier si les deux langues sont sélectionnées et valides
        const hasSourceLanguage = sourceLanguage && sourceLanguage !== '';
        const hasTargetLanguage = targetLanguage && targetLanguage !== '';
        const languagesAreDifferent = sourceLanguage !== targetLanguage;
        const canProceed = hasSourceLanguage && hasTargetLanguage && languagesAreDifferent;

        if (!canProceed) {
            // Désactiver le bouton Suivant
            nextStep.removeClass('border-green-700 text-white text-green-700')
                .addClass('border-gray-225 text-gray-225 opacity-50 cursor-not-allowed')
                .prop("disabled", true);
        } else {
            // Activer le bouton Suivant
            nextStep.removeClass('border-gray-225 text-gray-225 opacity-50 cursor-not-allowed')
                .addClass('border-green-700 text-green-700')
                .prop("disabled", false);
            $('.language-step').removeClass('hidden');
        }
    }



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
    
    // Fonction utilitaire pour créer un élément de sélection (radio + label + icône)
    function createSelectionItem(config) {
        const {
            radioId,
            radioName,
            value,
            isChecked,
            icon,
            label,
            containerClass = '',
            containerStyle = '',
            onChange
        } = config;
        
        // Créer l'élément liste
        const listItem = $('<li>', {
            class: 'flex items-center',
            style: containerStyle
        });
        
        // Créer le conteneur
        const container = $('<div>', {
            class: `flex items-center w-full rounded-lg p-2 cursor-pointer transition-colors hover:bg-blue-50 ${containerClass} ${isChecked ? 'bg-blue-50' : ''}`,
            'data-value': value
        });
        
        // Créer le radio button (12x12)
        const radio = $('<input>', {
            id: radioId,
            type: 'radio',
            name: radioName,
            value: value,
            class: 'w-3 h-3 text-blue-600 bg-gray-100 border-gray-300 focus:ring-blue-500',
            checked: isChecked
        });
        
        if (onChange) {
            radio.on('change', onChange);
        }
        
        // Créer l'icône
        const iconHtml = icon ? `<i class="ph ph-${icon} mx-2" style="font-size: 24px;" aria-hidden="true"></i>` : '';
        
        // Créer le label
        const labelElement = $('<label>', {
            for: radioId,
            class: 'ms-2 flex h-8 items-center cursor-pointer',
            html: iconHtml + `<span class="font-poppins text-sm font-normal leading-6 tracking-[-0.084px]" style="font-size: 14px; line-height: 24px;">${label}</span>`
        });
        
        // Assembler les éléments
        container.append(radio).append(labelElement);
        listItem.append(container);
        
        return { listItem, container, radio };
    }

    function updateDomainsList(domains) {
        const domainsList = $('.domains-list');
        domainsList.empty();

        domains.forEach((domain, index) => {
            const isFirst = index === 0;
            
            const { listItem } = createSelectionItem({
                radioId: `domain-radio-${index}`,
                radioName: 'domain-radio',
                value: domain.name,
                isChecked: isFirst,
                icon: domain.icon,
                label: domain.name,
                containerClass: 'domain-container',
                containerStyle: 'flex: 0 0 calc(20% - 6.4px);',
                onChange: function () {
                    $('.domains-list .domain-container').removeClass('bg-blue-50');
                    $(this).closest('.domain-container').addClass('bg-blue-50');
                    selectedDomain = $(this).val();
                    getDomains();
                }
            });
            
            domainsList.append(listItem);
            
            if (isFirst) {
                selectedDomain = domain.name;
            }
        });

        getDomains();
    }

    function updateSubDomainsList(subDomains) {
        const subDomainsList = $('.sub-domain-list');
        subDomainsList.empty();

        subDomains.forEach((subDomain, index) => {
            const domainName = typeof subDomain === 'object' ? subDomain.name : subDomain;
            const domainIcon = typeof subDomain === 'object' && subDomain.icon ? subDomain.icon : null;
            const isFirst = index === 0;
            
            const { listItem } = createSelectionItem({
                radioId: `subdomain-radio-${index}`,
                radioName: 'subdomain-radio',
                value: domainName,
                isChecked: isFirst,
                icon: domainIcon,
                label: domainName,
                containerClass: 'subdomain-container',
                containerStyle: 'flex: 0 0 calc(20% - 6.4px);',
                onChange: function () {
                    $('.sub-domain-list .subdomain-container').removeClass('bg-blue-50');
                    $(this).closest('.subdomain-container').addClass('bg-blue-50');
                    selectedSubDomain = $(this).val();
                    $('.domain-step').text(selectedSubDomain).removeClass('hidden');
                    loadDefaultGlossary();
                }
            });
            
            subDomainsList.append(listItem);
            
            if (isFirst) {
                selectedSubDomain = domainName;
                $('.domain-step').text(selectedSubDomain).removeClass('hidden');
                loadDefaultGlossary();
            }
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
                
                // Si default_domain === true : masquer la section sous-domaine et utiliser "Generic domain"
                if (response.default_domain) {
                    $('#subdomain-section').hide();
                    $('#glossary-section-number').text('2. ' + (language_code === 'en' ? 'Select a glossary' : 'Sélectionner un glossaire'));
                    selectedSubDomain = 'Generic domain';
                    
                    // Charger le glossaire par défaut pour Generic domain
                    loadDefaultGlossary();
                } else {
                    // Sinon, afficher la section sous-domaine
                    $('#subdomain-section').show();
                    $('#glossary-section-number').text('3. ' + (language_code === 'en' ? 'Select a glossary' : 'Sélectionner un glossaire'));
                    
                    if (response.data && response.data.length > 0) {
                        // Mettre à jour la liste des sous-domaines
                        updateSubDomainsList(response.data);
                    } else {
                        $('.sub-domain-list').empty();
                        selectedSubDomain = '';
                    }
                }
                
                // Note: L'affichage du tab "Standard" sera géré par loadDefaultGlossary()
                // en fonction du résultat de l'API default_glossary
                
                // Activer le bouton Suivant
                    nextStep.removeClass('border-gray-225 text-gray-225 pointer-events-none')
                        .addClass('border-green-700 text-green-700')
                        .prop("disabled", false);
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
                // Si la réponse est un objet vide {}, cacher le tab Standard
                if (!response || Object.keys(response).length === 0) {
                    $("#step2-default").addClass('hidden');
                    $("#step2-my-glossary").removeClass('pr-4').addClass('pr-4 pl-0');
                    $(".add-glossary-btn").removeClass('hidden');
                    selectedGlossaryType = 'my-glossary';
                    
                    // Attendre un court instant que loadMyGlossaries() se termine avant de basculer
                    setTimeout(function() {
                        showTab('my-glossary');
                    }, 300);
                } else {
                    // Afficher le tab Standard et afficher le glossaire
                    $("#step2-default").removeClass('hidden');
                    $("#step2-my-glossary").removeClass('pl-0').addClass('pl-4');
                    $(".add-glossary-btn").addClass('hidden');
                    selectedGlossaryType = 'default';
                    displayDefaultGlossaryInStep3(response);
                    // Basculer vers "Standard"
                    showTab('default');
                }
            },
            error: function (error) {
                // En cas d'erreur, cacher le tab Standard et basculer vers My glossaries
                $("#step2-default").addClass('hidden');
                $("#step2-my-glossary").removeClass('pr-4').addClass('pr-4 pl-0');
                $(".add-glossary-btn").removeClass('hidden');
                selectedGlossaryType = 'my-glossary';
                
                // Attendre un court instant que loadMyGlossaries() se termine avant de basculer
                setTimeout(function() {
                    showTab('my-glossary');
                }, 300);
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
                // Afficher dans step_3 (My glossaries tab)
                displayMyGlossariesInStep3(response);
                
                // Note: Le bouton Suivant reste actif car le glossaire est optionnel
                // Il sera géré par showTab() si nécessaire
            },
            error: function (error) {
                errorNotification(error?.status, error?.responseJSON?.detail);
            },
        });
    }

    function displayDefaultGlossaryInStep3(glossary) {
        const container = $('.glossary-list');
        container.empty();
        
        const { listItem, container: glossaryContainer } = createSelectionItem({
            radioId: 'default-glossary-radio',
            radioName: 'default-glossary-radio',
            value: glossary.id,
            isChecked: true,
            icon: 'file',
            label: glossary.name,
            containerClass: '',
            containerStyle: 'flex: 0 0 100%;'
        });
        
        // Ajouter un ID unique pour la restauration lors du changement de tab
        glossaryContainer.attr('id', 'default-glossary-container');
        
        container.append(listItem);
        selectedGlossary = glossary.id;
    }

    function displayMyGlossariesInStep3(glossaries) {
        const container = $('#step2-tab-my-glossary-content');
        container.empty();
        
        if (!glossaries || glossaries.length === 0) {
            container.html(`
                <div class="flex flex-col items-center justify-center pt-6 pb-0">
                    <p class="font-poppins font-normal text-gray-600" style="font-size: 14px; line-height: 24px;">${language_code === 'en' ? 'No glossaries found' : 'Aucun glossaire trouvé'}</p>
                </div>
            `);
            return;
        }
        
        const glossaryList = $('<ul>', {
            class: 'flex flex-row flex-wrap items-start w-full gap-2'
        });
        
        glossaries.forEach((glossary, index) => {
            const isFirst = index === 0;
            
            const { listItem } = createSelectionItem({
                radioId: `glossary-radio-${index}`,
                radioName: 'glossary-radio',
                value: glossary.id,
                isChecked: isFirst,
                icon: 'file',
                label: glossary.name,
                containerClass: 'glossary-container',
                containerStyle: 'flex: 0 0 calc(25% - 6px);',
                onChange: function () {
                    $('.glossary-container').removeClass('bg-blue-50');
                    $(this).closest('.glossary-container').addClass('bg-blue-50');
                    selectedGlossary = $(this).val();
                }
            });
            
            glossaryList.append(listItem);
            
            if (isFirst) {
                selectedGlossary = glossary.id;
            }
        });
        
        container.append(glossaryList);
    }

    function updateGlossaryList(glossaries, isDefault) {

        const $list = $(".glossary-list");

        $list.empty();

        glossaries.forEach(function (glossary) {
            const $item = $(`<button type="button" class="border border-gray-300  glossary-item text-3.5 py-3 px-7.5 ${isDefault ? "bg-green-700 text-white" : "bg-gray-175 text-gray-375"} rounded-md hover:bg-green-700 hover:text-white transition duration-300 ease-in-out">${glossary.name}</button>`);
            $item.click(function () {
                if (selectedGlossary === glossary.id) {
                    $(this).removeClass('bg-green-700 text-white').addClass('bg-gray-175 text-gray-375');
                    selectedGlossary = 'none';
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
                        selectedGlossary = 'none';
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
        // Console log pour afficher le domaine et le glossaire sélectionnés
        console.log('=== INFORMATIONS DE TRADUCTION ===');
        console.log('Domaine sélectionné:', selectedSubDomain);
        console.log('Glossaire sélectionné:', selectedGlossary);
        console.log('Langue source:', sourceLanguage);
        console.log('Langue cible:', targetLanguage);
        console.log('================================');

        const formData = new FormData();
        selectedFiles.forEach((file) => {
            formData.append(`document[]`, file.file);
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
        const documentsContainer = $('#documents-container');
        documentsContainer.empty();

        projects.forEach(project => {
            // Créer la ligne du document avec le style du dashboard
            const documentRow = $(`
                <tr>
                    <td>
                        <span class="doc-title">${project.source_file_name}</span>
                    </td>
                    <td>
                        <span class="lang-label">${sourceLanguage.toUpperCase()} → ${targetLanguage.toUpperCase()}</span>
                    </td>
                    <td class="status-col">
                        <span class="status-badge ${getStatusClass(project.status)}">
                            <i class="ph ${getStatusIcon(project.status)}" style="font-size: 16px;"></i>
                            ${getStatusText(project.status)}
                        </span>
                    </td>
                    <td class="table-actions">
                        <button 
                            class="download-file" 
                            data-translated-file="${project.translated_file}" 
                            data-reviewed-file="${project.reviewed_file || ''}"
                            title="${language_code === 'en' ? 'Download' : 'Télécharger'}"
                            ${project.status !== 'Translated' ? 'disabled style="opacity: 0.5; cursor: not-allowed;"' : ''}>
                            <i class="ph ph-download" style="font-size: 16px; color: #374151;"></i>
                        </button>
                        <button 
                            class="expert-revision text-green-600 hover:text-green-700 font-poppins text-sm font-normal underline" 
                            data-translated-file="${project.translated_file}" 
                            data-id="${project.id}"
                            ${project.status !== 'Translated' ? 'disabled style="opacity: 0.5; cursor: not-allowed; text-decoration: none;"' : ''}>
                            ${language_code === 'en' ? 'Expert review' : 'Révision d\'un expert'}
                        </button>
                    </td>
                </tr>
            `);

            documentsContainer.append(documentRow);
        });

        initializeDownloadButtons();
        initializeRevisionButtons();
    }

    function getStatusText(status) {
        switch (status) {
                case 'Being translated':
                return language_code === 'en' ? 'Processing...' : 'En cours...';
                case 'Translated':
                return language_code === 'en' ? 'Translated document' : 'Document traduit';
                case 'Sent to post-editing, not accepted yet':
                return language_code === 'en' ? 'Request for quote sent' : 'Demande de devis envoyée';
                case 'Sent to post-editing, accepted':
                return language_code === 'en' ? 'Request for quote accepted' : 'Demande de devis acceptée';
                case 'Post-edited file uploaded':
                return language_code === 'en' ? 'Proofread document uploaded' : 'Document relu importé';
                case 'Error':
                return language_code === 'en' ? 'Error' : 'Erreur';
                default:
                return status;
        }
    }

    function getStatusClass(status) {
        switch (status) {
            case 'Being translated':
                return 'status-progress';
            case 'Translated':
                return 'status-completed';
            case 'Sent to post-editing, not accepted yet':
            case 'Sent to post-editing, accepted':
                return 'status-attention';
            case 'Post-edited file uploaded':
                return 'status-completed';
            case 'Error':
                return 'status-error';
            default:
                return 'status-default';
        }
    }

    function getStatusIcon(status) {
        switch (status) {
            case 'Being translated':
                return 'ph-clock-clockwise';
            case 'Translated':
                return 'ph-check-circle';
            case 'Sent to post-editing, not accepted yet':
            case 'Sent to post-editing, accepted':
                return 'ph-hourglass';
            case 'Post-edited file uploaded':
                return 'ph-check-circle';
            case 'Error':
                return 'ph-warning-circle';
            default:
                return 'ph-circle';
        }
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
                
                // Mettre à jour le badge de statut (colonne 3, index 2)
                const statusBadge = projectRow.find('td:eq(2) .status-badge');
                statusBadge.removeClass('status-completed status-progress status-error status-default')
                    .addClass('status-attention');
                statusBadge.find('i').removeClass().addClass('ph ph-hourglass');
                statusBadge.contents().filter(function() {
                    return this.nodeType === 3; // Text node
                }).last().replaceWith(language_code === 'en' ? 'Request for quote sent' : 'Demande de devis envoyée');
                
                // Désactiver le bouton de révision
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
        let statusCheckInterval;
        
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
                    
                    // Vérifier si tous les projets ont un statut différent de "Being translated"
                    const allProjectsFinished = response.every(project => project.status !== 'Being translated');
                    
                    if (allProjectsFinished) {
                        console.log('Tous les projets sont terminés, arrêt de la boucle de vérification');
                        clearInterval(statusCheckInterval);
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

        checkDocumentStatus();

        statusCheckInterval = setInterval(checkDocumentStatus, 10000);
    };

    function showTab(tabId) {
        // Masquer tous les contenus de tabs
        $('#step2-tab-default-content').hide();
        $('#step2-tab-no-glossary-content').hide();
        $('#step2-tab-my-glossary-content').hide();

        // Réinitialiser toutes les sélections visuelles
        $('.subdomain-container').removeClass('bg-blue-50');
        // Ne pas réinitialiser le glossaire par défaut dans le tab Standard
        $('#step2-tab-my-glossary-content .glossary-container').removeClass('bg-blue-50');
        $('input[type="radio"][name="sub_domain"]').prop('checked', false);
        $('input[type="radio"][name="glossary-radio"]').prop('checked', false);

        // Afficher le contenu du tab sélectionné et sélectionner automatiquement le premier élément
        if (tabId === 'default') {
            $('#step2-tab-default-content').show();
            // Restaurer le glossaire par défaut s'il existe
            const defaultGlossaryContainer = $('#default-glossary-container');
            if (defaultGlossaryContainer.length) {
                const defaultGlossaryRadio = defaultGlossaryContainer.find('input[type="radio"]');
                defaultGlossaryRadio.prop('checked', true);
                defaultGlossaryContainer.addClass('bg-blue-50');
                selectedGlossary = defaultGlossaryRadio.val();
            } else {
                selectedGlossary = 'none';
            }
        } else if (tabId === 'no-glossary') {
            $('#step2-tab-no-glossary-content').show();
            // Pour "No glossary", sélectionner automatiquement "none"
            selectedGlossary = 'none';
            $('.terminology-step').text(language_code === 'en' ? 'none' : 'aucun').removeClass('hidden');
        } else if (tabId === 'my-glossary') {
        $(`#step2-tab-${tabId}-content`).show();
            
            // Sélectionner automatiquement le premier glossaire My glossaries s'il existe
            const firstGlossary = $('#step2-tab-my-glossary-content .glossary-container').first();
            if (firstGlossary.length) {
                firstGlossary.addClass('bg-blue-50');
                const firstRadio = firstGlossary.find('input[type="radio"]');
                firstRadio.prop('checked', true);
                selectedGlossary = firstRadio.val();
            } else {
                selectedGlossary = 'none';
            }
        }

        // Retirer les styles actifs de tous les boutons
        $('button.tab-button').removeClass('border-b-0.5 border-b-black');
        $(`#step2-${tabId}`).addClass('border-b-0.5 border-b-black');
        
        // S'assurer que le bouton Suivant reste actif lors du changement de tab
        nextStep.removeClass('border-gray-225 text-gray-225 opacity-50 cursor-not-allowed')
            .addClass('border-green-700 text-green-700')
            .prop("disabled", false);
    }

    $('#step2-default').click(function () {
        showTab('default');
    });

    $('#step2-my-glossary').click(function () {
        showTab('my-glossary');
        // Charger les glossaires de l'utilisateur
        if (sourceLanguage && targetLanguage && selectedSubDomain) {
            loadMyGlossaries();
        }
    });

    $('#step2-no-glossary').click(function () {
        showTab('no-glossary');
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


