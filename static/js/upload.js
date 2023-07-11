var Upload = {

	init: function() {
		let isValid = false;
		let upload = $("#upload");
		let fileTypes = $("#upload").find('input[type=file]').attr('accept').replaceAll(' ', '').split(',')
		let maxFileSize = parseInt($("#upload").find('input[type=file]').attr('data-maxsize')) * 1024 * 1024;

		upload.on('drag dragstart dragend dragover dragenter dragleave drop', function(e) {
			e.preventDefault();
			e.stopPropagation();
		})
		.on('dragover dragenter', function() { upload.addClass('is-dragover'); })
		.on('dragleave dragend drop', function() { upload.removeClass('is-dragover'); })
		.on('drop', validateFile);

		function validateFile(e, inp){
			let files = e ? e.originalEvent.dataTransfer.files : inp.files;
			let input = upload.find('input');
			let errorBlock = input.closest('.input').find('.invalid-feedback')

			$.each(fileTypes, function (_, type) {
				if(type.indexOf(files[0].type) !== -1)
					isValid = true;
			})

			if(!isValid){
				upload.addClass('error')
				input.val('');
				return false;
			}

			if(files[0].size > maxFileSize){
				isValid = false;
				errorBlock.text('Maximum file size is '+(maxFileSize / 1024 / 1024)+'mb').show()
				input.val('');
				return false;
			} else {
				isValid = true;
			}

			errorBlock.hide();
			upload.removeClass('error')
			if(e)
				input[0].files = files;
			input.trigger('change')
		}

		upload.on('change', 'input', function(e) {
			if(isValid) {
				Upload.submit();
			} else {
				validateFile(false, this)
			}
		});
	},

	// Check the uploaded file
	submit: function() {
		$('.translate__form__file-block').hide();
		$('.translate__form__file-block.uploaded').css('display', 'flex')
	}
}
