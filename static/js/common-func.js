function Drop() {

  function handleOpenClose(e) {
    e.preventDefault();
    $(this).next('.sub-nav').toggleClass('visible-drop');
  }

  $(document).on('click', '#menu-icon', handleOpenClose)
}

$(document).ready(function() {
  Drop();
})


$.fn.isValid = function(){
  return this[0].checkValidity()
}

$.fn.reportValidity = function(){
  return this[0].reportValidity()
}
$.validator.setDefaults({
  ignore: []
});

const only_num = /^[0-9]+$/;
const only_num_replace = /[^0-9.]/g;

const text_replace = /[^a-zA-Z0-9-_]/g;

const message = {
  empty: 'This field is required',
  max_length: 'Max length is ',
  min_length: 'Min length is ',
  requiredSelection: 'Select one of these fields',
  repassword: 'Passwords do not match',
  one_required: 'Select at least one of this fields'
}

const inputs = {
  'required-selection': {
    'rules': {
      requiredSelection: true,
      messages: {
        requiredSelection: message.requiredSelection
      }
    }
  },
  'text': {
    'rules': {
      regexReplace: text_replace
    }
  },
  'password': {
    'rules': {
      minlength: 6,
      messages: {
        minlength: message.min_length + 6
      }
    }
  },
  're-password': {
    'rules': {
      minlength: 6,
      repassword: true,
      messages: {
        minlength: message.min_length + 6,
        repassword: message.repassword
      }
    }
  },
  'one-required': {
    'rules': {
      one_required: true,
      messages: {
        one_required: message.one_required,
      }
    }
  }
}


function validatorMethods() {

  $.validator.addMethod("regex", function (value, element, regexp) {
    var re = new RegExp(regexp);

    return value == '' || re.test(value);
  });

  $.validator.addMethod("regexReplace", function (value, element, regexp) {

    return true;
  });

  $.validator.addMethod("requiredSelection", function (value, element, regexp) {
    let $form = $(element).closest('form')
    let input = $('[data-validation="required-selection"]', $form);
    let inputContainers = input.closest('.select, .checkbox:not(.select)')
    let canContinue = false;

    inputContainers.each(function () {
      let thisInputs = $(this).find('[data-validation="required-selection"]')

      thisInputs.each(function () {
        if($(this).is(':checked'))
          canContinue = true;
      })
    })

    if(canContinue){
      input.removeClass('error')
      inputContainers.removeClass('error')
    } else {
      input.addClass('error')
      inputContainers.addClass('error')
    }

    return canContinue;
  });

  $.validator.addMethod("repassword", function (value, element, regexp) {
    let thisForm = $(element).closest('form')
    let password = $('[data-validation="password"]', thisForm).val()

    return value === password
  });

  $.validator.addMethod("one_required", function (value, element, regexp) {
    let thisForm = $(element).closest('form')
    let oneRequiredFields = $('[data-validation="one-required"]', thisForm)
    let canContinue = false;

    oneRequiredFields.each(function () {
      if(this.value)
        canContinue = true;
    })

    if(canContinue)
      oneRequiredFields.each(function () {
        $(this).removeClass('error')
        $(this).closest('.error').removeClass('error')
      })

    return canContinue
  });

}

function inputsRules($form) {
  $('[required]', $form).each(function () {
    if(typeof $(this).rules().required !== 'undefined') return;
    $(this).rules("add", {
      required: true,
      messages: {
        required: message.empty
      }
    });
  });

  $('[maxlength]', $form).each(function () {
    if(typeof $(this).rules().maxlength !== 'undefined') return;
    let max = $(this).attr('maxlength');
    $(this).rules("add", {
      maxlength: max,
      messages: {
        maxlength: message.max_length + max
      }
    });
    $(this).on('input', function () {
      let maxLengthElement = $(this);
      let maxLength = parseInt(maxLengthElement.attr('maxlength'));
      if (maxLengthElement[0].value.length > maxLength)
        maxLengthElement[0].value = maxLengthElement[0].value.substr(0, maxLength);
    })
  });

  $('[minlength]', $form).each(function () {
    if(typeof $(this).rules().minlength !== 'undefined') return;
    let min = $(this).attr('minlength');
    $(this).rules("add", {
      minlength: min,
      messages: {
        minlength: message.min_length + min
      }
    });
  });

  $('input', $form).on('change', function () {
    $(this).valid()
  })

  $.each(inputs, function (data_id, opts) {
    var $input = $('[data-validation='+data_id+']', $form);

    if($input.length) {
      if (typeof opts.rules !== 'undefined') {
        validationRule($input,'add', opts.rules)
        if(typeof opts.rules.regexReplace !== 'undefined'){
          $input.on('input', function () {
            var re = new RegExp(opts.rules.regexReplace);
            this.value = this.value.replace(re, "");
          })
        }

      }
    }
  });
}
function validationRule(input, action, rule){
  input.each(function () {
    if(action === 'add' && typeof $(this).rules()[rule] !== 'undefined') return;
    if(rule == 'required' && action == 'add') {
      $(this).rules('add', {
        required: true,
        messages: {
          required: message.empty
        }
      });
    } else if(rule == 'required') {
      $(this).removeAttr('required')
      $(this).rules(action, rule);
    } else {
      $(this).rules(action, rule);
    }
  })
}
function validate(form, options) {
  var setings = {
    errorFunction: null,
    submitFunction: null,
    highlightFunction: null,
    unhighlightFunction: null
  };

  validatorMethods();

  $.extend(setings, options);

  if(typeof form !== 'string'){
    var $form = form;
  } else {
    var $form = $(form);
  }

  if ($form.length && $form.attr('novalidate') === undefined) {
    $form.on('submit', function (e) {
      e.preventDefault();
    });

    let thisValidator = $form.validate({
      errorClass: 'errorText',
      focusCleanup: false,
      onclick: false,
      onfocusout: false,
      // onkeyup: false,
      focusInvalid: true,
      invalidHandler: function (event, validator) {
        if (typeof setings.errorFunction === 'function') {
          setings.errorFunction(form);
        }
      },
      errorPlacement: function (error, element) {
        let thisContainer = element.closest('.select');

        if(!thisContainer.length)
          thisContainer = element.closest('.modal__name')
        if(!thisContainer.length)
          thisContainer = element.closest('.profile__input')
        if(!thisContainer.length)
          thisContainer = element.closest('.validation-input')

        error.appendTo(thisContainer);

        if(!thisContainer.length) {
          thisContainer = element.closest('.modal__btn')
          error.appendTo(thisContainer.find('.modal__btn-text--error').empty())
        }
      },
      highlight: function (element, errorClass, validClass) {
        let thisContainer = $(element).closest('.select');
        if(!thisContainer.length)
          thisContainer = $(element).closest('.profile__input');
        if(!thisContainer.length)
          thisContainer = $(element).closest('.validation-input');
        if(!thisContainer.length && !$(element).parent().hasClass('btn'))
          thisContainer = $(element).parent();

        thisContainer.addClass('error');
        $(element).addClass('error');
        if(!thisContainer.length) {
          thisContainer = $(element).closest('.modal__btn')
          thisContainer.addClass('is-error')
        }

        if (typeof setings.highlightFunction === 'function') {
          setings.highlightFunction(form);
        }
      },
      unhighlight: function (element, errorClass, validClass) {
        let thisContainer = $(element).closest('.select');
        if(!thisContainer.length)
          thisContainer = $(element).closest('.profile__input');
        if(!thisContainer.length)
          thisContainer = $(element).closest('.validation-input');
        if(!thisContainer.length && !$(element).parent().hasClass('btn'))
          thisContainer = $(element).parent();

        $(element).removeClass('error');
        thisContainer.removeClass('error');
        if(!thisContainer.length) {
          thisContainer = $(element).closest('.modal__btn')
          thisContainer.removeClass('is-error')
        }

        if (typeof setings.unhighlightFunction === 'function') {
          setings.unhighlightFunction(form);
        }
      },
      submitHandler: function (form) {
        $('[type=submit]', $(form)).each(function (){
          $(this).attr('disabled', 'disabled');
        });
        if (typeof setings.submitFunction === 'function') {
          setings.submitFunction(form);
        } else {
          $form[0].submit();
        }
      }
    });

    inputsRules($form);

    return thisValidator;
  }
}



function redirectToPage(ev) {
  document.location.href = ev.target.getAttribute('data-url');
}

function changeBlocksState(hideElements, showElements) {
  hideElements.forEach((item) => {
    item.style.display = 'none';
  });
  showElements.forEach((item) => {
    item.style.display = 'block';
  })
}

function changeBlocksStateJQuery(hideElements, showElements) {
  hideElements.forEach((item) => {
    $(item).hide();
  });
  showElements.forEach((item) => {
    $(item).show();
  })
}

async function getTaskStatus(taskID, callCount) {
  const STOP_EXECUTION_NUMBER = 100;
  callCount = callCount || 0;

  let response = await fetch(domain + `/tasks/${taskID}/`, {
    method: 'GET',
    credentials: 'same-origin',
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
    }
  });
  if (!response.ok) {
    $('#errorModal').modal('show');
    throw new Error('Network response was not OK');
  }
  const data = await response.json();
  console.log(data)
  const taskStatus = data.task_status;

  if (taskStatus === 'SUCCESS') {
    return data;
  } else if (taskStatus === 'FAILURE') {
    return false;
  }

  // stop fetch endpoint after 30 seconds
  if (callCount === STOP_EXECUTION_NUMBER) return false;

  return new Promise(resolve => {
    setTimeout(() => resolve(getTaskStatus(data.task_id, callCount + 1)), 3000)
  })
}

function setupDownloadLinkEvents() {
  $('.js-download-link').on('click', (ev) => {
    const downloadUrl = ev.target.getAttribute('data-url');
    console.log('data-url', downloadUrl, $(this));
    const url = window.location.origin + downloadUrl;
    window.open(url, '_blank').focus();
  })
}

function setupReportPageEvents() {
  setupDownloadLinkEvents();
}

function showErrorPopup(error=null) {
  if(error != null){
    if(error.type == 'sys_error'){
      $('#errorDescription').html('Information about this incident sent to our support team and we will connect with you a soon as possible.' );
    }else{
      $('#errorDescription').html(error.error);
    }
  }
  $('#errorModal').modal('show');
}

function showNoticePopup() {
  $('#noticeModal').modal('show');
}


function openPopup(e = false, listItemModal) {
  if(e) e.preventDefault();
  var fancyModal = $(this).attr('href') ? $(this).attr('href') : listItemModal;

  Fancybox.show([{
    src: fancyModal,
    type: 'inline',
    dragToClose: false,
    placeFocusBack: false,
    trapFocus: false,
    autoFocus: false,
  }]);
}

const isVisible = function (ele, container) {
  const eleTop = ele.offsetTop;
  const eleBottom = eleTop + ele.clientHeight;

  const containerTop = container.scrollTop;
  const containerBottom = containerTop + container.clientHeight;

  // The element is fully visible in the container

  return {
    visible: (eleTop >= containerTop && eleBottom <= containerBottom),
    part: (containerBottom - eleTop) > 0 ? (containerBottom - eleTop) : eleBottom - containerBottom
  }
};

function selects() {
  let container = $('.select')

  function selectItem(selected){
    let thisItem = $(this)

    if(typeof selected.originalEvent === 'undefined')
      thisItem = selected
    if(thisItem.is('input'))
      thisItem = thisItem.closest('li')

    let thisContainer = thisItem.closest('.select')
    let elseItems = thisContainer.find('li')
    let thisText = thisItem.text().trim().replaceAll('\n', '')
    if(thisItem.find('.select__item-title').length){
      thisText = thisItem.find('.select__item-title').text().trim().replaceAll('\n', '')
    }
    let thisValue = thisItem.attr('data-value')
    let outputText = thisContainer.find('.output_text')
    let outputValue = thisContainer.find('.output_value')
    let placeholder = outputText.attr('data-placeholder')

    if(thisContainer.hasClass('checkbox')){
      if(thisItem.hasClass('selected')) {
        thisItem.removeClass('selected')
      } else {
        thisItem.addClass('selected')
      }

      let allSelected = thisContainer.find('.selected')

      thisText = '';
      if(placeholder)
        thisText = placeholder+' '

      allSelected.each(function () {
        thisText += $(this).text().trim().replaceAll('\n', '')

        if(!$(this).is(allSelected.last()))
          thisText += ', '
      })
      thisText = thisText.trim();
      if(elseItems.length === allSelected.length){
        thisText = 'All'
      }
    } else {
      elseItems.removeClass('selected').removeClass('hidden').removeClass('hover')
      thisItem.addClass('selected')
    }

    if(outputText.length)
      outputText.val(thisText)
    if(outputValue.length)
      outputValue.val(thisValue).trigger('change')
  }
  function searchItem(e) {
    let regex = new RegExp(text_replace);
    let input = $(e.target)
    let value = input.val().toLowerCase().replace(regex, "");
    let thisContainer = input.closest('.select')
    let items = thisContainer.find('li')

    items.each(function () {
      let thisItem = $(this)

      if(thisItem.text().toLowerCase().replace(regex, "").indexOf(value) === 0){
        thisItem.removeClass('hidden')
      } else {
        thisItem.addClass('hidden')
      }
    })
  }
  function arrows(e) {
    e = e || window.event;
    let currentOpen = $('.select.open li:not(.hidden)')
    let currentHover = $('.select.open li:not(.hidden).hover')
    let topPos = 0;
    let keycode = e.keyCode

    if(keycode === 38 || keycode === 40) {
      currentOpen.removeClass('hover')

      if (keycode === 38) {
        if(currentHover.length) {
          let foundPrev = false

          currentHover.prevAll().each(function () {
            if(!$(this).hasClass('hidden')) {
              foundPrev = $(this)
            }
            if(foundPrev)
              return false;
          })

          if(foundPrev) {
            currentHover = foundPrev.addClass('hover')
          } else {
            currentHover.addClass('hover')
          }
        } else {
          currentHover = currentOpen.first().addClass('hover')
        }
        let visibility = isVisible(currentHover[0], currentHover.closest('ul')[0])
        if(!visibility.visible){
          currentHover.closest('ul')[0].scrollTop -= visibility.part
        }
      } else if (keycode === 40) {
        if(currentHover.length){
          let foundNext = false

          currentHover.nextAll().each(function () {
            if(!$(this).hasClass('hidden')) {
              foundNext = $(this)
            }
            if(foundNext)
              return false;
          })

          if(foundNext) {
            currentHover = foundNext.addClass('hover')
          } else {
            currentHover.addClass('hover')
          }
        } else {
          currentHover = currentOpen.first().addClass('hover')
        }
        let visibility = isVisible(currentHover[0], currentHover.closest('ul')[0])
        if(!visibility.visible){
          currentHover.closest('ul')[0].scrollTop += visibility.part
        }
      }

    }

    if(keycode === 13){
      e.preventDefault()
      if(currentHover.length) {
        currentHover.removeClass('selected')
        selectItem(currentHover)
        $(document).trigger('close-dropdown')
      } else {
        $(e.target).click()
      }
    }
  }

  container.each(function () {
    let selected = $(this).find('.selected')
    let placeholder = $(this).find('.output_text').attr('data-placeholder')

    if(selected.length) {
      selected.removeClass('selected')
      selectItem(selected)
    } else if(placeholder){
      $(this).find('.output_text').val(placeholder)
    }
  })

  document.onkeydown = arrows;
  $(document).on('click', '.select:not(.checkbox) li', selectItem)
  // $(document).on('mouseover', '.select li', function () {
  //   $('.select li').removeClass('hover')
  //   $(this).addClass('hover')
  // })
  // $(document).on('mouseover', '.select:not(.select__dropdown)', function () {
  //   $('.select li').removeClass('hover')
  // })
  $(document).on('change', '.select__dropdown input', selectItem)
  $(document).on('input', '.select:not(.checkbox) .output_text', searchItem)

  dropdown(container, {containerClass: 'select', btnSelector: '.output_text', dropdownSelector: '.select__dropdown'})
}

function ajaxError(resp = false, newErrorPopup = false) {
  let activePopup = $('.fancybox__content')

  if(activePopup.length) {
    activePopup = activePopup.attr('id')
    Fancybox.close()
  } else {
    activePopup = false
  }

  if(newErrorPopup && newErrorPopup.indexOf('#') === -1){
    newErrorPopup = false
  }

  if(resp && typeof resp.statusText !== 'undefined' && !newErrorPopup) {
    let modalText = $('#modal_error').find('.modal__text')
    modalText.find('>*:not(:last-child)').remove()
    modalText.prepend('<p>' + resp.statusText + '</p>')
  }

  let closeTimeout = setTimeout(function () {
    Fancybox.close()
  }, 5000)

  Fancybox.show([{
    src: newErrorPopup || '#modal_error',
    type: 'inline',
    dragToClose: false,
    placeFocusBack: false,
    trapFocus: false,
    autoFocus: false,
  }], {
    on: {
      "destroy": (event, fancybox, slide) => {
        clearTimeout(closeTimeout)

        if(activePopup){
          openPopup(false, activePopup)
        }
      },
    }
  });


  $('[type=submit]').removeAttr('disabled')
}


var Upload = {
  filename: '',
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

      Upload.filename = files[0].name

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
        upload.find('.filename').text(Upload.filename)
        Upload.submit();
      } else {
        validateFile(false, this)
      }
    });
  },

  // Check the uploaded file
  submit: function() {
    $('.translate__file-block').hide();
    $('.translate__file-block.uploaded').css('display', 'flex')
  }
}

function removeUsedModels(first, second) {
  let firstContainer = first.closest('.select')
  let secondContainer = second.closest('.select')
  let firstSelected = firstContainer.find('.selected')

  if(!firstSelected.attr('data-value')) return;

  let secondItem = secondContainer.find('[data-value="'+firstSelected.attr('data-value')+'"]')

  secondContainer.find('li').removeClass('used')
  secondItem.addClass('used')

  if(secondItem.hasClass('selected')){
    secondItem.removeClass('selected')
    secondContainer.find('.output_text').val('')
    secondContainer.find('.output_value').val('')
  }
}

function textTooltip() {
  let tooltipIcon = '<div class="text-tooltip__ico">\n' +
      '                <svg width="17" height="17" viewBox="0 0 17 17" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8.5 15.9375C6.52745 15.9375 4.63569 15.1539 3.24089 13.7591C1.84609 12.3643 1.0625 10.4725 1.0625 8.5C1.0625 6.52745 1.84609 4.63569 3.24089 3.24089C4.63569 1.84609 6.52745 1.0625 8.5 1.0625C10.4725 1.0625 12.3643 1.84609 13.7591 3.24089C15.1539 4.63569 15.9375 6.52745 15.9375 8.5C15.9375 10.4725 15.1539 12.3643 13.7591 13.7591C12.3643 15.1539 10.4725 15.9375 8.5 15.9375ZM8.5 17C10.7543 17 12.9163 16.1045 14.5104 14.5104C16.1045 12.9163 17 10.7543 17 8.5C17 6.24566 16.1045 4.08365 14.5104 2.48959C12.9163 0.895533 10.7543 0 8.5 0C6.24566 0 4.08365 0.895533 2.48959 2.48959C0.895533 4.08365 0 6.24566 0 8.5C0 10.7543 0.895533 12.9163 2.48959 14.5104C4.08365 16.1045 6.24566 17 8.5 17Z" fill="#2B4459"/><path d="M5.58348 6.14762C5.58202 6.18194 5.5876 6.21618 5.59987 6.24826C5.61214 6.28034 5.63085 6.30956 5.65483 6.33415C5.67881 6.35873 5.70757 6.37814 5.73934 6.3912C5.7711 6.40425 5.8052 6.41067 5.83954 6.41006H6.7161C6.86273 6.41006 6.9796 6.29 6.99873 6.14444C7.09435 5.44744 7.57248 4.93956 8.4246 4.93956C9.15348 4.93956 9.82073 5.304 9.82073 6.18056C9.82073 6.85525 9.42335 7.1655 8.79542 7.63725C8.08035 8.15681 7.51404 8.7635 7.55442 9.74844L7.5576 9.979C7.55872 10.0487 7.5872 10.1152 7.63689 10.1641C7.68658 10.213 7.75351 10.2404 7.82323 10.2404H8.68492C8.75536 10.2404 8.82293 10.2124 8.87274 10.1626C8.92255 10.1128 8.95054 10.0452 8.95054 9.97475V9.86319C8.95054 9.10031 9.2406 8.87825 10.0237 8.28431C10.6707 7.79238 11.3454 7.24625 11.3454 6.09981C11.3454 4.49438 9.98967 3.71875 8.50535 3.71875C7.15917 3.71875 5.68442 4.34562 5.58348 6.14762ZM7.23779 12.2708C7.23779 12.8371 7.68935 13.2557 8.31092 13.2557C8.95798 13.2557 9.40317 12.8371 9.40317 12.2708C9.40317 11.6843 8.95692 11.2721 8.30985 11.2721C7.68935 11.2721 7.23779 11.6843 7.23779 12.2708Z" fill="#2B4459"/></svg>\n' +
      '              </div>';
  let tooltipHtml = '<div class="text-tooltip">\n' +
      '                 <div class="text-tooltip__container" role="tooltip">\n' +
      '                   <div class="text-tooltip__inner"></div>\n' +
      '                   <div class="text-tooltip__arrow"><svg width="22" height="15" viewBox="0 0 22 15" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M-6.55671e-07 9.53674e-07L22 -7.97623e-09L11 15L-6.55671e-07 9.53674e-07Z" fill="#2B4459"/></svg></div>\n' +
      '                 </div>\n' +
      '              </div>';
  let tooltips = $('[data-text-tooltip]')

  function showTooltip() {
    let thisContainer = $(this).closest('[data-text-tooltip]')
    let tooltipText = thisContainer.attr('data-text-tooltip')
    let tooltipEl = $(tooltipHtml)
    let offsetLeft = thisContainer.offset().left + thisContainer[0].offsetWidth
    let offsetTop = thisContainer.offset().top

    tooltipEl.find('.text-tooltip__inner').text(tooltipText)

    $('body').append(tooltipEl)

    setTimeout(function () {
      tooltipEl.css({
        'left': offsetLeft+'px',
        'top': offsetTop+'px',
        'opacity': '1',
        'visibility': 'visible'
      })
    }, 100)
  }
  function removeTooltip() {
    let thisTooltip = $('.text-tooltip')
    thisTooltip.css('opacity', '0')
    setTimeout(function () {
      thisTooltip.remove()
    }, 300)
  }

  tooltips.each(function () {
    let thisIcon = $(tooltipIcon)
    $(this).append(thisIcon)
    thisIcon.hover(showTooltip, removeTooltip)
  })
}

textTooltip()


function modalShadow() {
  let inners = $('.modal--shadow-inner')

  function checkOverflow(newThis) {
    let $this = this
    if(typeof newThis.originalEvent === 'undefined')
      $this = newThis
    let thisEl = $($this).closest('.modal--shadow')
    let scrollTop = $this.scrollTop
    let isReachBottom = $this.offsetHeight + scrollTop + 10 >= $this.scrollHeight

    if(scrollTop < 10){
      thisEl.addClass('is-at-top')
    } else {
      thisEl.removeClass('is-at-top')
    }

    if(isReachBottom){
      thisEl.addClass('is-at-bottom')
    } else {
      thisEl.removeClass('is-at-bottom')
    }
  }

  inners.on('scroll', checkOverflow)
  inners.each(function () {
    checkOverflow(this)
  })

  return checkOverflow;
}

let modalShadowUpdate = modalShadow()


function modalTextCounters() {
  
  function refreshCounter() {
    let thisInput = $(this)
    if(!thisInput.length)
      thisInput = $('.modal__block-input>textarea')

    thisInput.each(function () {
      let thisMax = parseInt($(this).attr('maxlength'))
      let thisCounter = $(this).parent().find('.modal__block-input__counter')

      if(thisMax){
        thisCounter.text(thisMax - $(this).val().length)
      }
    })
  }
  
  $(document).on('input', '.modal__block-input>textarea', refreshCounter)
  refreshCounter()
}

if($('.modal__block-input__counter').length)
  modalTextCounters()