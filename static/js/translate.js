function gpt_processing() {
    let requestProcessAction = gpt_process || '/gpt-processing/gpt_process/'
    let requestProcessMethod = 'POST'
    let requestCheckMethod = 'POST'
    let gptBtnDownload = '.gpt_processing__download'
    let gptBtnSubmit = '.gpt_processing__submit'
    let gptBtnRetry = '.gpt_processing__error-restart'
    let gptInputAction = '.gpt_processing input[name="Action"]'
    let gptInputGender = '.gpt_processing [data-action="RewriteForOtherGender"] [name="gender"]'
    let gptInputPronouns = '.gpt_processing [data-action="RewriteForOtherGender"] [name="pronouns"]'
    let gptInputGenderPronouns = '.gpt_processing [data-action="RewriteForOtherGender"] .output_value'
    let gptAdditional = '.gpt_processing__additional'
    let gptError = '.gpt_processing__error'
    let gptUploads = '.gpt_processing__upload input[type="file"]'
    let gptUploadsDelete = '.upload_remove'
    let gptUploadTextSwitch = '.gpt_upload_text_switch'
    let gptTranslationText = '#gpt_translation_text'
    let fileData = false;

    function modalUpload() {
        let thisInput = $(this)
        let fileTypes = false;
        if (thisInput[0].hasAttribute('accept') && thisInput.attr('accept')) {
            fileTypes = thisInput.attr('accept').replaceAll(' ', '').split(',')
        }
        let maxFileSize = parseFloat(thisInput.attr('data-maxsize')) * 1024 * 1024;
        let isValid = false;
        let files = this.files;
        let thisContainer = thisInput.closest('.modal__btn')
        let errorBlock = thisContainer.find('.modal__btn-text--error')
        let uploadLabel = thisContainer.find('.upload_label')
        let resultBlock = thisContainer.find('.upload_result')
        let resultBlockImg = thisContainer.find('.upload_result img')
        let fileName = ''
        let thisName = files[0].name.split('.')
        let thisExt = thisName[thisName.length - 1]
        let checkboxUpload = thisContainer.find('input[type="checkbox"]')
        console.log('files', files)
        thisName.pop()

        if (thisName.length > 1) {
            thisName = thisName.join('.')
        } else {
            thisName = thisName[0]
        }

        if (thisName.length > 27)
            thisName = thisName.substring(0, 27) + '... '

        fileName = thisName + '.' + thisExt

        if (fileTypes) {
            $.each(fileTypes, function (_, type) {
                if (type === '.' + thisExt)
                    isValid = true;
            })
        } else {
            isValid = true
        }

        if (!isValid) {
            errorBlock.html('<p>Allowed extensions: ' + fileTypes.join(', ') + '</p>').show()
            thisInput.val('');
            thisContainer.addClass('is-error')
            if (checkboxUpload.length)
                checkboxUpload.prop('checked', false)
            return false;
        }

        if (files[0].size > maxFileSize) {
            isValid = false;
            errorBlock.html('<p>Maximum file size is ' + (maxFileSize / 1024 / 1024) + 'mb</p>').show()
            thisInput.val('');
            thisContainer.addClass('is-error')
            if (checkboxUpload.length)
                checkboxUpload.prop('checked', false)
            return false;
        }

        function onSuccessValid(resultLines) {
            thisContainer.removeClass('is-error')
            errorBlock.hide();

            resultBlock.text(fileName)
            resultBlock.append(resultBlockImg)
            // resultBlock.addClass('uploaded')

            uploadLabel.hide()
            resultBlock.css('display', 'inline-block')

            fileData = resultLines
        }

        function onErrorValid() {
            isValid = false;
            errorBlock.html('<p>Your file is empty</p>').show()
            thisInput.val('');
            thisContainer.addClass('is-error')
            fileData = false;
        }


        let reader = new FileReader();
        reader.addEventListener('load', function (e) {
            let txtData = e.target.result;
            gptTxt(txtData, onSuccessValid, onErrorValid);
        });
        reader.readAsText(files[0]);
    }

    function modalUploadDelete() {
        let thisInput = $(this)
        let thisContainer = thisInput.closest('.modal__btn')
        let thisIndex = false;

        if (!thisContainer.length) {
            thisContainer = thisInput.closest('.upload_result')
            thisIndex = thisContainer.index()
            thisContainer.remove()
            // if(!uploadBtns.find('.upload_result').length){
            //     uploadBtns.find('.btn').removeClass('btn--darkgray').text('Upload files')
            // }
            thisInput = $(gptUploads).eq(thisIndex)
            thisContainer = thisInput.closest('.modal__btn')
        }
        let uploadLabel = thisContainer.find('.upload_label')
        let resultBlock = thisContainer.find('.upload_result')
        let checkboxUpload = thisContainer.find('input[type="checkbox"]')

        if (checkboxUpload.length)
            checkboxUpload.prop('checked', false)

        uploadLabel.find('input').val('')
        uploadLabel.css('display', 'inline-block')
        resultBlock.hide()
        resultBlock.removeClass('uploaded')

        fileData = false;
    }

    function gptTxt(data, onSuccess, onError) {
        data = data.replaceAll('\r', '')
        let lines = data.split('\n');

        if (lines.length) {
            onSuccess(lines)
        } else {
            onError()
        }
    }

    function checkAdditional() {
        let thisInp = $(this)
        let thisVal = thisInp.val()
        if (!thisVal)
            return;
        let thisAdditionalBlock = thisInp.closest('.gpt_processing__row').find('[data-action="' + thisVal + '"]')

        $(gptAdditional).hide()
        thisAdditionalBlock.css('display', 'flex').hide().show()
    }

    function isInvalid(selector) {
        $(selector).closest('.translate__form-row').find('.invalid-feedback').show()
        $(selector).closest('.modal__btn').addClass('error')
        $(selector).closest('.select').addClass('error')
        $(selector).closest('.select').find('.errorText').show();
    }

    function isValidF(selector = false) {
        if (!selector || !$(selector).length) {
            $('.error').removeClass('error')
            $('.invalid-feedback').hide()
        } else {
            $(selector).closest('.translate__form-row').find('.invalid-feedback').hide()
            $(selector).closest('.modal__btn').removeClass('error')
            $(selector).closest('.select').removeClass('error')
        }
    }

    function onSuccess(data) {
        $(gptError).addClass('is-hidden')

        if (!$(gptUploadTextSwitch).is(':checked')) {
            $(gptBtnDownload).removeClass('is-hidden')
            var a = document.querySelector(gptBtnDownload);

            var file = new Blob([data.join('\n')], {type: 'text/plain'});
            a.href = URL.createObjectURL(file);
            a.download = 'result.txt';
        } else {
            $(gptBtnSubmit).removeAttr('disabled', 'disabled')
            $('#gpt_result_text').val(data);
        }
    }

    function onError() {
        $(gptError).removeClass('is-hidden')
        $(gptBtnSubmit).removeClass('is-hidden')

        $(gptBtnDownload).addClass('is-hidden')
    }

    function onSubmit(e) {
        e.preventDefault()
        let action = $(gptInputAction).val()
        if ($(gptUploadTextSwitch).is(':checked')) {
            fileData = $(gptTranslationText).val().split('\n')
            if (!fileData) {
                isInvalid(gptTranslationText)
            } else {
                isValidF(gptTranslationText)
            }
        } else {
            if (!fileData) {
                isInvalid(gptUploads)
            }
        }
        if (!action) {
            isInvalid('[name="' + $(gptInputAction).attr('name') + '"]')
            return;
        } else {
            isValidF('[name="' + $(gptInputAction).attr('name') + '"]')
        }
        let requestData = {
            "prompt": action,
            "text": fileData
        }
        let additionalBlock = $(gptAdditional + '[data-action="' + action + '"]')
        let additional = {}

        if (additionalBlock.length) {
            let additionalInputs = additionalBlock.find('[name]')
            let isValid = true;

            additionalInputs.each(function () {
                let thisInput = $(this)

                additional[thisInput.attr('name')] = thisInput.val()

                if (thisInput.prop('required') && !thisInput.val()) {
                    isInvalid('[name="' + thisInput.attr('name') + '"]')
                    isValid = false
                } else {
                    isValidF('[name="' + thisInput.attr('name') + '"]')
                }
            })

            if (!isValid) return;
        }
        if (!fileData)
            return;

        isValidF()
        $(gptBtnSubmit).attr('disabled', 'disabled')

        console.log('creating ' + requestProcessAction)
        fetch(requestProcessAction, {
            method: requestProcessMethod,
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
            .then(response => response.json())
            .then(function (data) {
                onSuccess(data.result);
            }).catch(() => {
            onError();
        })
    }

    function toggleModalStock() {
        let uploadForm = $('.gpt_processing__upload')
        let textForm = $('.gpt_processing__text')

        if ($(gptUploadTextSwitch).is(':checked')) {
            uploadForm.fadeOut(300, function () {
                textForm.fadeIn(300)
            })
        } else {
            textForm.fadeOut(300, function () {
                uploadForm.fadeIn(300)
            })
        }
    }

    toggleModalStock()
    toggleModalStock()
    $(document).on('change', gptUploadTextSwitch, toggleModalStock)

    $(document).on('change', gptUploads, modalUpload)
    $(document).on('click', gptUploadsDelete, modalUploadDelete)

    $(document).on('change', gptInputGenderPronouns, function () {
        $(gptInputGender).val(this.value.split(',')[0])
        $(gptInputPronouns).val(this.value.split(',')[1])
    })
    $(document).on('change', gptInputAction, checkAdditional)
    $(document).on('click', gptBtnSubmit, onSubmit)
    $(document).on('click', gptBtnRetry, function () {
        $(gptInputAction).val('')
        $(gptTranslationText).val('')
        $(gptBtnSubmit).removeAttr('disabled', 'disabled')
        $(gptError).addClass('is-hidden')
        $(".output_text").val('');
    });
}


$(document).ready(function () {
    let tabs = $("#tabs");
    let formText = $('#text_translate_form');
    let formFile = $('#file_translate_form');
    let clearBtn = $('.btn_clear');
    let copyBtn = $('.btn_copy');
    let resetBtn = $('.btn_reset');
    let preloader = $('.modal__wrapper, .preloader');
    let errorPopup = '#error_popup'
    let successPopup = '#success_modal'
    var swapTextIcon = document.querySelector('.swap__language-ico');
    var swapDocIcon = document.querySelector('.translate__tab#tabs-2 .swap__language-ico.document');


    if (tabs.length) {
        var tabIndex = 0; // Default tab index (first tab)
        var hash = window.location.hash;

        // Check if URL hash matches any of the tab's anchors
        tabs.find("a").each(function (index) {
            if ("#" + this.getAttribute("href").split("#")[1] === hash) {
                tabIndex = index;
            }
        });

        // Tabs with  determined active index
        tabs.tabs({active: tabIndex});

        // Add a handler for the beforeActivate event
        tabs.tabs({
            activate: function (event, ui) {
                var currentHash = ui.newPanel.attr('id');
                window.location.hash = currentHash;
            },
            beforeActivate: function (event, ui) {
                // Check if the tab has 'no-tab' class
                if (ui.newTab.children("a").hasClass("no-tab")) {
                    event.preventDefault();
                    window.location.href = ui.newTab.children("a").attr("href");
                }
            }
        });

        var hash = window.location.hash;
        if (hash) {
            $('#tabs').tabs('load', hash);
        }
    }

    $(".header__lang li a").click(function (event) {
        event.preventDefault();

        var languageCode = $(this).text().trim().toLowerCase();

        var currentUrl = window.location.href;

        if (languageCode === "en") {
            currentUrl = currentUrl.replace("/fr/", "/en/");
        } else if (languageCode === "fr") {
            currentUrl = currentUrl.replace("/en/", "/fr/");
        }

        $(".header__lang li a").each(function () {
            var href = $(this).attr("href");
            var newHref = href.replace("/en/", "/fr/").replace("/fr/", "/en/");
            $(this).attr("href", newHref);
        });

        window.location.href = currentUrl;
    });

    function sendDocument(file, id) {
        let url = expert_revision_file_url;
        let formData = new FormData();
        formData.append('file_url', file);
        formData.append('project_id', id);

        $('.translate__file-block').hide();
        $('.output-type').hide();
        $('.translate__file-block.trans-progress').css('display', 'flex')

        $.ajax({
            type: 'POST',
            url: url,
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
                $('.translate__file-block').hide();
                $('.output-type').hide();
                $('.translate__file-block.complete').css('display', 'flex')
                $('#expert_revision_document').addClass('expert--revision');
                successHandler();
            },
            error: function (xhr, status, error) {
                errorHandler(error);
            }
        });
    }

    function errorHandler() {
        preloader.hide()
        $('<a href=' + errorPopup + '></a>').fancybox({
            arrows: false,
            padding: 0,
            overlay: {
                locked: false
            },
            afterClose: function () {
                location.reload()
            }
        }).click()
    }

    function successHandler() {
        $('<a href=' + successPopup + '></a>').fancybox({
            arrows: false,
            padding: 0,
            overlay: {
                locked: false
            },
        }).click()
    }

    function formTextHandler(e) {
        e.preventDefault();
        let form = $(this);
        let text = form.find('[name="text"]');

        let btn = form.find('[type=submit]');
        let url = form.attr('action')
        let formData = new FormData(form[0]);
        let resultContainer = $('#result_text');
        let errorBlock = form.find('.invalid-feedback');

        if (text.length > parseInt(text.attr('maxlength'))) {
            errorBlock.text('Maximum text length is ' + text.attr('maxlength')).show()
            return false;
        } else {
            errorBlock.hide()
        }

        btn.attr('disabled', true);
        preloader.fadeIn(300);

        fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: formData,
        })
            .then(r => r.json().then(data => ({status: r.status, body: data})))
            .then(obj => {
                if (obj.status === 200) {
                    resultContainer.val(obj.body['translated_text']);
                    btn.attr('disabled', false);
                    $('#expert_revision').removeClass('expert--revision');
                    preloader.fadeOut(300);
                } else {
                    errorHandler();
                }
            })
            .catch(error => errorHandler(error))
    }

    $('#expert_revision').on('click', expertRevision);

    function expertRevision(e) {
        e.preventDefault();

        let resultTextArea = $('#result_text');
        let sourceTextArea = $('#translation_text');
        let resultData = resultTextArea.val();
        let sourceData = sourceTextArea.val();
        let url = expert_revision_url;

        preloader.fadeIn(300);

        $.ajax({
            type: 'POST',
            url: url,
            data: {result: resultData, source_text: sourceData},
            dataType: 'json',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
                'Accept': 'application/json',
            },
            success: function () {
                $('#expert_revision').addClass('expert--revision');
                preloader.fadeOut(300);
                successHandler();
            },
            error: function (xhr, status, error) {
                errorHandler(error);
            }
        });
    }

    function downloadResult(url) {
        if (url) {
            var a = document.createElement('A');
            a.href = url;
            a.download = url.substr(url.lastIndexOf('/') + 1);
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }
    }

    function checkDocument(fileIds, intervalId, isPostEditing) {
        let params = new URLSearchParams();

        fileIds.forEach(fileId => {
            params.append('project_id[]', fileId);
        });

        let url = '/project/?' + params.toString();
        $('.translate__file-block').hide();
        $('.output-type').hide();
        $('.translate__file-block.trans-progress').css('display', 'flex')

        $.ajax({
            type: 'GET',
            url: url,
            processData: false,
            contentType: false,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            success: function (response) {
                console.log('response', response);

                let allTranslated = response.every(project => project.status === 'Translated');

                if (allTranslated && !isPostEditing) {
                    clearInterval(intervalId);
                    $('.translate__file-block').hide();
                    $('.output-type').hide();
                    let completeBlock = $('.translate__file-block.complete');
                    completeBlock.css('display', 'flex');

                    completeBlock.find('.download-buttons').remove();

                    let downloadButtonsContainer = $('<div class="download-buttons"></div>');

                    response.forEach((project) => {
                        let buttonSet = $(`
                <div class="button-set">
                    <button type="button" class="button button--secondary button--transparent button--ico download-result" data-file="${project.translated_file}">
                        <svg width="16" height="17" viewBox="0 0 16 17" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <g clip-path="url(#clip0_2624_14289)">
                                <path d="M15.2188 7.71875C14.7875 7.71875 14.4375 8.06875 14.4375 8.5C14.4375 12.05 11.55 14.9375 8 14.9375C4.45 14.9375 1.5625 12.05 1.5625 8.5C1.5625 8.06875 1.2125 7.71875 0.78125 7.71875C0.35 7.71875 0 8.06875 0 8.5C0 10.6375 0.83125 12.6469 2.34375 14.1562C3.85625 15.6687 5.8625 16.5 8 16.5C10.1375 16.5 12.1469 15.6687 13.6562 14.1562C15.1687 12.6438 16 10.6375 16 8.5C16 8.06875 15.65 7.71875 15.2188 7.71875Z" fill="#292929"/>
                                <path d="M6.92793 11.2375C7.21543 11.525 7.59668 11.6812 7.9998 11.6812C8.40605 11.6812 8.7873 11.5219 9.07168 11.2375L11.0373 9.27187C11.3436 8.96562 11.3436 8.47187 11.0373 8.16562C10.7311 7.85937 10.2373 7.85937 9.93105 8.16562L8.78105 9.31875V1.28125C8.78105 0.85 8.43105 0.5 7.9998 0.5C7.56855 0.5 7.21855 0.85 7.21855 1.28125V9.31875L6.06543 8.16562C5.75918 7.85937 5.26543 7.85937 4.95918 8.16562C4.65293 8.47187 4.65293 8.96562 4.95918 9.27187L6.92793 11.2375Z" fill="#292929"/>
                            </g>
                            <defs>
                                <clipPath id="clip0_2624_14289">
                                    <rect width="16" height="16" fill="white" transform="translate(0 0.5)"/>
                                </clipPath>
                            </defs>
                        </svg>
                        <span>Download ${project.name}</span>
                    </button>
                    <button type="button" class="button button--secondary button--transparent button--ico export--revision--download expert-revision" data-id="${project.id}">
                        <span>Expert Revision</span>
                        <span class="revision-icon">
                            <svg width="16" height="17" viewBox="0 0 16 17" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <g clip-path="url(#clip0_2704_437)">
                                    <path d="M8 0.5C6.41775 0.5 4.87104 0.969192 3.55544 1.84824C2.23985 2.72729 1.21447 3.97672 0.608967 5.43853C0.00346629 6.90034 -0.15496 8.50887 0.153721 10.0607C0.462403 11.6126 1.22433 13.038 2.34315 14.1569C3.46197 15.2757 4.88743 16.0376 6.43928 16.3463C7.99113 16.655 9.59966 16.4965 11.0615 15.891C12.5233 15.2855 13.7727 14.2602 14.6518 12.9446C15.5308 11.629 16 10.0823 16 8.5C15.9977 6.37897 15.1541 4.34547 13.6543 2.84568C12.1545 1.34589 10.121 0.502294 8 0.5ZM8 15.1667C6.68146 15.1667 5.39253 14.7757 4.2962 14.0431C3.19987 13.3106 2.34539 12.2694 1.84081 11.0512C1.33622 9.83305 1.2042 8.49261 1.46144 7.1994C1.71867 5.90619 2.35361 4.71831 3.28596 3.78596C4.21831 2.85361 5.4062 2.21867 6.6994 1.96143C7.99261 1.7042 9.33305 1.83622 10.5512 2.3408C11.7694 2.84539 12.8106 3.69987 13.5431 4.7962C14.2757 5.89253 14.6667 7.18146 14.6667 8.5C14.6647 10.2675 13.9617 11.9621 12.7119 13.2119C11.4621 14.4617 9.76752 15.1647 8 15.1667Z" fill="#292929"/>
                                    <path d="M8.47816 3.87534C8.09372 3.8053 7.69857 3.8206 7.32069 3.92017C6.94281 4.01974 6.59144 4.20115 6.29143 4.45155C5.99142 4.70195 5.7501 5.01522 5.58457 5.36921C5.41903 5.72319 5.33332 6.10923 5.3335 6.50001C5.3335 6.67682 5.40373 6.84639 5.52876 6.97142C5.65378 7.09644 5.82335 7.16668 6.00016 7.16668C6.17697 7.16668 6.34654 7.09644 6.47157 6.97142C6.59659 6.84639 6.66683 6.67682 6.66683 6.50001C6.66666 6.30386 6.70977 6.11009 6.79309 5.93252C6.87641 5.75494 6.99788 5.59794 7.14884 5.4727C7.2998 5.34746 7.47654 5.25707 7.66645 5.20797C7.85635 5.15888 8.05475 5.15229 8.2475 5.18868C8.51086 5.2398 8.753 5.36827 8.943 5.55767C9.13299 5.74707 9.26222 5.98881 9.31416 6.25201C9.36663 6.52828 9.3304 6.81406 9.21067 7.0685C9.09093 7.32294 8.89381 7.53301 8.6475 7.66868C8.23961 7.90499 7.90255 8.24635 7.67145 8.65721C7.44034 9.06807 7.32364 9.53338 7.3335 10.0047V10.5C7.3335 10.6768 7.40373 10.8464 7.52876 10.9714C7.65378 11.0964 7.82335 11.1667 8.00016 11.1667C8.17697 11.1667 8.34654 11.0964 8.47157 10.9714C8.59659 10.8464 8.66683 10.6768 8.66683 10.5V10.0047C8.65846 9.77269 8.71137 9.54258 8.82021 9.33754C8.92905 9.13249 9.08999 8.95974 9.28683 8.83668C9.76984 8.57139 10.1588 8.16298 10.4002 7.66761C10.6416 7.17225 10.7237 6.61425 10.635 6.07036C10.5464 5.52647 10.2914 5.0234 9.90516 4.63034C9.51893 4.23728 9.02041 3.97352 8.47816 3.87534Z" fill="#292929"/>
                                    <path d="M8.66683 12.5C8.66683 12.1319 8.36835 11.8334 8.00016 11.8334C7.63197 11.8334 7.3335 12.1319 7.3335 12.5C7.3335 12.8682 7.63197 13.1667 8.00016 13.1667C8.36835 13.1667 8.66683 12.8682 8.66683 12.5Z" fill="#292929"/>
                                </g>
                                <defs>
                                    <clipPath id="clip0_2704_437">
                                        <rect width="16" height="16" fill="white" transform="translate(0 0.5)"/>
                                    </clipPath>
                                </defs>
                            </svg>
                            <span class="tooltiptext">Expert revision</span>
                        </span>
                    </button>
                </div>
            `);
                        downloadButtonsContainer.append(buttonSet);
                    });

                    completeBlock.find('.translate__file-ico').append(downloadButtonsContainer);

                    $('.download-result').on('click', function() {
                        downloadResult($(this).data('file'));
                    });

                    $('.expert-revision').on('click', function() {
                        let projectId = $(this).data('id');
                        let project = response.find(p => p.id === projectId);
                        sendDocument(project.translated_file, projectId);
                    });

                } else if (response.some(project => project.status === 'Error')) {
                    errorHandler();
                }
            },
            error: function (xhr, status, error) {
                errorHandler(error);
            }
        });
    }

    function formFileHandler(e) {
        e.preventDefault();
        let form = $(this);
        let fileInput = form.find('input[type=file]')
        let errorBlock = fileInput.closest('.translate__file-block').find('.invalid-feedback');
        if (fileInput[0].files.length) {
            errorBlock.hide();
        } else {
            errorBlock.show()
            return false;
        }
        let url = form.attr('action')
        let formData = new FormData();

        for (let i = 0; i < fileInput[0].files.length; i++) {
            formData.append('document[]', fileInput[0].files[i]);
        }

        let otherInputs = form.find('input:not([type=file]), select, textarea');
        otherInputs.each(function () {
            formData.append(this.name, this.value);
        });

        $('.translate__file-block').hide();
        $('.output-type').hide();
        $('.translate__file-block.trans-progress').css('display', 'flex')

        $('.translate__form-submit').eq(1).hide();

        fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: formData
        })
            .then(r => r.json().then(data => ({status: r.status, body: data})))
            .then(obj => {
                if (obj.status === 200) {
                    console.log('obj.body', obj.body.data)
                    let intervalId = setInterval(() => {
                        checkDocument(obj.body.data, intervalId);
                    }, 10000);
                    checkDocument(obj.body.data, intervalId);
                } else {
                    errorHandler();
                }
            })
            .catch(error => errorHandler(error))
    }

    function formReset(e) {
        e.preventDefault();

        let form = $(this);
        let btn = form.find('[type=submit]');
        $('#document').val(null);

        btn.show();

        $('.translate__file-block.input').css('display', 'flex');
        $('.translate__file-block.complete').css('display', 'none');
        $('#expert_revision_document').removeClass('expert--revision');
    }

    function clearText() {
        let btn = $(this)
        let textarea = btn.closest('.translate__form-text').find('textarea');
        let textareaResult = $('#result_text');

        textarea.val('');
        textareaResult.val('');
    }

    function copyText() {
        let btn = $(this)
        let textarea = btn.closest('.translate__form-text').find('textarea')

        textarea[0].select();
        document.execCommand('copy');
    }

    function swapLanguages() {
        var textSourceLangText = document.querySelector('#tabs-1 .output_text.source');
        var textSourceLangValue = document.querySelector('#tabs-1 input[name="source_language"]');
        var textTargetLangText = document.querySelector('#tabs-1 .output_text.target');
        var textTargetLangValue = document.querySelector('#tabs-1 input[name="target_language"]');

        var docSourceLangText = document.querySelector('#tabs-2 .output_text.source');
        var docSourceLangValue = document.querySelector('#tabs-2 input[name="source_language"]');
        var docTargetLangText = document.querySelector('#tabs-2 .output_text.target');
        var docTargetLangValue = document.querySelector('#tabs-2 input[name="target_language"]');

        var inputText = document.querySelector('#translation_text');
        var resultText = document.querySelector('#result_text');

        [textSourceLangText.value, textTargetLangText.value] = [textTargetLangText.value, textSourceLangText.value];
        [textSourceLangValue.value, textTargetLangValue.value] = [textTargetLangValue.value, textSourceLangValue.value];

        [docSourceLangText.value, docTargetLangText.value] = [docTargetLangText.value, docSourceLangText.value];
        [docSourceLangValue.value, docTargetLangValue.value] = [docTargetLangValue.value, docSourceLangValue.value];

        var tempText = inputText.value;
        inputText.value = resultText.value;
        resultText.value = tempText;

        var textSourceLang = textSourceLangValue.value.toLowerCase();
        var textTargetLang = textTargetLangValue.value.toLowerCase();

        if (textTargetLang && textSourceLang) {
            getTemplates(textSourceLang, textTargetLang);
        }

        var docSourceLang = docSourceLangValue.value.toLowerCase();
        var docTargetLang = docTargetLangValue.value.toLowerCase();

        if (docSourceLang && docTargetLang) {
            getTemplates(docSourceLang, docTargetLang);
        }
    }

    document.querySelectorAll(".select-box").forEach(function (box) {
        box.addEventListener("click", function (event) {
            if (event.target.classList.contains('option')) {
                const selectedText = box.querySelector(".selected-text");
                const hiddenInput = box.closest('form').querySelector("input[name='translation_name']");
                const optionsContainer = box.querySelector(".options-container");

                selectedText.textContent = event.target.textContent;
                hiddenInput.value = event.target.getAttribute("value");

                optionsContainer.classList.remove("active");
            }
        });

        const selected = box.querySelector(".selected");
        const optionsContainer = box.querySelector(".options-container");

        selected.addEventListener("click", function () {
            document.querySelectorAll(".select-box .options-container.active").forEach(function (openContainer) {
                if (openContainer !== optionsContainer) {
                    openContainer.classList.remove("active");
                }
            });
            optionsContainer.classList.toggle("active");
        });
    });


    function getTemplates(sourceLanguage, targetLanguage) {
        let url
        const algorithm = translation_algorithm === 'domain';

        if (algorithm) {
            url = `get-domains?source_language=${sourceLanguage}&target_language=${targetLanguage}`;
        } else {
            url = `get-templates?source_language=${sourceLanguage}&target_language=${targetLanguage}`;
        }


        $.ajax({
            type: 'GET',
            url: url,
            processData: false,
            contentType: false,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            success: function (response) {
                console.log('templates', response)
                $('.translate__tab').each(function () {
                    const tab = $(this);
                    const optionsContainer = tab.find('.output_value[name="translation_name"]').siblings('.select__dropdown').find('ul');
                    optionsContainer.empty();

                    let result = [];

                    if (algorithm) {
                        result = response.data;
                    } else {
                        result = response.data;
                    }

                    result.forEach((i, index) => {
                        const option = $('<li></li>');
                        option.addClass('option');
                        option.attr('data-value', i);
                        option.text(i);

                        if (index === 0) {
                            option.addClass('selected');
                            tab.find('.output_value[name="translation_name"]').val(i);
                            tab.find('.output_text.template').val(i);
                        }

                        optionsContainer.append(option);
                    })
                });

            },
            error: function (xhr, status, error) {
                errorHandler(error);
            }
        });
    }

    $(document).on('change', '[name="source_language"], [name="target_language"]', function () {
        const sourceLanguage = $(this).closest('.translate__tab').find('.output_value[name="source_language"]').val().toLowerCase();
        const sourceLanguageText = $(this).closest('.translate__tab').find('.output_text.source').val();
        const targetLanguage = $(this).closest('.translate__tab').find('.output_value[name="target_language"]').val().toLowerCase();
        const targetLanguageText = $(this).closest('.translate__tab').find('.output_text.target').val();

        const tabIndex = $(this).closest('.translate__tab').attr('id').split('-')[1];

        const oppositeTabIndex = tabIndex === '1' ? '2' : '1';

        const oppositeSourceLanguageInput = $('#tabs-' + oppositeTabIndex + ' .output_value[name="source_language"]');
        const oppositeSourceLanguageText = $('#tabs-' + oppositeTabIndex + ' .output_text.source');
        const oppositeTargetLanguageInput = $('#tabs-' + oppositeTabIndex + ' .output_value[name="target_language"]');
        const oppositeTargetLanguageText = $('#tabs-' + oppositeTabIndex + ' .output_text.target');

        oppositeSourceLanguageInput.val(sourceLanguage);
        oppositeTargetLanguageInput.val(targetLanguage);
        oppositeSourceLanguageText.val(sourceLanguageText);
        oppositeTargetLanguageText.val(targetLanguageText);

        if (targetLanguage && sourceLanguage) {
            getTemplates(sourceLanguage, targetLanguage);
        }
    });

    const inputs = document.querySelectorAll('.select.translation > input.output_text');
    const submitButton = document.querySelector('.translate__form-submit > button[type="submit"]');
    const submitDocumentButton = document.querySelector('.translate__form-submit.uploaded > button[type="submit"]');

    function validateForm() {
        inputs.forEach(input => {
            if (input.value.trim() === '') {
                input.classList.add('required');
            } else {
                input.classList.remove('required');
            }
        });
    }

    submitButton.addEventListener('click', validateForm);
    submitDocumentButton.addEventListener('click', validateForm);

    swapTextIcon.addEventListener('click', swapLanguages);
    swapDocIcon.addEventListener('click', swapLanguages);

    formText.on('submit', formTextHandler);
    formFile.on('submit', formFileHandler);
    resetBtn.on('click', formReset);

    clearBtn.on('click', clearText)
    copyBtn.on('click', copyText)

    Upload.init();

    gpt_processing()
});
