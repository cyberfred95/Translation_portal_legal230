

function gpt_processing() {
    let requestProcessAction = gpt_process || '/gpt-processing/gpt_process/'
    let requestProcessMethod = 'POST'
    let requestCheckAction = gpt_process_status_check || '/gpt-processing/gpt_check/'
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
        if(thisInput[0].hasAttribute('accept') && thisInput.attr('accept')) {
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
        let thisExt = thisName[thisName.length-1]
        let checkboxUpload = thisContainer.find('input[type="checkbox"]')

        thisName.pop()

        if(thisName.length > 1) {
            thisName = thisName.join('.')
        } else {
            thisName = thisName[0]
        }

        if(thisName.length > 27)
            thisName = thisName.substring(0, 27) + '... '

        fileName = thisName + '.' + thisExt

        if(fileTypes) {
            $.each(fileTypes, function (_, type) {
                if (type === '.' + thisExt)
                    isValid = true;
            })
        } else {
            isValid = true
        }

        if(!isValid){
            errorBlock.html('<p>Allowed extensions: '+fileTypes.join(', ')+'</p>').show()
            thisInput.val('');
            thisContainer.addClass('is-error')
            if(checkboxUpload.length)
                checkboxUpload.prop('checked', false)
            return false;
        }

        if(files[0].size > maxFileSize){
            isValid = false;
            errorBlock.html('<p>Maximum file size is '+(maxFileSize / 1024 / 1024)+'mb</p>').show()
            thisInput.val('');
            thisContainer.addClass('is-error')
            if(checkboxUpload.length)
                checkboxUpload.prop('checked', false)
            return false;
        }

        function onSuccessValid(resultLines) {
            thisContainer.removeClass('is-error')
            errorBlock.hide();

            resultBlock.text(fileName)
            resultBlock.append(resultBlockImg)
            resultBlock.addClass('uploaded')

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

        if(!thisContainer.length){
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

        if(checkboxUpload.length)
            checkboxUpload.prop('checked', false)

        uploadLabel.find('input').val('')
        uploadLabel.css('display', 'inline-block')
        resultBlock.hide()
        resultBlock.removeClass('uploaded')

        fileData = false;
    }
    function gptTxt(data, onSuccess, onError){
        data = data.replaceAll('\r', '')
        let lines = data.split('\n');

        if(lines.length) {
            onSuccess(lines)
        } else {
            onError()
        }
    }

    function checkAdditional() {
        let thisInp = $(this)
        let thisVal = thisInp.val()
        if(!thisVal)
            return;
        let thisAdditionalBlock = thisInp.closest('.gpt_processing__row').find('[data-action="'+thisVal+'"]')

        $(gptAdditional).hide()
        thisAdditionalBlock.css('display', 'flex').hide().show()
    }

    function isInvalid(selector) {
        $(selector).closest('.translate__form-row').find('.invalid-feedback').show()
        $(selector).closest('.select').find('.errorText').remove()
        $(selector).closest('.modal__btn').addClass('error')
        $(selector).closest('.select').addClass('error')
        $(selector).closest('.select').append('<div class="errorText">This input is required.</div>')
    }
    function isValidF(selector = false) {
        if(!selector || !$(selector).length) {
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

        if(!$(gptUploadTextSwitch).is(':checked')) {
            $(gptBtnDownload).removeClass('is-hidden')


            var a = document.querySelector(gptBtnDownload);

            var file = new Blob([data.join('\n')], {type: 'text/plain'});
            a.href = URL.createObjectURL(file);
            a.download = 'result.txt';
        } else {
            $('#gpt_result_text').text(data.join('\n'))
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
        if($(gptUploadTextSwitch).is(':checked')){
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
        if(!action) {
            isInvalid('[name="'+$(gptInputAction).attr('name')+'"]')
            return;
        } else {
            isValidF('[name="'+$(gptInputAction).attr('name')+'"]')
        }
        let requestData = {
            "action": action,
            "text": fileData
        }
        let additionalBlock = $(gptAdditional + '[data-action="' + action + '"]')
        let additional = {}

        if(additionalBlock.length){
            let additionalInputs = additionalBlock.find('[name]')
            let isValid = true;

            additionalInputs.each(function () {
                let thisInput = $(this)

                additional[thisInput.attr('name')] = thisInput.val()

                if(thisInput.prop('required') && !thisInput.val()){
                    isInvalid('[name="'+thisInput.attr('name')+'"]')
                    isValid = false
                } else {
                    isValidF('[name="'+thisInput.attr('name')+'"]')
                }
            })

            if(!isValid) return;
        }
        if(!fileData)
            return;

        isValidF()
        $(gptBtnSubmit).attr('disabled', 'disabled')
        requestData["prompt"] = additional

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
                let taskId = typeof data['task_id'] !== 'undefined' ? data['task_id'] : false

                if(taskId){
                    let checkInterval = 0;

                    function sendCheckRequest() {
                        fetch(requestCheckAction, {
                            method: requestCheckMethod,
                            credentials: 'same-origin',
                            headers: {
                                'X-Requested-With': 'XMLHttpRequest',
                                'X-CSRFToken': getCookie('csrftoken'),
                                'Accept': 'application/json',
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify([taskId])
                        })
                            .then(function (response) {
                                if(response.ok) {
                                    return response.json()
                                } else {
                                    clearInterval(checkInterval)
                                    return false;
                                }
                            })
                            .then(function (data) {
                                if(data[0]){
                                    if(data[0]['task_status']){
                                        if(data[0]['task_status'] !== 'PENDING') {
                                            clearInterval(checkInterval)

                                            if (data[0]['task_status'] === 'SUCCESS') {
                                                onSuccess(data[0]['result'])
                                            } else {
                                                onError()
                                            }
                                        }
                                    } else {
                                        clearInterval(checkInterval)
                                        onError()
                                    }
                                } else {
                                    clearInterval(checkInterval)
                                    onError()
                                }
                            })
                    }
                    console.log('checking ' + requestCheckAction)
                    checkInterval = setInterval(sendCheckRequest, 1000)
                } else {
                    onError()
                }
            });
    }

    function toggleModalStock() {
        let uploadForm = $('.gpt_processing__upload')
        let textForm = $('.gpt_processing__text')

        if($(gptUploadTextSwitch).is(':checked')){
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
    $(document).on('change', gptUploadTextSwitch, toggleModalStock)

    $(document).on('change', gptUploads, modalUpload)
    $(document).on('click', gptUploadsDelete, modalUploadDelete)

    $(document).on('change', gptInputGenderPronouns, function () {
        $(gptInputGender).val(this.value.split(',')[0])
        $(gptInputPronouns).val(this.value.split(',')[1])
    })
    $(document).on('change', gptInputAction, checkAdditional)
    $(document).on('click', gptBtnSubmit, onSubmit)
    $(document).on('click', gptBtnRetry, onSubmit)
}



$(document).ready(function(){
    let tabs = $( "#tabs" );
    let formText = $('#text_translate_form');
    let formFile = $('#file_translate_form');
    let clearBtn = $('.btn_clear');
    let copyBtn = $('.btn_copy');
    let resetBtn = $('.btn_reset');
    let resultBlob;
    let sourceLangSelect = $('[name=source_language]')
    let preloader = $('.modal__wrapper, .preloader');
    let errorPopup = '#error_popup'
    let successPopup = '#success_modal'

    if(tabs.length)
        tabs.tabs();

    function downloadResult() {
        download(resultBlob, $('#file_translate_form input[name=document]').val().replace(/.*(\/|\\)/, ''));
    }

    function sendDocument(e) {
        e.preventDefault();
        let url = expert_revision_file_url;
        var file = new File([resultBlob], $('#file_translate_form input[name=document]').val().replace(/.*(\/|\\)/, ''));
        let formData = new FormData();
        formData.append('file', file);

        $('.translate__file-block').hide();
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
            success: function() {
                $('.translate__file-block').hide();
                $('.translate__file-block.complete').css('display', 'flex')
                $('#expert_revision_document').addClass('expert--revision');
                successHandler();
            },
            error: function(xhr, status, error) {
                errorHandler(error);
            }
        });
    }

    function setSourceLang(lang){
        let container = $('.translate__pair')
        if($(this).is('select')) {
            lang = $(this).val()
            container = $(this).closest('.translate__pair')
        } else {
            sourceLangSelect.val(lang)
        }
        let targetSelect = container.find('[name="target_language"]')

        setTargetLang(lang, targetSelect)
    }
    function setTargetLang(lang, select){
        select.val('')
        select.find('option:not([value=""])').remove()
        if(!lang) return false;

        let pairs = languages.find(item => item.language === lang).pairs;

        if(!pairs) return false;

        $.each(pairs, function (_, pair) {
            select.append($('<option value="'+pair.language+'">'+pair.name+'</option>'))
        })
    }

    function errorHandler(){
        preloader.hide()
        $('<a href='+errorPopup+'></a>').fancybox({
            arrows : false,
            padding: 0,
            overlay: {
                locked: false
            },
            afterClose: function() {
                location.reload()
            }
        }).click()
    }

    function successHandler(){
        $('<a href='+successPopup+'></a>').fancybox({
            arrows : false,
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
        let resultContainer = $('.translate__form-text.result textarea')
        let errorBlock = form.find('.invalid-feedback');

        if(text.length > parseInt(text.attr('maxlength'))) {
            errorBlock.text('Maximum text length is '+text.attr('maxlength')).show()
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
        .then(r =>  r.json().then(data => ({status: r.status, body: data})))
        .then(obj => {
            if(obj.status === 200) {
                resultContainer.text(obj.body['result']);
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
        let resultData = resultTextArea.val();
        let url = expert_revision_url;

        preloader.fadeIn(300);

        $.ajax({
            type: 'POST',
            url: url,
            data: { result: resultData },
            dataType: 'json',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
                'Accept': 'application/json',
            },
            success: function() {
                $('#expert_revision').addClass('expert--revision');
                preloader.fadeOut(300);
                successHandler();
            },
            error: function(xhr, status, error) {
                errorHandler(error);
            }
        });
    }

    function formFileHandler(e) {
        e.preventDefault();
        let form = $(this);
        let fileInput = form.find('input[type=file]')
        let errorBlock = fileInput.closest('.translate__file-block').find('.invalid-feedback');
        if(fileInput[0].files.length) {
            errorBlock.hide();
        } else {
            errorBlock.show()
            return false;
        }
        let btn = form.find('[type=submit]');
        let url = form.attr('action')
        let formData = new FormData(form[0]);


        $('.translate__file-block').hide();
        $('.translate__file-block.trans-progress').css('display', 'flex')

        btn.hide();


        fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: formData
        })
        .then(r =>  r.blob().then(data => ({status: r.status, body: data})))
        .then(obj => {
            if(obj.status === 200) {
                $('.translate__file-block').hide();
                $('.translate__file-block.complete').css('display', 'flex')

                resultBlob = obj.body;
                $('#download_result').on('click', downloadResult)
                $('#expert_revision_document').on('click', sendDocument)
            } else {
                errorHandler();
            }
        })
        .catch(error => errorHandler(error))
    }
    function formReset(e) {
        e.preventDefault()
        formFile.find('input').val('')
        $('.complete').hide();
        $('.translate__file-block.input').css('display', 'flex')
    }

    function clearText() {
        let btn = $(this)
        let textarea = btn.closest('.translate__form-text').find('textarea')

        textarea.val('')
    }
    function copyText() {
        let btn = $(this)
        let textarea = btn.closest('.translate__form-text').find('textarea')

        textarea[0].select();
        document.execCommand('copy');
    }

    formText.on('submit', formTextHandler);
    formFile.on('submit', formFileHandler);
    resetBtn.on('click', formReset);

    clearBtn.on('click', clearText)
    copyBtn.on('click', copyText)

    sourceLangSelect.on('change', setSourceLang)

    setSourceLang(base_lang_code)
    Upload.init();


    gpt_processing()
});
