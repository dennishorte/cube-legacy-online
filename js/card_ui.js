
module.exports = (function() {

  var _state;

  let cardui = {}

  cardui.init = function(gamestate) {
    _state = gamestate
  }

  cardui.factory = function(data) {
    let card = $('<li></li>')
    cardui.set_name(card, data.json.card_faces[0].name)
    card.attr('id', `card-${data.id}`)

    // Styling and autocard popup
    card.addClass('card-list-item')
    card.attr('data-front', data.json.card_faces[0].image_url)
    if (data.json.card_faces.length > 1) {
      card.attr('data-back', data.json.card_faces[1].image_url)
    }

    cardui.set_annotation(card, data.annotation)
    cardui.set_visibility(card, data)

    if (data.tapped) {
      card.addClass('tapped')
    }

    if (data.face_down) {
      card.addClass('face-down')
    }

    return card
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


  cardui.set_visibility = function(elem, data) {
    if (!cardui.is_visible(data)) {
      elem.addClass('face-down')
    }
  }


  cardui.twiddle = function(elem) {
    let id = cardui.id(elem)
    _state.twiddle(id)
  }


  return cardui
}())
