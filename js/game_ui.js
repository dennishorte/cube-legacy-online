'use strict'

let assert = require('assert')

let GameState = require('./game_state.js')


let gameui = (function() {
  var _state

  let _card = {
    factory(data) {
      let card = $('<li></li>')
      _card.set_name(card, data.json.card_faces[0].name)
      card.attr('id', `card-${data.id}`)

      // Styling and autocard popup
      card.addClass('card-list-item')
      card.attr('data-front', data.json.card_faces[0].image_url)
      if (data.json.card_faces.length > 1) {
        card.attr('data-back', data.json.card_faces[1].image_url)
      }

      _card.set_annotation(card, data.annotation)
      _card.set_visibility(card, data)

      if (data.tapped) {
        card.addClass('tapped')
      }

      return card
    },

    id(elem) {
      return parseInt(elem.attr('id').split('-')[1])
    },

    is_tapped(elem) {
      let id = _card.id(elem)
      return _state.card(id).tapped
    },

    is_visible(data) {
      return data.visibility.includes(_state.viewer_name)
    },

    set_annotation(elem, text) {
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
    },

    set_name(elem, name) {
      var name_elem = elem.find('.card-name')

      if (name_elem.length == 0) {
        name_elem = $('<p class="card-name"></p>')
        elem.prepend(name_elem)
      }

      name_elem.text(name)
    },

    set_visibility(elem, data) {
      if (!_card.is_visible(data)) {
        elem.addClass('face-down')
      }
    },

    tap(elem) {
      // elem.addClass('tapped')  // Will happen during redraw
      let id = _card.id(elem)
      _state.twiddle(id)
    },

    untap(elem) {
      // elem.removeClass('tapped')  // Will happen during redraw
      let id = _card.id(elem)
      _state.twiddle(id)
    },
  }

  ////////////////////////////////////////////////////////////////////////////////
  // State

  let _card_drag_state = {
    orig: undefined,
    oidx: undefined,
    dest: undefined,
    didx: undefined,
    card: undefined,
  }

  let _popup_viewer_state = {
    active: false,
    source_id: undefined,
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

  function _init_double_click_for_tap() {
    $(".card-zone").dblclick(function(event) {
      let card = $(event.target).closest('.card-list-item')
      if (_card.is_tapped(card)) {
        _card.untap(card)
      }
      else {
        _card.tap(card)
      }
      _redraw()
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
      let player_idx = _player_idx_from_elem(button.parent())
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

        new_menu.find('li').click(_popup_menu_click_handler)

        parent.append(new_menu)

        parent.click(function () {
          $(this).find('.popup-menu').show()
        })
      }
    })

    window.addEventListener('click', function(event) {
      if (!event.target.matches('.zone-menu-icon')) {
        $(".popup-menu").hide()
      }
    })
  }

  function _init_popup_viewer() {
    $('#popup-viewer-zone').draggable({
      handle: '.card-section-header',
    })

    $('#popup-viewer-zone-close-button').click(function () {
      _popup_viewer_state.active = false
      _popup_viewer_state.source_id = undefined
      _redraw()
    })
  }

  function _move_card(orig, oidx, dest, didx, card) {
    let source_index = card.data('source-index')

    // Update the game state to reflect the change.
    let orig_loc = _move_card_location_maker(orig, oidx, source_index)
    let dest_loc = _move_card_location_maker(dest, didx)
    let card_id = _card.id(card)

    _state.move_card(orig_loc, dest_loc, card_id)
    _update_card_zone(orig_loc.player_idx, orig_loc.name)
    _update_card_zone(dest_loc.player_idx, dest_loc.name)
    _redraw()
  }

  function _move_card_location_maker(elem, index, source_index) {
    var elem_id = elem.attr('id')
    if (elem_id == 'popup-viewer-cards') {
      elem_id = _popup_viewer_state.source_id

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
    let zone = target.closest('.card-zone')
    let player_idx = _player_idx_from_elem(zone)

    if (menu_item == 'draw') {
      _state.draw(player_idx, 1)
      _redraw()
    }

    else if (menu_item == 'draw 7') {
      _state.draw(player_idx, 7)
      _redraw()
    }

    else if (menu_item == 'shuffle') {
      _state.shuffle(player_idx)
      _redraw()
    }

    else if (menu_item == 'view') {
      _popup_viewer_state.active = true
      _popup_viewer_state.source_id = zone.attr('id')
      _redraw()
    }

    else {
      console.log(`Unknown menu item ${menu_item}`)
    }
  }

  function _player_idx_from_elem(elem) {
    return _player_idx_from_id($(elem).attr('id'))
  }

  function _player_idx_from_id(id_string) {
    return id_string.split('-')[1]
  }

  function _redraw() {
    let root = $('.game-root')

    _update_turn_and_priority()
    _update_phase()
    _update_popup_viewer()

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
      cards_elem.append(_card.factory(card))
    }

    // Fill in number of cards
    count_elem.text(card_list.length)
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

  function _update_popup_viewer() {
    let popup = $('#popup-viewer-zone')

    if (!_popup_viewer_state.active) {
      popup.hide()
      return
    }
    else {
      popup.show()
    }

    assert.ok(_popup_viewer_state.source_id, "popup-viewer zone should have source id when active")

    let player_idx = _player_idx_from_id(_popup_viewer_state.source_id)
    let zone = $(`#${_popup_viewer_state.source_id}`)
    let zone_name = zone.find('.card-section-name').text().trim()
    let zone_id = zone_name.toLowerCase()

    popup.find('.card-section-header').text(zone_name)

    let card_list = $('#popup-viewer-cards')
    card_list.empty()

    let zone_card_ids = _state.player(player_idx).tableau[zone_id]
    for (var i = 0; i < zone_card_ids.length; i++) {
      let card_id = zone_card_ids[i]
      let card = _card.factory(_state.card(card_id))
      card.attr('data-source-index', i)
      card_list.append(card)
    }
  }

  function _update_turn_and_priority() {
    $('.tableau').removeClass('player-turn')
    $('.player-info').removeClass('player-priority')

    let turn_player_idx = _state.turn_player_idx()
    let priority_player_idx = _state.priority_player_idx()
    $(`#player-${turn_player_idx}-tableau`).addClass('player-turn')
    $(_zone_prefix(priority_player_idx, 'info')).addClass('player-priority')
  }

  function _zone_prefix(player_idx, zone) {
    return `#player-${player_idx}-${zone}`
  }

  ////////////////////////////////////////////////////////////////////////////////
  // Public Interface

  let gameui = {
    init(game_state, viewing_player) {
      _state = new GameState(game_state, viewing_player)

      // UI interactions
      _init_card_dragging()
      _init_double_click_for_tap()
      _init_life_buttons()
      _init_popup_menus()
      _init_popup_viewer()

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
