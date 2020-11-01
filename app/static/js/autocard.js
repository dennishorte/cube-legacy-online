var stopAutocard = false;
var autocardTimeout = null;

const autocardEnterListeners = new Map();
const autocardLeaveListeners = new Map();
function autocard_init(classname) {
  const elements = document.getElementsByClassName(classname);
  for (let i = 0; i < elements.length; i++) {
    const element = elements[i];

    const enterListener = autocardEnterListeners.get(element);
    if (enterListener) {
      element.removeEventListener('mouseenter', enterListener);
    }
    autocardEnterListeners.set(
      element,
      element.addEventListener('mouseenter', (event) => {
        if (!stopAutocard) {
          const target = $(event.target);
          autocard_show_card(
            target.data('front'),
            target.data('back'),
          );
        }
      }),
    );

    const leaveListener = autocardLeaveListeners.get(element);
    if (leaveListener) {
      element.removeEventListener('mouseleave', leaveListener);
    }
    autocardLeaveListeners.set(
      element,
      element.addEventListener('mouseleave', () => autocard_hide_card()),
    );
  }
}

document.onmousemove = function (e) {
  popupElement = document.getElementById('autocardPopup');

  var leftPixelSpace = e.clientX;
  var rightPixelSpace = window.innerWidth - leftPixelSpace;
  var topPixelSpace = e.clientY;
  var bottomPixelSpace = window.innerHeight - topPixelSpace;

  var x_offset = e.clientX + self.pageXOffset;
  var y_offset = e.clientY + self.pageYOffset;

  if (rightPixelSpace > leftPixelSpace) {
    // display on right
    autocardPopup.style.left = Math.max(self.pageXOffset, 5 + x_offset) + 'px';
    autocardPopup.style.right = null;
  } else {
    // display on left
    autocardPopup.style.right = Math.max(window.innerWidth + 5 - x_offset, 0) + 'px';
    autocardPopup.style.left = null;
  }
  if (autocardPopup.offsetHeight > window.innerHeight) {
    autocardPopup.style.top = self.pageYOffset + 'px';
    autocardPopup.style.bottom = null;
  } else {
    if (bottomPixelSpace > topPixelSpace) {
      // display on bottom
      autocardPopup.style.top = 5 + y_offset + 'px';
      autocardPopup.style.bottom = null;
    } else {
      // display on top
      autocardPopup.style.bottom = window.innerHeight + 5 - y_offset + 'px';
      autocardPopup.style.top = null;
    }
  }
};

const autocardLoadListeners = {};
function autocard_show_card(card_image, card_flip) {
  const popup = document.getElementById('autocardPopup');
  const popupImg = document.getElementById('autocardImageFront');
  const popupImgBack = document.getElementById('autocardImageBack');

  console.log("=====\nautocard_show_card")
  console.log(card_image)
  console.log(card_flip)

  if (card_flip) {
    popup.classList.add('double-width');
  } else {
    popup.classList.remove('double-width');
  }

  popupImg.setAttribute('src', card_image);
  if (card_flip) {
    popupImgBack.setAttribute('src', card_flip);
    popupImgBack.classList.remove('d-none');
  } else {
    popupImgBack.removeAttribute('src');
    popupImgBack.classList.add('d-none');
  }

  // only show the three autocard divs once the images are done loading
  autocardLoadListeners[popupImg.id] = () => {
    if (card_flip && !popupImgBack.complete) {
      return;
    }
    // only fill in tags area once the image is done loading
    if (autocardTimeout) autocardTimeout = clearTimeout(autocardTimeout);
    autocardTimeout = setTimeout(() => document.getElementById('autocardPopup').classList.remove('d-none'), 10);
  };
  popupImg.addEventListener('load', autocardLoadListeners[popupImg.id]);

  if (card_flip) {
    autocardLoadListeners[popupImgBack.id] = () => {
      if (!popupImg.complete) {
        return;
      }
      if (autocardTimeout) autocardTimeout = clearTimeout(autocardTimeout);
      autocardTimeout = setTimeout(() => document.getElementById('autocardPopup').classList.remove('d-none'), 10);
    };
    popupImgBack.addEventListener('load', autocardLoadListeners[popupImgBack.id]);
  }

  if (popupImg.complete && (!card_flip || popupImgBack.complete)) {
    // cached workaround
    if (autocardTimeout) autocardTimeout = clearTimeout(autocardTimeout);
    autocardTimeout = setTimeout(() => document.getElementById('autocardPopup').classList.remove('d-none'), 10);
  }
}

function autocard_hide_card() {
  // clear any load events that haven't fired yet so that they don't fire after the card should be hidden
  if (autocardTimeout) autocardTimeout = clearTimeout(autocardTimeout);
  for (const id in autocardLoadListeners) {
    const img = document.getElementById(id);
    img.removeEventListener('load', autocardLoadListeners[id]);
    delete autocardLoadListeners[id];
  }

  document.getElementById('autocardPopup').classList.add('d-none');
}
