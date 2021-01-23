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
    _init_closeup_close_on_enter()
    _init_token_maker_interactions()
  }

  function _init_draggable() {
    $('.dialog').draggable({
      handle: '.dialog-header, .drag-handle',
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

  function _init_closeup_close_on_enter() {
    $('.card-closeup-annotation-input').keydown(function(event) {
      if (event.keyCode == 13) {
        $('#card-closeup').find('.dialog-close').click()
      }
    })
  }

  function _init_token_maker_interactions() {
    $('#token-create').click(function() {
      let name = $('#token-name').val()
      let zone = $('#token-zone').val()
      let annotation = $('#token-annotation').val()
      let persistent = $('#token-persistent').prop('checked')

      let player_idx = _data('token-maker').player_idx
      let player = _state.player(player_idx)

      let token = _state.card_factory()
      token.annotation = annotation
      token.owner = player.name
      token.visibility = _state.state.players.map(p => p.name).sort()
      token.token = !persistent  // Persistent cards are not actually tokens

      let data = token.json
      data.name = name
      data.type_line = 'Token'

      let front = data.card_faces[0]
      front.image_url = 'https://i.ibb.co/bBjMCHC/tc19-28-manifest.png'
      front.art_crop_url = 'https://i.ibb.co/bBjMCHC/tc19-28-manifest.png'
      front.name = name
      front.type_line = 'Token'

      _state.card_create(token, zone)
      $(window).trigger('redraw')
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

    util.draw_card_frame(closeup, data)

    // Set annotation
    closeup.find('.card-closeup-annotation-input').val(card.annotation)

    // Set external link to card editor
    const link = `https://cubelegacyonline.com/card/${d.card_id}`
    $('#closeup-card-link').attr('href', link)
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
