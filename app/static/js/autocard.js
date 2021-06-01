'use_strict'

////////////////////////////////////////////////////////////////////////////////
// Public Interface

function autocard_init(classname, legacy, dataFetcher=undefined) {
  legacyAutocard = legacy
  autocardDataFetcher = dataFetcher

  const elements = document.getElementsByClassName(classname)
  for (let i = 0; i < elements.length; i++) {
    const element = elements[i]

    if (!autocardEnterListeners.get(element)) {
      autocardEnterListeners.set(
        element,
        element.addEventListener('mouseenter', _autocard_enter_listener),
      )
    }

    if (!autocardLeaveListeners.get(element)) {
      autocardLeaveListeners.set(
        element,
        element.addEventListener('mouseleave', _autocard_leave_card),
      )
    }
  }
}



////////////////////////////////////////////////////////////////////////////////
// Private Interface

var stopAutocard = false
var legacyAutocard = false
var autocardDataFetcher

// These maps prevent duplicate listeners from being added.
const autocardEnterListeners = new Map()
const autocardLeaveListeners = new Map()

const autocardLoadListeners = {}


// Each time the mouse is moved, calculate the position where the popup should be displayed.
document.addEventListener('mousemove', function (e) {
  const leftPixelSpace = e.clientX
  const rightPixelSpace = window.innerWidth - leftPixelSpace
  const topPixelSpace = e.clientY
  const bottomPixelSpace = window.innerHeight - topPixelSpace

  const x_offset = e.clientX + self.pageXOffset
  const y_offset = e.clientY + self.pageYOffset

  let autocardPopup = _autocard_popup_element()

  if (rightPixelSpace > leftPixelSpace) {
    // display on right
    autocardPopup.style.left = Math.max(self.pageXOffset, 5 + x_offset) + 'px'
    autocardPopup.style.right = null
  }
  else {
    // display on left
    autocardPopup.style.right = Math.max(window.innerWidth + 5 - x_offset, 0) + 'px'
    autocardPopup.style.left = null
  }

  if (bottomPixelSpace > topPixelSpace) {
    // display on bottom
    autocardPopup.style.top = 5 + y_offset + 'px'
    autocardPopup.style.bottom = null
  }
  else {
    // display on top
    autocardPopup.style.bottom = window.innerHeight + 5 - y_offset + 'px'
    autocardPopup.style.top = null
  }
})

function autocard_show_legacy_card(card_id) {
  let popup_element = $(_autocard_popup_element())
  popup_element.removeClass('d-none')
  popup_element.find('.scarred').removeClass('scarred')

  let card_data
  if (autocardDataFetcher) {
    card_data = autocardDataFetcher(card_id)
  }
  else {
    card_data = window.clo.card_data[card_id]
  }

  clo.util.draw_card_frame(
    popup_element.find('.closeup-card-wrapper'),
    card_data,
  )
}

function autocard_show_image_card(card_image, card_flip) {
  const popup = _autocard_popup_element()
  const popupImg = document.getElementById('autocardImageFront')
  const popupImgBack = document.getElementById('autocardImageBack')

  if (card_flip) {
    popup.classList.add('double-width')
  }
  else {
    popup.classList.remove('double-width')
  }

  popupImg.setAttribute('src', card_image)
  if (card_flip) {
    popupImgBack.setAttribute('src', card_flip)
    popupImgBack.classList.remove('d-none')
  }
  else {
    popupImgBack.removeAttribute('src')
    popupImgBack.classList.add('d-none')
  }

  document.getElementById('autocardPopup').classList.remove('d-none')
}

function _autocard_enter_listener(event) {
  if (!stopAutocard) {
    const target = $(event.target)

    if (legacyAutocard) {
      autocard_show_legacy_card(
        target.data('card-id')
      )
    }
    else {
      autocard_show_image_card(
        target.data('front'),
        target.data('back'),
      )
    }
  }
}

function _autocard_leave_card() {
  _autocard_popup_element().classList.add('d-none')
}

function _autocard_popup_element() {
  if (legacyAutocard) {
    return document.getElementById('legacy-card-popup')
  }
  else {
    return document.getElementById('autocardPopup')
  }
}
