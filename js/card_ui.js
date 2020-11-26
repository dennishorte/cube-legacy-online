
module.exports = (function() {

  var _state;

  let cardui = {}

  cardui.init = function(gamestate) {
    _state = gamestate
  }

  cardui.factory = function(data) {
    let elem = $('<li></li>')
    elem.attr('id', `card-${data.id}`)

    // Styling and autocard popup
    elem.addClass('card-list-item')

    cardui.set_name(elem, data.json.name)
    cardui.set_annotation(elem, data.annotation)

    if (data.tapped) {
      elem.addClass('tapped')
    }

    if (data.face_down) {
      if (data.owner != _state.viewer_name) {
        cardui.set_name(elem, 'face down')
      }

      elem.addClass('face-down')
      let icon = $('<i class="not-visible-icon fas fa-caret-square-down"></i>')
      elem.find('.card-name').prepend(icon)
    }

    return elem
  }


  cardui.id = function(elem) {
    return parseInt(elem.attr('id').split('-')[1])
  }


  cardui.is_tapped = function(elem) {
    let id = cardui.id(elem)
    return _state.card(id).tapped
  }


  cardui.is_visible = function(data) {
    return data.visibility.includes(_state.viewer_name)
  }


  cardui.set_annotation = function(elem, text) {
    var ann = elem.find('.annotation')

    if (ann.length == 0) {
      ann = $('<p class="card-annotation"></p>')
      elem.append(ann)
    }

    if (text) {
      ann.text(text)
      ann.removeClass('d-none')
    }
    else {
      ann.addClass('d-none')
    }
  }


  cardui.set_name = function(elem, name) {
    var name_elem = elem.find('.card-name')

    if (name_elem.length == 0) {
      name_elem = $('<p class="card-name"></p>')
      elem.prepend(name_elem)
    }

    name_elem.text(name)
  }


  cardui.set_visibility = function(elem, is_visible) {
    if (is_visible) {
      elem.removeClass('not-visible')
    }
    else {
      elem.addClass('not-visible')
      cardui.set_name(elem, 'hidden')
    }
  }


  cardui.twiddle = function(elem) {
    let id = cardui.id(elem)
    _state.twiddle(id)
  }


  return cardui
}())
