var Upload = {
    init: function() {
        let thisContainer = $("#upload");

        thisContainer.on('drag dragstart dragend dragover dragenter dragleave drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
        })
            .on('dragover dragenter', function() { thisContainer.addClass('is-dragover'); })
            .on('dragleave dragend drop', function() { thisContainer.removeClass('is-dragover'); })
            .on('drop', validateFiles);

        $(document).on('click', '.upload-remove', function () {
            let fileItem = $(this).closest('.translate__file-review');
            let fileName = fileItem.find('.output-name').text();
            removeFile(fileName);
            fileItem.remove();
            if ($('.file-list .translate__file-review').length === 0) {
                resetUpload();
            }
        });

        function validateFiles(e, inp){
            let thisInput = thisContainer.find('input')
            let fileTypes = false;
            if(thisInput[0].hasAttribute('accept') && thisInput.attr('accept')) {
                fileTypes = thisInput.attr('accept').replaceAll(' ', '').split(',')
            }
            let maxFileSize = parseInt(thisInput.attr('data-maxsize')) * 1024 * 1024;
            let isValid = true;
            let files = e ? e.originalEvent.dataTransfer.files : inp.files;
            let errorBlock = thisInput.closest('.input').find('.invalid-feedback')

            // Очищаємо попередній список файлів
            $('.file-list').empty();

            // Перевіряємо кожен файл
            for (let i = 0; i < files.length; i++) {
                let file = files[i];
                let fileName = file.name;
                let isFileValid = true;

                if (fileTypes) {
                    isFileValid = fileTypes.some(type => file.type.indexOf(type) !== -1);
                }

                if (!isFileValid) {
                    errorBlock.html('Дозволені розширення: ' + fileTypes.join(', '))
                    isValid = false;
                } else if (file.size > maxFileSize) {
                    errorBlock.html('Максимальний розмір файлу ' + (maxFileSize / 1024 / 1024) + 'mb')
                    isValid = false;
                } else {
                    $('.file-list').append(`
                        <div class="translate__file-review">
                            <span class="output-name">${fileName}</span>
                            <img src="/static/images/ico-cancel.svg" class="upload-remove" alt="X">
                        </div>
                    `);
                }
            }

            if (!isValid) {
                thisInput.val('');
                thisContainer.removeClass('upload-success').addClass('is-error');
                return false;
            }

            thisContainer.addClass('upload-success').removeClass('is-error')
            if (e)
                thisInput[0].files = files;
            Upload.submit();
        }

        thisContainer.on('change', 'input', function(e) {
            validateFiles(false, this)
        });
    },

    // Перевірка завантажених файлів
    submit: function() {
        $('.translate__file-block').hide();
        $('.uploaded').css('display', 'flex')
    }
}

function removeFile(fileName) {
    let input = document.querySelector('input[type="file"]');
    let files = input.files;
    let fileBuffer = new DataTransfer();

    for (let i = 0; i < files.length; i++) {
        if (files[i].name !== fileName) {
            fileBuffer.items.add(files[i]);
        }
    }

    input.files = fileBuffer.files;

    console.log(`Видалено файл: ${fileName}`);

    updateFileList();
}

function updateFileList() {
    let input = document.querySelector('input[type="file"]');
    let fileList = document.querySelector('.file-list');
    fileList.innerHTML = '';

    for (let i = 0; i < input.files.length; i++) {
        let fileName = input.files[i].name;
        fileList.innerHTML += `
            <div class="translate__file-review">
                <span class="output-name">${fileName}</span>
                <img src="/static/images/ico-cancel.svg" class="upload-remove" alt="X">
            </div>
        `;
    }

    if (input.files.length === 0) {
        resetUpload();
    }
}

function resetUpload() {
    let thisContainer = $("#upload");
    thisContainer.find('input').val('')
    thisContainer.removeClass('upload-success')
    $('.uploaded').hide();
    $('.output-type').hide();
    $('.translate__file-block.input').css('display', 'flex')
}

$(document).on('click', '.upload-remove', function () {
    let fileItem = $(this).closest('.translate__file-review');
    let fileName = fileItem.find('.output-name').text();
    removeFile(fileName);
});
