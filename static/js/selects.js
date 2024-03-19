
const text_replace = /[^a-zA-Z0-9-_]/g;

function dropdown(dropdownEl, options) {
  let opts = {
    closeOnClick: true,
    timing: false
  }
  let timing = 300;

  $.extend( opts, options );

  function open(e) {
    e.preventDefault()
    let container = $(this).closest('.'+opts.containerClass)
    let thisDropdown = container.find(opts.dropdownSelector)

    if(e.type === 'focusin')
      container.addClass('focusin')

    if(((container.hasClass('open') && container.hasClass('checkbox')) || container.hasClass('disabled')) && !container.hasClass('focusin')){
      close()
      return;
    }

    if(e.type !== 'focusin')
      container.removeClass('focusin')

    close(container)

    container.addClass('open').css('z-index', '4')
    thisDropdown.slideDown(timing)
  }
  function close(dontClose = false) {
    let dropdownsToClose = $('.'+opts.containerClass)

    if(dontClose)
      dropdownsToClose = dropdownsToClose.not(dontClose)

    dropdownsToClose.find('li').removeClass('hover')

    dropdownsToClose.removeClass('open')
    dropdownsToClose.find(opts.dropdownSelector).slideUp(timing)

    setTimeout(function () {
      dropdownsToClose.removeAttr('style')
    }, timing)
  }

  $(document).on('click', function (e) {
    let thisEl = $(e.target)

    if(!thisEl.hasClass(opts.containerClass) && !thisEl.closest('.'+opts.containerClass).length)
      close()
  })
  $(document).on('click', '.'+opts.containerClass +' '+ opts.btnSelector, open)
  $(document).on('focusin', '.'+opts.containerClass +' '+ opts.btnSelector, open)
  $(document).on('focusout', '.'+opts.containerClass +' '+ opts.btnSelector, function () {
    $(this).closest('.'+opts.containerClass).removeClass('focusin')
    close($(this).closest('.'+opts.containerClass))
  })
  $(document).on('close-dropdown', close)



  if(options.timing !== false)
    timing = options.timing;
  if(options.containerClass === 'select')
    timing = 0;

  if(opts.closeOnClick){
    $(document).on('click', opts.dropdownSelector, function () {
      if(!$(this).closest('.'+opts.containerClass).hasClass('checkbox'))
        close()
    })
  }
}

function isVisible(ele, container) {
  const eleTop = ele.offsetTop;
  const eleBottom = eleTop + ele.clientHeight;

  const containerTop = container.scrollTop;
  const containerBottom = containerTop + container.clientHeight;

  // The element is fully visible in the container

  return {
    visible: (eleTop >= containerTop && eleBottom <= containerBottom),
    part: (containerBottom - eleTop) > 0 ? (containerBottom - eleTop) : eleBottom - containerBottom
  }
}

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

    $('.errorText').hide();

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

      if(thisItem.text().toLowerCase().replace(regex, "").trim().indexOf(value) !== -1){
        thisItem.removeClass('hidden')
      } else {
        thisItem.addClass('hidden')
      }
    })
  }
  function arrows(e) {
    e = e || window.event;
    if(!e.target.closest('.select')) return;
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

$(document).ready(function () {
  selects()
})