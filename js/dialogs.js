'use strict'

let assert = require('assert')
let cardui = require('./card_ui.js')
let util = require('./util.js')


module.exports = (function() {

  var _state;  // game state

  let _dialogs = {
    'card-closeup': {
      active: false,
      card_id: undefined,
    },

    'token-maker': {
      active: false,
      player_idx: undefined,
      zone: undefined,
    },

    'popup-viewer-zone': {
      active: false,
      source_id: undefined,
    }
  }

  function _data(dialog_id) {
    return _dialogs[dialog_id]
  }

  function _init(gamestate) {
    _state = gamestate

    _init_draggable()
    _init_close_buttons()
  }

  function _init_draggable() {
    $('.dialog').draggable({
      handle: '.dialog-header',
    })
  }

  function _init_close_buttons() {
    $('.dialog-close').click(function() {
      let dialog = $(this).closest('.dialog')

      dialog.trigger('clo.dialogs.closing')

      dialog.hide()

      // Reset state
      let data = _dialogs[dialog.attr('id')]
      for (let prop in data) {
        if (!data.hasOwnProperty(prop))
          continue

        if (prop == 'active') {
          data[prop] = false
        }
        else {
          data[prop] = undefined
        }
      }

      dialog.trigger('clo.dialogs.closed')
    })
  }

  function _redraw() {
    _redraw_card_closeup()
    _redraw_popup_viewer_zone()
    _redraw_token_maker()
  }

  function _redraw_card_closeup() {
    let closeup = $('#card-closeup')
    let d = _dialogs['card-closeup']

    if (!d.active) {
      closeup.hide()
      return
    }
    else {
      closeup.show()
      assert.ok(
        d.card_id,
        "card closeup should have source id when active"
      )
    }

    let card = _state.card(d.card_id)
    let data = card.json
    let front = data.card_faces[0]

    // Elements to be updated
    let container = closeup.find('.card-container')
    let name_elem = closeup.find('.frame-card-name')
    let mana_elem = closeup.find('.frame-mana-cost')
    let type_elem = closeup.find('.frame-card-type')
    let rules_elem = closeup.find('.frame-description-wrapper')
    let flavor_elem = closeup.find('.frame-flavor-wrapper')
    let image_elem = closeup.find('.frame-art')
    let ptl_elem = closeup.find('.frame-pt-loyalty')

    // Name, Mana, Type
    name_elem.text(front.name)
    type_elem.text(front.type_line)

    // Mana
    mana_elem.empty().append(util.mana_symbols_from_string(front.mana_cost))

    // Image
    let art_crop = front.image_url.replace('normal', 'art_crop')
    image_elem.attr('src', art_crop)

    // Rules Text
    rules_elem.empty()
    let rules = front.oracle_text.split('\n')
    for (var i = 0; i < rules.length; i++) {
      let rule = rules[i].trim()
      let html_string = util.format_rules_text(rule)

      if (rule.length == 0)
        continue

      let rule_elem = $('<p></p>')
      rule_elem.addClass('frame-description')
      rule_elem.html(html_string)
      rules_elem.append(rule_elem)
    }

    // Flavor text
    flavor_elem.empty()
    let flavor = front.flavor_text.split('\n')
    for (var i = 0; i < flavor.length; i++) {
      let flav = flavor[i].trim()
      if (flav.length == 0)
        continue

      let flav_elem = $('<p></p>')
      flav_elem.addClass('frame-flavor-text')
      flav_elem.text(flav)
      flavor_elem.append(flav_elem)
    }

    // Power/Toughness or Loyalty
    if (front.power) {
      let pt = `${front.power}/${front.toughness}`
      ptl_elem.text(pt)
      ptl_elem.show()
    }
    else if (front.loyalty) {
      ptl_elem.text(front.loyalty)
      ptl_elem.show()
    }
    else {
      ptl_elem.hide()
    }

    // Container classes
    let container_classes = ['card-container']
    if (card.json.card_faces[0].type_line.toLowerCase().indexOf('land') >= 0) {
      container_classes.push('land-card')
    }
    else {
      let colors = util.card_colors(card).join('')

      if (colors == 'W')
        container_classes.push('white-card')

      else if (colors == 'U')
        container_classes.push('blue-card')

      else if (colors == 'B')
        container_classes.push('black-card')

      else if (colors == 'R')
        container_classes.push('red-card')

      else if (colors == 'G')
        container_classes.push('green-card')

      else if (colors.length > 1)
        container_classes.push('gold-card')

      else
        container_classes.push('artifact-card')
    }

    container.removeClass()
    container.addClass(container_classes)

    // Set annotation
    closeup.find('.card-closeup-annotation-input').val(card.annotation)
  }

  function _redraw_popup_viewer_zone() {
    let id = 'popup-viewer-zone'
    let popup = $(`#${id}`)
    let d = _dialogs[id]

    if (!d.active) {
      popup.hide()
      return
    }
    else {
      popup.show()
    }

    assert.ok(d.source_id, "popup-viewer zone should have source id when active")

    let player_idx = util.player_idx_from_elem_id(d.source_id)
    let zone = $(`#${d.source_id}`)
    let zone_name = zone.find('.card-section-name').text().trim()
    let zone_id = zone_name.toLowerCase()

    popup.find('.card-section-header').text(zone_name)

    let card_list = $('#popup-viewer-cards')
    card_list.empty()

    let zone_card_ids = _state.player(player_idx).tableau[zone_id]
    for (var i = 0; i < zone_card_ids.length; i++) {
      let card_id = zone_card_ids[i]
      let card = cardui.factory(_state.card(card_id))
      card.attr('data-source-index', i)
      card_list.append(card)
    }
  }

  function _redraw_token_maker() {
    let id = 'token-maker'
    let dialog = $(`#${id}`)
    let d = _dialogs[id]

    if (!d.active) {
      dialog.hide()
      return
    }

    dialog.show()
  }

  function _show(dialog_id, options) {
    if (dialog_id.charAt(0) == '#') {
      dialog_id = dialog_id.substr(1)
    }

    let d = _dialogs[dialog_id]
    d.active = true
    _dialogs[dialog_id] = $.extend(d, options)

    _redraw()
  }


  return {
    data: _data,
    init: _init,
    redraw: _redraw,
    show: _show,
  }

}())
