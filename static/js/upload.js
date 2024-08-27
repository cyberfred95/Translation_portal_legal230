var Upload = {
    fileList: new DataTransfer(),

    init: function () {
        let thisContainer = $("#upload");

        thisContainer.on('drag dragstart dragend dragover dragenter dragleave drop', function (e) {
            e.preventDefault();
            e.stopPropagation();
        })
            .on('dragover dragenter', function () {
                thisContainer.addClass('is-dragover');
            })
            .on('dragleave dragend drop', function () {
                thisContainer.removeClass('is-dragover');
            })
            .on('drop', function (e) {
                Upload.handleFiles(e.originalEvent.dataTransfer.files);
            });

        $(document).on('click', '.upload-remove', function () {
            let fileItem = $(this).closest('.translate__file-review');
            let fileName = fileItem.find('.output-name').text();
            Upload.removeFile(fileName);
        });

        thisContainer.on('change', 'input', function (e) {
            Upload.handleFiles(this.files);
        });
    },

    handleFiles: function (newFiles) {
        let thisContainer = $("#upload");
        let thisInput = thisContainer.find('input');
        let fileTypes = thisInput[0].hasAttribute('accept') && thisInput.attr('accept')
            ? thisInput.attr('accept').replaceAll(' ', '').split(',').map(type => type.trim())
            : false;
        let maxFileSize = parseInt(thisInput.attr('data-maxsize')) * 1024 * 1024;
        let errorBlock = thisInput.closest('.input').find('.invalid-feedback');

        for (let i = 0; i < newFiles.length; i++) {
            let file = newFiles[i];
            let isFileValid = this.validateFile(file, fileTypes, maxFileSize);

            if (isFileValid === true) {
                this.addFile(file);
            } else {
                errorBlock.html(isFileValid);
                thisContainer.removeClass('upload-success').addClass('is-error');
            }
        }

        this.updateFileList();
        this.updateInputFiles();

        if (this.fileList.files.length > 0) {
            thisContainer.addClass('upload-success').removeClass('is-error');
            this.submit();
        }
    },

    validateFile: function (file, fileTypes, maxFileSize) {
        if (fileTypes) {
            let isValidType = fileTypes.some(type => {
                const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
                return file.type === type ||
                    file.type.includes(type.split(',')[0]) ||
                    fileExtension === '.' + type.split('.').pop();
            });
            if (!isValidType) {
                return 'Allow file: ' + fileTypes.map(type => '.' + type.split('.').pop()).join(', ');
            }
        }

        if (file.size > maxFileSize) {
            return 'Max size file' + (maxFileSize / 1024 / 1024) + 'MB';
        }

        return true;
    },

    addFile: function (file) {
        // Перевіряємо, чи файл з таким ім'ям вже існує
        for (let i = 0; i < this.fileList.files.length; i++) {
            if (this.fileList.files[i].name === file.name) {
                console.log(`Файл ${file.name} вже існує в списку.`);
                return;
            }
        }
        this.fileList.items.add(file);
    },

    removeFile: function (fileName) {
        let newFileList = new DataTransfer();
        for (let i = 0; i < this.fileList.files.length; i++) {
            if (this.fileList.files[i].name !== fileName) {
                newFileList.items.add(this.fileList.files[i]);
            }
        }
        this.fileList = newFileList;
        this.updateFileList();
        this.updateInputFiles();

        if (this.fileList.files.length === 0) {
            this.resetUpload();
        }
    },

    updateFileList: function () {
        let fileList = $('.file-list');
        fileList.empty();

        for (let i = 0; i < this.fileList.files.length; i++) {
            let fileName = this.fileList.files[i].name;
            fileList.append(`
                <div class="translate__file-review">
                    <span class="output-name">${fileName}</span>
                    <img src="/static/images/ico-cancel.svg" class="upload-remove" alt="X">
                </div>
            `);
        }
    },

    updateInputFiles: function () {
        let input = document.querySelector('input[type="file"]');
        input.files = this.fileList.files;
    },

    resetUpload: function () {
        let thisContainer = $("#upload");
        thisContainer.find('input').val('');
        thisContainer.removeClass('upload-success');
        $('.uploaded').hide();
        $('.output-type').hide();
        this.fileList = new DataTransfer();
        this.updateFileList();
        this.updateInputFiles();
        $('.translate__file-block.input').css('display', 'flex');
        $('.translate__file-block.complete').css('display', 'none');
    },

    publicReset: function () {
        this.resetUpload();
    },

    submit: function () {
        $('.uploaded').css('display', 'flex');
    }
}

$(document).ready(function () {
    Upload.init();
});
