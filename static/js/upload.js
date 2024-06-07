var Upload = {

	init: function() {
		let thisContainer = $("#upload");

		thisContainer.on('drag dragstart dragend dragover dragenter dragleave drop', function(e) {
			e.preventDefault();
			e.stopPropagation();
		})
		.on('dragover dragenter', function() { thisContainer.addClass('is-dragover'); })
		.on('dragleave dragend drop', function() { thisContainer.removeClass('is-dragover'); })
		.on('drop', validateFile);

		$(document).on('click', '.upload-remove', function () {
			thisContainer.find('input').val('')
			thisContainer.removeClass('upload-success')
			$('.uploaded').hide();
			$('.output-type').hide();

			$('.translate__file-block.input').css('display', 'flex')
		})

		function validateFile(e, inp){
			let thisInput = thisContainer.find('input')
			let fileTypes = false;
			if(thisInput[0].hasAttribute('accept') && thisInput.attr('accept')) {
				fileTypes = thisInput.attr('accept').replaceAll(' ', '').split(',')
			}
			let maxFileSize = parseInt(thisInput.attr('data-maxsize')) * 1024 * 1024;
			let isValid = false;
			let files = e ? e.originalEvent.dataTransfer.files : inp.files;
			let resultBlock = thisContainer.find('.output-name')

			let errorBlock = thisInput.closest('.input').find('.invalid-feedback')
			let fileName = ''
			let thisName = files[0].name.split('.')
			let thisExt = thisName[thisName.length-1]

			if (files[0].type === 'application/pdf') {
				$('.output-type').css('display', 'flex')
			}
			thisName.pop()

			if(thisName.length > 1) {
				thisName = thisName.join('.')
			} else {
				thisName = thisName[0]
			}

			if(thisName.length > 22)
				thisName = thisName.substring(0, 22) + '... '

			fileName = thisName + '.' + thisExt

			if(fileTypes) {
				$.each(fileTypes, function (_, type) {
					if(type.indexOf(files[0].type) !== -1)
						isValid = true;
				})
			} else {
				isValid = true
			}

			if(!isValid){
				errorBlock.html('Allowed extensions: ' + fileTypes.join(', '))
				thisInput.val('');
				thisContainer.removeClass('upload-success')
				thisContainer.addClass('is-error')

				return false;
			}

			if(files[0].size > maxFileSize){
				isValid = false;
				errorBlock.html('Maximum file size is ' + (maxFileSize / 1024 / 1024)+'mb')
				thisInput.val('');
				thisContainer.removeClass('upload-success')
				thisContainer.addClass('is-error')

				return false;
			}

			thisContainer.addClass('upload-success').removeClass('is-error')

			resultBlock.text(fileName)
			if(e)
				thisInput[0].files = files;
			Upload.submit();
		}

		thisContainer.on('change', 'input', function(e) {
			validateFile(false, this)
		});
	},

	// Check the uploaded file
	submit: function() {
		$('.translate__file-block').hide();
		$('.uploaded').css('display', 'flex')
	}
}
