let util = require('./util.js')


module.exports = (function() {

  var _state;

  let cardui = {}

  cardui.init = function(gamestate) {
    _state = gamestate
  }

  cardui.factory = function(data) {
    const elem = $('<li></li>')
    elem.attr('id', `card-${data.id}`)
    elem.attr('data-card-id', data.id)  // Used by autocard

    elem.addClass('card-list-item')  // Base for CSS
    elem.addClass('card-autocard')  // Show autocard popups

    cardui.set_name(elem, data.json.name)
    cardui.set_annotation(elem, data.annotation)

    if (data.token) {
      elem.prepend($('<i class="token-symbol fas fa-ghost">'))
    }

    if (data.tapped) {
      elem.addClass('tapped')
    }

    if (data.face_down) {
      if (data.owner != _state.viewer_name) {
        cardui.set_name(elem, 'face down')
      }

      elem.addClass('face-down')
      elem.removeClass('card-autocard')
      const icon = $('<i class="not-visible-icon fas fa-caret-square-down">')
      elem.find('.card-name').prepend(icon)
    }

    else if (data.scarred) {
      elem.prepend($('<i class="scar-symbol fas fa-bolt">'))
      elem.addClass('scarred')
    }

    // Mana cost (hidden by default)
    const mana_cost = $('<div class="card-mana-cost">')
    mana_cost.addClass('d-none')
    mana_cost.append(util.mana_symbols_from_string(data.json.card_faces[0].mana_cost))
    elem.prepend(mana_cost)

    // Power/Toughness (only shown in creatures zone)
    const power = data.json.card_faces[0].power
    const toughness = data.json.card_faces[0].toughness
    if (power !== undefined && power != '') {
      const pt = $('<div class="card-power-toughness">')
      pt.addClass('d-none')
      pt.text(`${power}/${toughness}`)
      elem.prepend(pt)
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
    return _state.card_is_visible(data.id)
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


  cardui.set_revealed = function(elem) {
    elem.find('.card-name').prepend($('<i class="far fa-eye revealed-icon"></i>'))
  }


  cardui.set_visibility = function(elem, is_visible, is_face_down) {
    if (is_visible) {
      elem.removeClass('not-visible')
    }
    else if (!is_face_down) {
      elem.addClass('not-visible')
      elem.removeClass('card-autocard')
      cardui.set_name(elem, 'hidden')
    }
  }


  cardui.show_ownership = function(elem) {
    elem.prepend($('<i class="ownership-symbol fas fa-arrows-alt-h">'))
  }


  cardui.show_power_toughness = function(elem) {
    elem.find('.card-power-toughness').removeClass('d-none')
  }


  cardui.show_mana_cost = function(elem) {
    elem.find('.card-mana-cost').removeClass('d-none')
  }


  cardui.twiddle = function(elem) {
    let id = cardui.id(elem)
    _state.twiddle(id)
  }


  return cardui
}())
