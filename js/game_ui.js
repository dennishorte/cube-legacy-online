'use strict'

let assert = require('assert')

let GameState = require('./game_state.js')
let cardui = require('./card_ui.js')
let dialogs = require('./dialogs.js')
let util = require('./util.js')


let gameui = (function() {
  var _state


  ////////////////////////////////////////////////////////////////////////////////
  // State

  let _click_state = {
    delay: 200,
    clicks: 0,
    timer: undefined,
  }

  let _card_drag_state = {
    orig: undefined,
    oidx: undefined,
    dest: undefined,
    didx: undefined,
    card: undefined,
  }

  let _token_maker_state = {
    active: true,
    player_idx: undefined,
  }

  ////////////////////////////////////////////////////////////////////////////////
  // Functions

  function _find_by_path(root, path) {
    assert.ok(root instanceof jQuery, "root should be a jQuery obj")
    assert.ok(Array.isArray(path), "path should be an array")
    assert.notEqual(root.length, 0, "root can't be empty")
    assert.equal(root.length, 1, "root should be a single element")

    var elem = root
    for (var i = 1; i < path.length; i++) {
      elem = elem.find(`.section-${path[i]}`)
      assert.equal(elem.length, 1, `found too many elements on path: ${path}, ${elem.length}`)
    }
    return elem
  }

  function _init_actions() {
    $('#undo').click(function() {
      _state.undo()
      _redraw()
    })

    $('#pass-priority').click(function() {
      _state.pass_priority()
      _save()
      // _redraw()  // This happens in the save callback
    })

    $('#pass-turn').click(function() {
      _state.pass_turn()
      _redraw()
    })
  }

  function _init_card_click_handler() {
    $('.card-list').click(function(event) {

      let card = $(event.target).closest('.card-list-item')
      _click_state.clicks += 1

      if (_click_state.clicks == 1) {
        _click_state.timer = setTimeout(function() {
          _click_state.clicks = 0
          _click_state.timer = undefined

          dialogs.show('card-closeup', {
            card_id: cardui.id(card),
          })
          _redraw()
        }, _click_state.delay)
      }

      else {
        clearTimeout(_click_state.timer)
        _click_state.clicks = 0
        _click_state.timer = undefined

        cardui.twiddle(card)
        _redraw()
      }

    }).dblclick(function(event) {
      event.preventDefault();
    })
  }

  function _init_card_dragging() {
    $(".sortable").sortable({
      connectWith: '.card-list',
      placeholder: 'sortable-highlight',
      helper: 'clone',
      appendTo: '#drag-holder',
      start: function(e, ui) {
        ui.placeholder.height(ui.item.height())
        _card_drag_state.orig = $(e.target)
        _card_drag_state.oidx = ui.item.index()
        _card_drag_state.card = ui.item
      },
      update: function(e, ui) {
        _card_drag_state.dest = $(e.target)
        _card_drag_state.didx = ui.item.index()
      },
      stop: function(e, ui) {
        if (_card_drag_state.dest) {
          _move_card(
            _card_drag_state.orig,
            _card_drag_state.oidx,
            _card_drag_state.dest,
            _card_drag_state.didx,
            _card_drag_state.card,
          )
        }

        _card_drag_state.orig = undefined
        _card_drag_state.card = undefined
        _card_drag_state.oidx = undefined
        _card_drag_state.cidx = undefined
        _card_drag_state.dest = undefined
      }
    })
    $( ".sortable" ).disableSelection()
  }

  function _init_die_modal() {
    $('#die-roll').click(function() {
      let player_idx = parseInt($('#die-roller-player-idx').text())
      let player = _state.player(player_idx)

      let faces = parseInt($('#die-faces').val())
      let roll = Math.floor(Math.random() * faces) + 1
      _state.message(`Rolled ${roll} on a d${faces} for ${player.name}`)

      $('#die-roller').modal('hide')
      _redraw()
    })

    $('#die-faces').keydown(function(event) {
      if (event.keyCode === 13) {
        event.preventDefault()
        $('#die-roll').click()
      }
    })

  }

  function _init_history_navigation() {
    $('#messages').click(function(e) {
      _state.set_history_index($(e.target).index())
      _redraw()
    })
  }

  function _init_life_buttons() {
    $('.life-buttons').click(function(event) {
      let button = $(event.target)
      let amount = parseInt(button.attr('amount'))
      let player_idx = util.player_idx_from_elem(button.parent())
      _state.increment_life(player_idx, amount)
      _redraw()
    })
  }

  function _init_message_box() {
    $("#message-input").keyup(function(event) {
      if (event.keyCode === 13) {
        let input = $(this)
        _state.message(input.val())
        input.val('')
        _redraw()
      }
    })
  }

  function _init_phase_changes() {
    $('.phase').click(function(e) {
      let phase = $(e.target).attr('id')
      assert.ok(phase.startsWith('phase-'))

      _state.set_phase(phase.substring(6))
      _redraw()
    })
  }

  function _init_popup_menus() {
    // Populate all of the zone popup menus from the templates.
    $('.popup-menu-template').each(function() {
      let menu = $(this)
      let zone = menu.data('zone')

      for (var i = 0; i < _state.num_players(); i++) {
        let parent_id = `#player-${i}-${zone}`
        let parent = $(parent_id).find('.zone-menu-inner')
        assert.equal(parent.length, 1, `No zone menu found for id ${parent_id}`)

        let new_menu = menu.clone()
        new_menu.removeClass('popup-menu-template')
        new_menu.addClass(`popup-menu-${zone}`)

        parent.append(new_menu)
      }
    })

    // Open all popup menus on click
    $('.zone-menu-icon').click(function () {
      $(this).siblings('.popup-menu').show()
    })

    // Handle clicks on popup menus
    $('.popup-menu ul').click(_popup_menu_click_handler)

    // Close all popup menus on click
    window.addEventListener('click', function(event) {
      if (!event.target.matches('.zone-menu-icon')) {
        $(".popup-menu").hide()
      }
    })
  }

  function _init_card_closeup_interations() {
    let closeup = $('#card-closeup')

    closeup.on('clo.dialogs.closing', function() {
      _state.card_annotation(
        dialogs.data('card-closeup').card_id,
        closeup.find('.card-closeup-annotation-input').val(),
      )
      _redraw()
    })
  }

  function _init_token_maker_interactions() {
    $('#token-create').click(function() {
      let name = $('#token-name').val()
      let annotation = $('#token-annotation').val()

      let player_idx = dialogs.data('token-maker').player_idx
      let player = _state.player(player_idx)

      let token = _state.card_factory()
      token.annotation = annotation
      token.owner = player.name
      token.visibility = _state.state.players.map(p => p.name).sort()

      let data = token.json
      data.name = name
      data.type_line = 'Token'

      let front = data.card_faces[0]
      front.image_url = 'https://i.ibb.co/bBjMCHC/tc19-28-manifest.png'
      front.name = name
      front.type_line = 'Token'

      _state.card_create(token)
      _redraw()
    })
  }

  function _move_card(orig, oidx, dest, didx, card) {
    let source_index = card.data('source-index')

    // Update the game state to reflect the change.
    let orig_loc = _move_card_location_maker(orig, oidx, source_index)
    let dest_loc = _move_card_location_maker(dest, didx)
    let card_id = cardui.id(card)

    _state.move_card(orig_loc, dest_loc, card_id)
    _update_card_zone(orig_loc.player_idx, orig_loc.name)
    _update_card_zone(dest_loc.player_idx, dest_loc.name)
    _redraw()
  }

  function _move_card_location_maker(elem, index, source_index) {
    var elem_id = elem.attr('id')
    if (elem_id == 'popup-viewer-cards') {
      elem_id = dialogs.data(elem_id)

      if (source_index) {
        index = source_index
      }
    }

    let tokens = elem_id.split('-')
    return {
      player_idx: parseInt(tokens[1]),
      zone_idx: parseInt(index),
      name: tokens[2],
    }
  }

  function _popup_menu_click_handler(event) {
    let target = $(event.target)
    let menu_item = target.text()

    if (menu_item == 'collapse/expand') {
      let zone = target.closest('.card-zone')
      let player_idx = util.player_idx_from_elem(zone)
      _state.toggle_zone_collapse(player_idx, zone.attr('id'))
      _redraw()
    }

    else if (menu_item == 'create token') {
      let zone = target.closest('.card-zone')
      let player_idx = util.player_idx_from_elem(zone)
      dialogs.show('token-maker', {
        player_idx: player_idx,
      })
    }

    else if (menu_item == 'draw') {
      let zone = target.closest('.card-zone')
      let player_idx = util.player_idx_from_elem(zone)
      _state.draw(player_idx, 1)
      _redraw()
    }

    else if (menu_item == 'draw 7') {
      let zone = target.closest('.card-zone')
      let player_idx = util.player_idx_from_elem(zone)
      _state.draw(player_idx, 7)
      _redraw()
    }

    else if (menu_item == 'face-down/face-up') {
      let card_id = $('#card-closeup').data('card-id')
      _state.card_flip_down_up(card_id)
      _redraw()
    }

    else if (menu_item == 'roll a die') {
      let zone = target.closest('.card-zone')
      let player_idx = util.player_idx_from_elem(zone)
      $('#die-roller-player-idx').text(player_idx)
      $('#die-roller').modal('show')
    }

    else if (menu_item == 'shuffle') {
      let zone = target.closest('.card-zone')
      let player_idx = util.player_idx_from_elem(zone)
      _state.shuffle(player_idx)
      _redraw()
    }

    else if (menu_item == 'view') {
      let zone = target.closest('.card-zone')
      dialogs.show('popup-viewer-zone', {
        source_id: zone.attr('id')
      })
    }

    else {
      console.log(`Unknown menu item ${menu_item}`)
    }
  }

  function _redraw() {
    let root = $('.game-root')

    _update_phase()
    _update_turn_and_priority()

    for (var i = 0; i < _state.num_players(); i++) {
      _update_card_zone(i, 'battlefield')
      _update_card_zone(i, 'land')
      _update_card_zone(i, 'exile')
      _update_card_zone(i, 'graveyard')
      _update_card_zone(i, 'hand')
      _update_card_zone(i, 'library')
      _update_card_zone(i, 'sideboard')
      _update_card_zone(i, 'command')
      _update_card_zone(i, 'stack')
      _update_player_info(i)
      _update_history()
    }

    dialogs.redraw()
  }

  function _save() {
    $.ajax({
      type: 'POST',
      url: $('#save-game-meta').data('save-url'),
      data: JSON.stringify(_state.save_data()),
      contentType: "application/json; charset=utf-8",
      success: function() {
        _state.set_history_save_point()
        _redraw()
      },
      error: function(error_message) {
        alert('Error Saving Game')
      }
    })
  }

  function _update_card_zone(player_idx, zone) {
    assert.equal(typeof player_idx, 'number', `player_idx should be number, got ${player_idx}`)
    assert.equal(typeof zone, 'string', `zone should be string, got ${zone}`)

    let card_list = _state.card_list(player_idx, zone)
    let zone_prefix = _zone_prefix(player_idx, zone)
    let cards_elem = $(`${zone_prefix}-cards`)
    let count_elem = $(`${zone_prefix}-count`)

    assert.equal(cards_elem.length, 1)
    assert.equal(count_elem.length, 1)

    // Remove any old card data.
    cards_elem.empty()

    // Load up new card data.
    for (var i = 0; i < card_list.length; i++) {
      let card_id = card_list[i]
      let card = _state.card(card_id)
      cards_elem.append(cardui.factory(card))
    }

    // Fill in number of cards
    count_elem.text(card_list.length)

    let is_collapsed = _state.is_collapsed(_state.viewer_idx, zone_prefix)
    if (is_collapsed) {
      cards_elem.hide()
    }
    else {
      cards_elem.show()
    }
  }

  function _update_history() {
    let elem = $('#messages')
    let prev_message_count = elem.children().length

    elem.empty()

    for (var i = 0; i < _state.history.length; i++) {
      let hist = _state.history[i]
      let msg = $('<li></li>')
        .text(hist.message)
        .addClass('message')

      if (hist.player == _state.viewer_name) {
        msg.addClass('viewer-message')
      }
      else if (hist.player != 'GM') {
        msg.addClass('other-message')
      }

      if (i > _state.history_index) {
        msg.addClass('future-message')
      }

      if (i == _state.history_save_point) {
        msg.addClass('history-save-point')
      }

      elem.append(msg)
    }

    if (prev_message_count != elem.children().length) {
      elem.scrollTop(99999)
    }
  }

  function _update_phase() {
    let phase = _state.phase()

    // UI
    let phases = $('.phase')
    let current = $(`#phase-${phase}`)

    phases.removeClass('current-phase')
    current.addClass('current-phase')
  }

  function _update_player_info(player_idx) {
    let player = _state.player(player_idx)
    $(`#player-${player_idx}-name`).text(player.name)
    $(`#player-${player_idx}-life`).text(player.tableau.counters['life'])
  }

  function _update_turn_and_priority() {
    $('.tableau').removeClass('player-turn')
    $('.player-info').removeClass('player-priority')

    let turn_player_idx = _state.turn_player_idx()
    let priority_player_idx = _state.priority_player_idx()
    $(`#player-${turn_player_idx}-tableau`).addClass('player-turn')
    $(_zone_prefix(priority_player_idx, 'info')).addClass('player-priority')
  }

  function _zone_from_id(elem_id) {
    return elem_id.split('-')[2]
  }

  function _zone_prefix(player_idx, zone) {
    return `#player-${player_idx}-${zone}`
  }

  ////////////////////////////////////////////////////////////////////////////////
  // Public Interface

  let gameui = {
    init(game_state, viewing_player) {
      _state = new GameState(game_state, viewing_player)

      cardui.init(_state)
      dialogs.init(_state)

      // UI interactions
      _init_card_click_handler()
      _init_card_dragging()
      _init_die_modal()
      _init_life_buttons()
      _init_popup_menus()

      // Dialog interactiions
      _init_card_closeup_interations()
      _init_token_maker_interactions()

      // Player activites
      _init_actions()
      _init_phase_changes()
      _init_history_navigation()
      _init_message_box()

      _redraw()
    }
  }

  return gameui
}())


module.exports = gameui