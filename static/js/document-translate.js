$(document).ready(function () {
    // Get API URL from translate-config element (set by translate.js)
    var api_lara_glossary_search = window.api_lara_glossary_search || (function() {
        var el = document.getElementById('translate-config');
        return el ? el.dataset.apiLaraGlossarySearch : null;
    })();

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
        if (!$status.hasClass('hidden') && $status.find('span').text().includes(getTranslation('Detecting', 'Détection'))) {
            detectionCancelled = true;
            const cancelMessage = getTranslation('Detection cancelled', 'Détection annulée');
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
    let selectedSubDomainId = null;  // Domain ID for LARA backend
    let selectedSubDomainEnglishName = '';  // English domain name for LARA
    let defaultDomain = false;
    let selectedGlossary = 'none';
    let selectedPersonalGlossaries = [];  // Array for multi-select personal glossaries
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
                enableNextButton();
            } else {
                disableNextButton();
            }

            $("div[class^='step-']").addClass('hidden').hide();
            $('.step-document').removeClass('hidden').show();
            $('.stepindicator-1').removeClass('border border-gray-300').addClass('border-[1.5px] border-[#166534]');
            $('.stepindicator-2').removeClass('border-[1.5px] border-[#166534]').addClass('border border-gray-300');
            $('.stepindicator-3').removeClass('border-[1.5px] border-[#166534]').addClass('border border-gray-300');
            $('.stepindicator-4').removeClass('border-[1.5px] border-[#166534]').addClass('border border-gray-300');
        } else if (currentStep === 1) {
            $("div[class^='step-']").addClass('hidden').hide();
            $('.step-language').removeClass('hidden').show();
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
            disableNextButton();
            
            // Lancer la détection de langue
            detectLanguageFiles();
            
            // Appeler checkLanguagesConsistency pour initialiser l'état
            checkLanguagesConsistency();
        } else if (currentStep === 2) {
            $("div[class^='step-']").addClass('hidden').hide();
            $('.step-domain').removeClass('hidden').show();
            $blockButtons.addClass('justify-between').removeClass('justify-end');
            prevStep.show();
            $('span', $nextButton).text(getTranslation('Next', 'Suivant'));
            $('.stepindicator-1').removeClass('border border-gray-300').addClass('border-[1.5px] border-[#166534]');
            $('.stepindicator-2').removeClass('border border-gray-300').addClass('border-[1.5px] border-[#166534]');
            $('.stepindicator-3').removeClass('border border-gray-300').addClass('border-[1.5px] border-[#166534]');
            $('.stepindicator-4').removeClass('border-[1.5px] border-[#166534]').addClass('border border-gray-300');
            
            // Activer le bouton Suivant par défaut sur step 3 (glossaire optionnel)
            enableNextButton();
            
            // Charger automatiquement les groupes de domaines
            getDomainsGroups();
            
            // Charger automatiquement les glossaires My glossaries si les langues sont définies
            if (sourceLanguage && targetLanguage) {
                loadMyGlossaries();
            }
        } else if (currentStep === 3) {
            $("div[class^='step-']").addClass('hidden').hide();
            $('.step-traduction').removeClass('hidden').show();
            $blockButtons.addClass('justify-between').removeClass('justify-end');
            prevStep.show();
            $('span', $nextButton).text(getTranslation('Finish', 'Terminé'));
            $('.stepindicator-1').removeClass('border border-gray-300').addClass('border-[1.5px] border-[#166534]');
            $('.stepindicator-2').removeClass('border border-gray-300').addClass('border-[1.5px] border-[#166534]');
            $('.stepindicator-3').removeClass('border border-gray-300').addClass('border-[1.5px] border-[#166534]');
            $('.stepindicator-4').removeClass('border border-gray-300').addClass('border-[1.5px] border-[#166534]');
            
            // Déclencher la requête de traduction à l'arrivée sur step-traduction
            fileTranslate();
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
                // Don't reset selections when clicking Next (user might have selected glossaries)
                loadMyGlossaries(false);
                $(".add-glossary-btn").removeClass('hidden');
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
                enableNextButton();

                $('.step-container').removeClass('bg-red-100 border-red-200');
            }
        }
    });

    $("#restart").click(function () {
        window.location.reload();
    });

    showStep(currentStep);


    // ------------- STEP-DOCUMENT -------------


    const allowedTypes = ['.txt', '.pdf', '.docx', '.xlsx', '.pptx'];
    const MAX_CSV_FILENAME_LENGTH = 128;

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

        // Validation spécifique pour les CSV : longueur max du nom de fichier
        filteredFiles = filteredFiles.filter(function (file) {
            var ext = '.' + file.name.split('.').pop().toLowerCase();
            if (ext === '.csv' && file.name.length > MAX_CSV_FILENAME_LENGTH) {
                // Message UI clair, sans déclencher d'upload inutile
                alert(getTranslation(
                    'The CSV filename must not exceed 128 characters.',
                    'Le nom du fichier CSV ne doit pas dépasser 128 caractères.'
                ));
                return false;
            }
            return true;
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
                enableNextButton();
            } else {
                disableNextButton();
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



    // ------------- STEP-LANGUAGE -------------

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
        const detectionMessage = getTranslation('Detecting language...', 'Détection de la langue en cours...');
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
            headers: getAjaxHeaders(),
            success: function (response) {
                // Si détection annulée, ne rien faire
                if (detectionCancelled) {
                    return;
                }
                
                // Si l'utilisateur a sélectionné une langue pendant le chargement, marquer comme annulé
                if (sourceLanguage && sourceLanguage !== '') {
                    detectionCancelled = true;
                    const cancelMessage = getTranslation('Detection cancelled', 'Détection annulée');
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
                    const successMessage = getTranslation('Language detected', 'Langue détectée');
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
                const errorMessage = getTranslation('Language detection error', 'Erreur lors de détection de langue');
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
            disableNextButton();
        } else {
            enableNextButton();
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


    // ------------- STEP-DOMAIN -------------
    
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
            dataAttributes = {},
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

        // Ajouter les data attributes au radio button
        if (dataAttributes) {
            Object.keys(dataAttributes).forEach(key => {
                radio.data(key, dataAttributes[key]);
            });
        }

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
            const domainId = typeof subDomain === 'object' ? subDomain.id : null;
            const domainEnglishName = typeof subDomain === 'object' ? subDomain.english_name : subDomain;
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
                dataAttributes: {
                    'domain-id': domainId,
                    'english-name': domainEnglishName
                },
                onChange: function () {
                    $('.sub-domain-list .subdomain-container').removeClass('bg-blue-50');
                    $(this).closest('.subdomain-container').addClass('bg-blue-50');
                    selectedSubDomain = $(this).val();
                    selectedSubDomainId = $(this).data('domain-id');
                    selectedSubDomainEnglishName = $(this).data('english-name');
                    $('.domain-step').text(selectedSubDomain).removeClass('hidden');
                }
            });

            subDomainsList.append(listItem);

            if (isFirst) {
                selectedSubDomain = domainName;
                selectedSubDomainId = domainId;
                selectedSubDomainEnglishName = domainEnglishName;
                $('.domain-step').text(selectedSubDomain).removeClass('hidden');
            }
        });
    }

    // ============= UTILITY FUNCTIONS =============
    
    /**
     * Get translation based on current language code
     * @param {string} enText - English text
     * @param {string} frText - French text
     * @returns {string} Translated text
     */
    function getTranslation(enText, frText) {
        return language_code === 'en' ? enText : frText;
    }

    /**
     * Get standard AJAX headers for API calls
     */
    function getAjaxHeaders() {
        return {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
        };
    }

    /**
     * Standard error handler for AJAX calls
     */
    function handleAjaxError(error) {
        errorNotification(error?.status, error?.responseJSON?.detail);
    }

    /**
     * Enable the Next button
     */
    function enableNextButton() {
        nextStep.removeClass('border-gray-225 text-gray-225 pointer-events-none opacity-50 cursor-not-allowed')
            .addClass('border-green-700 text-green-700')
            .prop("disabled", false);
    }

    /**
     * Disable the Next button
     */
    function disableNextButton() {
        nextStep.removeClass('border-green-700 text-green-700')
            .addClass('border-gray-225 text-gray-225 opacity-50 cursor-not-allowed')
            .prop("disabled", true);
    }

    /**
     * Update glossary section number based on step
     */
    function updateGlossarySectionNumber(stepNumber) {
        const text = getTranslation('Select or not, one or more glossaries', 'Sélectionner ou non, un ou plusieurs glossaires');
        $('#glossary-section-number').text(`${stepNumber}. ${text}`);
    }

    /**
     * Handle default domain response (when no specific domains available)
     */
    function handleDefaultDomain() {
        $('#subdomain-section').hide().addClass('hidden');
        updateGlossarySectionNumber(2);
        selectedSubDomain = 'Generic domain';
    }

    /**
     * Handle specific domains response
     */
    function handleSpecificDomains(domains) {
        $('#subdomain-section').show().removeClass('hidden');
        updateGlossarySectionNumber(3);
        
        if (domains && domains.length > 0) {
            updateSubDomainsList(domains);
        } else {
            $('.sub-domain-list').empty();
            selectedSubDomain = '';
        }
    }

    // ============= DOMAIN MANAGEMENT =============

    /**
     * Fetch domain groups from API
     */
    const getDomainsGroups = () => {
        $.ajax({
            url: domain_groups,
            type: 'GET',
            headers: getAjaxHeaders(),
            success: function (response) {
                updateDomainsList(response);
            },
            error: handleAjaxError
        });
    };

    /**
     * Fetch domains for selected domain group
     */
    const getDomains = () => {
        $.ajax({
            url: `${get_domains}?domain_group=${selectedDomain}`,
            type: 'GET',
            headers: getAjaxHeaders(),
            success: function (response) {
                defaultDomain = response.default_domain;
                
                if (response.default_domain) {
                    handleDefaultDomain();
                } else {
                    handleSpecificDomains(response.data);
                }
                
                enableNextButton();
            },
            error: handleAjaxError
        });
    };


    // ------------- STEP-TRADUCTION -------------

    // ============= GLOSSARY MANAGEMENT =============

    // Constants for glossary layout (4 items per row with gap-2 = 8px, so 3 gaps = 24px total)
    const GLOSSARY_LAYOUT = {
        ITEMS_PER_ROW: 4,
        GAP_SIZE_PX: 24,
        get flexBasis() {
            return `calc((100% - ${this.GAP_SIZE_PX}px) / ${this.ITEMS_PER_ROW})`;
        }
    };

    // Constants for glossary API requests
    const GLOSSARY_API = {
        PERSONAL_DOMAIN: '*', // Personal glossaries use '*' as domain
        CHECKBOX_NAME: 'glossary-checkbox',
        CHECKBOX_ID_PREFIX: 'glossary-checkbox-'
    };

    // CSS classes constants for glossary items
    const GLOSSARY_CLASSES = {
        checkbox: 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 flex-shrink-0',
        icon: 'ph ph-file mx-2 flex-shrink-0',
        nameSpan: 'font-poppins text-sm font-normal leading-6 tracking-[-0.084px] truncate',
        label: 'ms-2 flex h-8 items-center cursor-pointer min-w-0 flex-1',
        container: 'flex items-center w-full rounded-lg p-2 cursor-pointer transition-colors hover:bg-blue-50 glossary-checkbox-container min-w-0',
        containerSelected: 'bg-blue-50',
        listItem: 'flex items-center min-w-0'
    };

    /**
     * Reset personal glossaries selection
     */
    function resetPersonalGlossariesSelection() {
        selectedPersonalGlossaries = [];
    }

    /**
     * Check if a glossary is currently selected
     * @param {string} glossaryId - Glossary ID to check
     * @returns {boolean} True if glossary is selected
     */
    function isGlossarySelected(glossaryId) {
        return selectedPersonalGlossaries.includes(glossaryId);
    }

    /**
     * Add glossary to selection
     * @param {string} glossaryId - Glossary ID to add
     */
    function addGlossaryToSelection(glossaryId) {
        if (!isGlossarySelected(glossaryId)) {
            selectedPersonalGlossaries.push(glossaryId);
        }
    }

    /**
     * Remove glossary from selection
     * @param {string} glossaryId - Glossary ID to remove
     */
    function removeGlossaryFromSelection(glossaryId) {
        selectedPersonalGlossaries = selectedPersonalGlossaries.filter(id => id !== glossaryId);
    }

    /**
     * Update visual state of glossary container based on selection
     * @param {jQuery} $container - Container element
     * @param {boolean} isSelected - Whether glossary is selected
     */
    function updateGlossaryContainerState($container, isSelected) {
        if (isSelected) {
            $container.addClass(GLOSSARY_CLASSES.containerSelected);
        } else {
            $container.removeClass(GLOSSARY_CLASSES.containerSelected);
        }
    }

    /**
     * Handle glossary checkbox change event
     * @param {HTMLElement} checkbox - Checkbox element that changed
     */
    function handleGlossaryCheckboxChange(checkbox) {
        const $checkbox = $(checkbox);
        const glossaryId = $checkbox.val();
        const $container = $checkbox.closest('.glossary-checkbox-container');
        const isChecked = $checkbox.is(':checked');

        if (isChecked) {
            addGlossaryToSelection(glossaryId);
        } else {
            removeGlossaryFromSelection(glossaryId);
        }

        updateGlossaryContainerState($container, isChecked);
    }

    /**
     * Create glossary checkbox input element
     * @param {string} checkboxId - Unique checkbox ID
     * @param {string} glossaryId - Glossary ID value
     * @param {boolean} isChecked - Whether checkbox should be checked
     * @returns {jQuery} Checkbox element
     */
    function createGlossaryCheckbox(checkboxId, glossaryId, isChecked) {
        const checkbox = $('<input>', {
            id: checkboxId,
            type: 'checkbox',
            name: GLOSSARY_API.CHECKBOX_NAME,
            value: glossaryId,
            class: GLOSSARY_CLASSES.checkbox,
            checked: isChecked
        });
        checkbox.on('change', function() {
            handleGlossaryCheckboxChange(this);
        });
        return checkbox;
    }

    /**
     * Create glossary icon element
     * @returns {jQuery} Icon element
     */
    function createGlossaryIcon() {
        return $('<i>', {
            class: GLOSSARY_CLASSES.icon,
            style: 'font-size: 24px;',
            'aria-hidden': 'true'
        });
    }

    /**
     * Create glossary name span with truncation and tooltip
     * @param {string} glossaryName - Name of the glossary
     * @returns {jQuery} Name span element
     */
    function createGlossaryNameSpan(glossaryName) {
        return $('<span>', {
            class: GLOSSARY_CLASSES.nameSpan,
            text: glossaryName,
            title: glossaryName
        });
    }

    /**
     * Create glossary label with icon and name
     * @param {string} checkboxId - ID of associated checkbox
     * @param {string} glossaryName - Name of the glossary
     * @returns {jQuery} Label element
     */
    function createGlossaryLabel(checkboxId, glossaryName) {
        const label = $('<label>', {
            for: checkboxId,
            class: GLOSSARY_CLASSES.label
        });
        label.append(createGlossaryIcon()).append(createGlossaryNameSpan(glossaryName));
        return label;
    }

    /**
     * Create glossary item container
     * @param {string} glossaryId - Glossary ID
     * @param {jQuery} checkbox - Checkbox element
     * @param {jQuery} label - Label element
     * @param {boolean} isSelected - Whether glossary is selected
     * @returns {jQuery} Container element
     */
    function createGlossaryContainer(glossaryId, checkbox, label, isSelected) {
        const container = $('<div>', {
            class: GLOSSARY_CLASSES.container,
            'data-value': glossaryId
        });
        container.append(checkbox).append(label);
        
        if (isSelected) {
            container.addClass(GLOSSARY_CLASSES.containerSelected);
        }
        
        return container;
    }

    /**
     * Create glossary checkbox item element
     * @param {Object} glossary - Glossary object with id and name
     * @param {number} index - Index for unique ID generation
     * @returns {jQuery} List item element
     */
    /**
     * Create glossary checkbox item element
     * @param {Object} glossary - Glossary object with id and name
     * @param {number} index - Index for unique ID generation
     * @returns {jQuery} List item element
     */
    function createGlossaryCheckboxItem(glossary, index) {
        const checkboxId = `${GLOSSARY_API.CHECKBOX_ID_PREFIX}${index}`;
        const isSelected = isGlossarySelected(glossary.id);

        const checkbox = createGlossaryCheckbox(checkboxId, glossary.id, isSelected);
        const label = createGlossaryLabel(checkboxId, glossary.name);
        const container = createGlossaryContainer(glossary.id, checkbox, label, isSelected);

        const listItem = $('<li>', {
            class: GLOSSARY_CLASSES.listItem,
            style: `flex: 0 0 ${GLOSSARY_LAYOUT.flexBasis};`
        });
        listItem.append(container);

        return listItem;
    }

    /**
     * Display empty glossary message
     * @param {jQuery} container - Container element to display message in
     */
    function displayEmptyGlossaryMessage(container) {
        const message = getTranslation(
            'No personal glossary found. The best glossary prepared by Lexa experts will be used.',
            'Aucun glossaire personnel trouvé. Le meilleur glossaire préparé par les experts Lexa sera utilisé.'
        );
        
        container.html(`
            <div class="flex flex-col items-center justify-center pt-6 pb-0">
                <p class="font-poppins font-normal text-gray-600 text-center" style="font-size: 14px; line-height: 24px;">${message}</p>
            </div>
        `);
    }

    /**
     * Create glossary list container
     * @returns {jQuery} List element
     */
    function createGlossaryList() {
        return $('<ul>', {
            class: 'flex flex-row flex-wrap items-start w-full gap-2'
        });
    }

    /**
     * Render glossary items into list
     * @param {Array} glossaries - Array of glossary objects
     * @param {jQuery} glossaryList - List element to append items to
     */
    function renderGlossaryItems(glossaries, glossaryList) {
        glossaries.forEach((glossary, index) => {
            const listItem = createGlossaryCheckboxItem(glossary, index);
            glossaryList.append(listItem);
        });
    }

    /**
     * Display glossaries list in the glossary content area
     * Note: Does not reset selection to preserve user choices when list is refreshed
     * @param {Array} glossaries - Array of glossary objects to display
     */
    function displayMyGlossariesInStep3(glossaries) {
        const container = $('#glossary-content');
        container.empty();

        if (!glossaries || glossaries.length === 0) {
            displayEmptyGlossaryMessage(container);
            return;
        }

        const glossaryList = createGlossaryList();
        renderGlossaryItems(glossaries, glossaryList);
        container.append(glossaryList);
    }

    /**
     * Load user's personal glossaries from API
     * @param {boolean} shouldReset - Whether to reset selected glossaries (default: true)
     */
    function loadMyGlossaries(shouldReset = true) {
        if (shouldReset) {
            resetPersonalGlossariesSelection();
        }

        $.ajax({
            url: api_lara_glossary_search,
            type: 'POST',
            data: {
                source_language: sourceLanguage,
                target_language: targetLanguage,
                domain: GLOSSARY_API.PERSONAL_DOMAIN
            },
            headers: getAjaxHeaders(),
            success: function (response) {
                displayMyGlossariesInStep3(response);
            },
            error: handleAjaxError
        });
    }


    // ============= GLOSSARY MODAL MANAGEMENT =============

    const $modal = $('#modalGlossary');
    const $closeIcon = $('#closeIcon');
    const maxFileSize = 5 * 1024 * 1024; // 5MB

    /**
     * Reset glossary modal styles to default state
     */
    function resetGlossaryModalStyles() {
        $('#uploadButton').removeClass('bg-transparent border border-red-400 text-red-400').addClass('bg-green-700');
        $('#downloadSample').removeClass('bg-transparent border border-gray-200 text-gray-400').addClass('bg-green-700 text-green-700 border border-green-700');
        $('.glossary-container').removeClass('bg-red-150').addClass('bg-gray-25');
    }

    /**
     * Close glossary modal
     */
    function closeGlossaryModal() {
        resetGlossaryModalStyles();
        $modal.addClass('hidden');
        $closeIcon.addClass('hidden');
        $('input[name=openGlossary]').prop('checked', false).trigger('change');
    }

    /**
     * Open glossary modal
     */
    function openGlossaryModal() {
        $modal.removeClass('hidden');
        $closeIcon.removeClass('hidden');
        $('input[name=openGlossary]').prop('checked', 'checked');
    }

    /**
     * Handle glossary file upload
     */
    function handleGlossaryFileUpload(file) {
        if (!file) return;

        resetGlossaryModalStyles();

        // Sécurité : limiter la longueur du nom de fichier CSV côté front
        var ext = '.' + file.name.split('.').pop().toLowerCase();
        if (ext === '.csv' && file.name.length > MAX_CSV_FILENAME_LENGTH) {
            alert(getTranslation(
                'The CSV filename must not exceed 128 characters.',
                'Le nom du fichier CSV ne doit pas dépasser 128 caractères.'
            ));
            $('.glossary-file').val('');
            glossaryFile = null;
            return;
        }

        if (file.size <= maxFileSize) {
            showUploadedFile(file.name);
        } else {
            alert('File size exceeds 5MB limit.');
            $('.glossary-file').val('');
        }
    }

    // Event handlers
    $(document).on('click', '.openGlossary', function(event) {
        event.preventDefault();
        openGlossaryModal();
    });

    $('#closeModal, #closeIcon').on('click', function () {
        closeGlossaryModal();
    });

    $(window).on('click', function (event) {
        if (event.target == $modal[0]) {
            closeGlossaryModal();
        }
    });

    $('#uploadButton').on('click', function () {
        $('.glossary-file').click();
    });

    $('.glossary-file').on('change', function (e) {
        glossaryFile = e.target.files[0];
        handleGlossaryFileUpload(glossaryFile);
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
            headers: getAjaxHeaders(),
            success: function (response) {
                glossaryFile = null;
                $('#fileInfo').addClass('hidden');
                $('#fileName').text('');
                $('.glossary-file').val('');
                $modal.addClass('hidden');
                $closeIcon.addClass('hidden');

                // Recharger la liste des glossaires pour afficher le nouveau glossaire
                // Preserve existing selections when reloading after creating a new glossary
                if (sourceLanguage && targetLanguage && selectedSubDomain) {
                    loadMyGlossaries(false);
                }
            },
            error: handleAjaxError
        });
    });


    // ------------- STEP-5 -------------


    const fileTranslate = () => {
        // Console log pour afficher le domaine et le glossaire sélectionnés
        console.log('=== INFORMATIONS DE TRADUCTION ===');
        console.log('Domaine sélectionné:', selectedSubDomain);
        console.log('Domaine ID:', selectedSubDomainId);
        console.log('Domaine (anglais):', selectedSubDomainEnglishName);
        console.log('Glossaire sélectionné:', selectedGlossary);
        console.log('Glossaires personnels sélectionnés:', selectedPersonalGlossaries);
        console.log('Langue source:', sourceLanguage);
        console.log('Langue cible:', targetLanguage);
        console.log('================================');

        const formData = new FormData();
        selectedFiles.forEach((file) => {
            formData.append(`document[]`, file.file);
        });

        // Envoyer domain_id pour LARA (le nom anglais est retrouvé via l'ID côté backend)
        formData.append('domain_id', selectedSubDomainId || '');

        // Combine selected glossary and personal glossaries into one glossary parameter
        let glossaries = [];
        if (selectedGlossary && selectedGlossary !== 'none') {
            glossaries.push(selectedGlossary);
        }
        if (selectedPersonalGlossaries && selectedPersonalGlossaries.length > 0) {
            glossaries = glossaries.concat(selectedPersonalGlossaries);
        }
        formData.append('glossary', glossaries.length > 0 ? glossaries.join(',') : 'none');

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
            headers: getAjaxHeaders(),
            success: function (response) {
                if (response && response.project_ids && response.project_ids.length > 0) {
                    startStatusCheck(response.project_ids);
                }
            },
            error: handleAjaxError,
            complete: function () {
                $('#loader-row').addClass('hidden');
            }
        });
    };

    const $modalRevision = $('#modal-revision');
    const $closeRevision = $('#close-revision');

    function formatErrorReasonsForAttr(reasons) {
        if (!reasons) return '';
        if (Array.isArray(reasons)) {
            return reasons.join('\n');
        }
        return String(reasons);
    }

    function applyStatusMetadata($statusNode, status, errorReasons) {
        $statusNode.attr('data-status', status || '');
        const formatted = formatErrorReasonsForAttr(errorReasons);
        if (formatted) {
            $statusNode.attr('data-error-reason', formatted);
        } else {
            $statusNode.removeAttr('data-error-reason');
        }
    }

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
                        <span class="status-badge status-default">
                            <span class="status" data-status="${project.status || ''}">${project.status || ''}</span>
                        </span>
                    </td>
                    <td class="table-actions">
                        <button 
                            class="download-file" 
                            data-translated-file="${project.translated_file}" 
                            data-reviewed-file="${project.reviewed_file || ''}"
                            title="${getTranslation('Download', 'Télécharger')}"
                            ${project.status !== 'Translated' ? 'disabled style="opacity: 0.5; cursor: not-allowed;"' : ''}>
                            <i class="ph ph-download" style="font-size: 16px; color: #374151;"></i>
                        </button>
                        <button 
                            class="expert-revision text-green-600 hover:text-green-700 font-poppins text-sm font-normal underline" 
                            data-translated-file="${project.translated_file}" 
                            data-id="${project.id}"
                            ${project.status !== 'Translated' ? 'disabled style="opacity: 0.5; cursor: not-allowed; text-decoration: none;"' : ''}>
                            ${getTranslation('Expert review', 'Révision d\'un expert')}
                        </button>
                    </td>
                </tr>
            `);

            applyStatusMetadata(documentRow.find('.status'), project.status, project.error_reason);
            documentsContainer.append(documentRow);
        });

        initializeDownloadButtons();
        initializeRevisionButtons();

        if (typeof window.applyStatusMapping === 'function' && documentsContainer.length) {
            window.applyStatusMapping(documentsContainer[0]);
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
                
                // Mettre à jour le badge de statut et réappliquer le mapping partagé
                const statusNode = projectRow.find('td:eq(2) .status');
                const newStatus = 'Sent to post-editing, not accepted yet';
                statusNode.text(newStatus);
                applyStatusMetadata(statusNode, newStatus, null);

                if (typeof window.applyStatusMapping === 'function' && projectRow.length) {
                    window.applyStatusMapping(projectRow[0]);
                }
                
                // Désactiver le bouton de révision
                projectRow.find('.expert-revision').prop('disabled', true).addClass('disabled:pointer-events-none disabled:text-gray-225 disabled:border-gray-225');

                $modalRevision.addClass('hidden');
                $closeRevision.addClass('hidden');
            },
            error: handleAjaxError
        });
    });

    /**
     * Constants for status checking
     */
    const STATUS_CHECK_INTERVAL_MS = 5000;
    const TRANSLATING_STATUS = 'Being translated';

    /**
     * Build URL parameters for project status check
     */
    const buildProjectStatusParams = (projectIds) => {
        const params = new URLSearchParams();
        projectIds.forEach(projectId => {
            params.append('project_id[]', projectId);
        });
        return params;
    };

    /**
     * Check if all projects have finished translation
     */
    const areAllProjectsFinished = (projects) => {
        return projects && projects.length > 0 && 
               projects.every(project => project.status !== TRANSLATING_STATUS);
    };

    /**
     * Handle modal display based on project response
     */
    const handleProjectModalDisplay = (response) => {
        if (!response || response.length === 0) {
            return;
        }
        
        if (response[0].display_popup) {
            $('.show-modal-false').removeClass('hidden');
        } else {
            $('.show-modal-true').removeClass('hidden');
        }
    };

    /**
     * Start polling project status until all translations are complete
     */
    const startStatusCheck = (projectIds) => {
        if (!projectIds || projectIds.length === 0) {
            return;
        }

        let statusCheckInterval = null;
        
        const checkDocumentStatus = () => {
            const params = buildProjectStatusParams(projectIds);
            const url = `${single_project}?${params.toString()}`;

            $.ajax({
                type: 'GET',
                url: url,
                processData: false,
                contentType: false,
                headers: getAjaxHeaders(),
                success: function (response) {
                    handleProjectModalDisplay(response);
                    updateProjectTable(response);
                    
                    if (areAllProjectsFinished(response)) {
                        console.log('Tous les projets sont terminés, arrêt de la boucle de vérification');
                        if (statusCheckInterval) {
                            clearInterval(statusCheckInterval);
                            statusCheckInterval = null;
                        }
                    }
                },
                error: handleAjaxError,
                complete: function () {
                    $('#loader-row').addClass('hidden');
                }
            });
        };

        // Check immediately, then poll at interval
        checkDocumentStatus();
        statusCheckInterval = setInterval(checkDocumentStatus, STATUS_CHECK_INTERVAL_MS);
    };


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


