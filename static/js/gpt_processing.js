
function gpt_processing() {
    let requestProcessAction = '/gpt-processing/gpt_process/'
    let requestProcessMethod = 'POST'
    let requestCheckAction = '/gpt-processing/gpt_check/'
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
        $(selector).closest('.select').find('.errorText').remove()
        $(selector).closest('.modal__btn').addClass('error')
        $(selector).closest('.select').addClass('error')
        $(selector).closest('.select').append('<div class="errorText">This input is required.</div>')
    }
    function isValidF(selector = false) {
        if(!selector || !$(selector).length) {
            $('.error').removeClass('error')
        } else {
            $(selector).closest('.modal__btn').removeClass('error')
            $(selector).closest('.select').removeClass('error')
        }
    }

    function onSuccess(data) {
        $(gptError).addClass('is-hidden')
        $(gptBtnSubmit).addClass('is-hidden')

        $(gptBtnDownload).removeClass('is-hidden')


        var a = document.querySelector(gptBtnDownload);

        var file = new Blob([data.join('\n')], {type: 'text/plain'});
        a.href = URL.createObjectURL(file);
        a.download = 'result.txt';
    }
    function onError() {
        $(gptError).removeClass('is-hidden')
        $(gptBtnSubmit).removeClass('is-hidden')

        $(gptBtnDownload).addClass('is-hidden')
    }
    function onSubmit(e) {
        e.preventDefault()
        let action = $(gptInputAction).val()
        if(!fileData) {
            isInvalid(gptUploads)
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
                    .then(response => response.json())
                    .then(function (data) {
                        if(data[0]){
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
                        }
                    })
                }

                checkInterval = setInterval(sendCheckRequest, 1000)
            } else {
                onError()
            }
        });
    }

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


$(document).ready(function() {
    selects()
    gpt_processing()
});