$(document).ready(function(){
    let tabs = $( "#tabs" );
    let formText = $('#text_translate_form');
    let formFile = $('#file_translate_form');
    let clearBtn = $('.btn_clear');
    let copyBtn = $('.btn_copy');
    let resultBlob;
    let sourceLangSelect = $('[name=source_language]')
    let preloader = $('.modal__wrapper, .preloader');
    let errorPopup = '#error_popup'

    if(tabs.length)
        tabs.tabs();

    function downloadResult() {
        download(resultBlob, $('#file_translate_form input[name=document]').val().replace(/.*(\/|\\)/, ''));
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

    function formTextHandler(e) {
        e.preventDefault();
        let form = $(this);
        let text = form.find('[name="text"]');
        let btn = form.find('[type=submit]');
        let url = form.attr('action')
        let formData = new FormData(form[0]);
        let resultContainer = $('.translate__form__text.result textarea')
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
                preloader.fadeOut(300);
            } else {
                errorHandler();
            }
        })
        .catch(error => errorHandler(error))
    }
    function formFileHandler(e) {
        e.preventDefault();
        let form = $(this);
        let fileInput = form.find('input[type=file]')
        let errorBlock = fileInput.closest('.translate__form__file-block').find('.invalid-feedback');
        if(fileInput[0].files.length) {
            errorBlock.hide();
        } else {
            errorBlock.show()
            return false;
        }
        let btn = form.find('[type=submit]');
        let url = form.attr('action')
        let formData = new FormData(form[0]);


        $('.translate__form__file-block').hide();
        $('.translate__form__file-block.trans-progress').css('display', 'flex')

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
                $('.translate__form__file-block').hide();
                $('.translate__form__file-block.complete').css('display', 'flex')

                resultBlob = obj.body;
                $('#download_result').on('click', downloadResult)
            } else {
                errorHandler();
            }
        })
        .catch(error => errorHandler(error))
    }

    function clearText() {
        let btn = $(this)
        let textarea = btn.closest('.translate__form__text').find('textarea')

        textarea.val('')
    }
    function copyText() {
        let btn = $(this)
        let textarea = btn.closest('.translate__form__text').find('textarea')

        textarea[0].select();
        document.execCommand('copy');
    }

    formText.on('submit', formTextHandler);
    formFile.on('submit', formFileHandler);

    clearBtn.on('click', clearText)
    copyBtn.on('click', copyText)

    sourceLangSelect.on('change', setSourceLang)

    setSourceLang(base_lang_code)
    Upload.init();
});
