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
    delay: 300,
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

    $('#start-turn').click(function() {
      _state.start_turn()
      _redraw()
    })
  }

  function _init_card_click_handler() {
    $('.card-list').click(function(event) {
      event.preventDefault()

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

        if (!_state.spectator) {
          cardui.twiddle(card)
          _redraw()
        }
      }

    }).dblclick(function(event) {
      event.preventDefault()
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
        var redraw = false;

        if (_card_drag_state.dest.hasClass('closeup-dropper')) {
          dialogs.show('card-closeup', {
            card_id: cardui.id(_card_drag_state.card),
          })
          redraw = true
        }

        else if (_card_drag_state.dest.hasClass('twiddle-dropper')) {
          cardui.twiddle(_card_drag_state.card)
          redraw = true
        }

        else if (_card_drag_state.dest) {
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

        if (redraw) {
          _redraw()
        }
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
      var target_msg = $(e.target)

      if (target_msg.tagName != 'li') {
        target_msg = target_msg.closest('li')
      }

      _state.set_history_index(target_msg.index())
      _redraw()
    })

    $(document).keyup(function(event) {
      let focus = $(document.activeElement).prop('tagName').toLowerCase()
      if (focus == 'input' || focus == 'textarea')
        return

      if (event.keyCode == 37) { // left arrow
        _state.set_history_index(_state.history_index - 1)
        _redraw()
      }
      else if (event.keyCode == 39) { // right arrow
        _state.set_history_index(_state.history_index + 1)
        _redraw()
      }
    })
  }

  function _init_library_move_modal() {
    // Populate possible destinations
    let library_move_dest_select = $('#library-move-dest')
    for (var i = 0; i < _state.num_players(); i++) {
      let player_name = _state.state.players[i].name

      let zone_meta_info = _state.zone_meta_info()
      for (let zone in zone_meta_info) {
        if (!zone_meta_info.hasOwnProperty(zone))
          continue

        let zone_id = `player-${i}-${zone}`
        let zone_name = `${player_name}'s ${zone}`
        let opt_elem = $(`<option value="${zone_id}">${zone_name}</option>`)
        library_move_dest_select.append(opt_elem)
      }
    }

    $('#library-move-submit').click(function() {
      let player_idx = parseInt($('#library-move-modal-player-idx').text())
      let dest_zone_id = $('#library-move-dest').val()
      let count = parseInt($('#library-move-count').val())
      let face_down = $('#library-move-face-down').is(':checked')

      _state.move_top_of_library_to(
        player_idx,
        util.player_idx_from_elem_id(dest_zone_id),
        _zone_from_id(dest_zone_id),
        count,
        face_down
      )

      $('#library-move-modal').modal('hide')
      _redraw()
    })

    $('#library-move-count').keydown(function(event) {
      if (event.keyCode === 13) {
        event.preventDefault()
        $('#library-move-submit').click()
      }
    })
  }

  function _init_life_buttons() {
    $('.life-buttons').click(function(event) {
      let button = $(event.target)
      let amount = parseInt(button.attr('amount'))
      let player_idx = util.player_idx_from_elem(button.parent())
      _state.increment_life(player_idx, amount)
      _update_player_info(player_idx)
      _update_history()
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

    // Hide menu icons with no child elements
    $('.zone-menu-inner').each(function(i, elem) {
      let jelem = $(elem)
      if (jelem.find('ul').length == 0) {
        jelem.find('.zone-menu-icon').hide()
      }
    })

    // Open all popup menus on click
    $('.zone-menu-icon').click(function () {
      let popup = $(this).siblings('.popup-menu').show()

      // Adjust position if off the edge of the screen.
      let popup_right = popup.offset().left + popup.outerWidth()
      let viewportRight = $(window).width() + $(window).scrollLeft() // Scroll left considers horizontal scrollbar

      if (popup_right < viewportRight) {
        popup.css('left', 0)
      }
      else {
        popup.css('right', 0)
      }
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

  function _init_randomize_bottom_modal() {
    $('#randomize-bottom-submit').click(function() {
      let player_idx = parseInt($('#randomize-bottom-modal-player-idx').text())
      let count = parseInt($('#randomize-bottom-count').val())

      _state.randomize_bottom_of_library(player_idx, count)

      $('#randomize-bottom-modal').modal('hide')
      _redraw()
    })

    $('#randomize-bottom-count').keydown(function(event) {
      if (event.keyCode === 13) {
        event.preventDefault()
        $('#randomize-bottom-submit').click()
      }
    })
  }

  function _init_scry_modal() {
    $('#scry-submit').click(function() {
      let player_idx = parseInt($('#scry-modal-player-idx').text())
      let count = parseInt($('#scry-count').val())

      _state.reveal_top_of_library_to(_state.viewer_idx, player_idx, count)

      $('#scry-modal').modal('hide')
      _redraw()
    })

    $('#scry-count').keydown(function(event) {
      if (event.keyCode === 13) {
        event.preventDefault()
        $('#scry-submit').click()
      }
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
      front.art_crop_url = 'https://i.ibb.co/bBjMCHC/tc19-28-manifest.png'
      front.name = name
      front.type_line = 'Token'

      _state.card_create(token, dialogs.data('token-maker').zone)
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
    _redraw()
  }

  // Source index is used when the card is moved by the viewer, rather than from a regular zone.
  function _move_card_location_maker(elem, index, source_index) {
    var elem_id = elem.attr('id')
    if (elem_id == 'popup-viewer-cards') {
      elem_id = dialogs.data('popup-viewer-zone').source_id

      if (source_index) {
        index = source_index
      }
    }

    if (elem_id.endsWith('-bottom')) {
      elem_id = elem_id.substr(0, elem_id.length - '-bottom'.length)
      index = '-1'
    }

    let tokens = elem_id.split('-')
    return {
      player_idx: parseInt(tokens[1]),
      zone_idx: parseInt(index),
      name: tokens[2],
    }
  }

  function _perform_message_styling(message) {
    const card_name_span = '<span class="message-card-name">CARD_NAME</span>'

    var msg = message
    if (msg.match(/^PLAYER_[0-9]_NAME: /)) {
      msg = `<span class="message-player-typed">${msg}</span>`
    }
    msg = msg.replace(/CARD_NAME/g, card_name_span)
    msg = msg.replace(/PLAYER_[0-9]_NAME/g, (match) => {
      return `<span class="message-player-name">${match}</span>`
    })

    return msg
  }

  function _perform_message_substitutions(hist, message) {
    var msg = message
    msg = msg.replace(/PLAYER_[0-9]_NAME/g, (match) => {
      let player_idx = parseInt(match.charAt(7))
      return _state.player(player_idx).name
    })

    if (msg.indexOf('CARD_NAME') >= 0) {
      let card = _state.card(hist.delta[0].card_id)
      let visibility = hist.delta[0].card_vis || 'UNKNOWN'

      var card_name = 'a card'
      let spectator_can_see = (
        visibility != 'UNKNOWN'
        && _state.spectator
        && visibility.length >= _state.num_players()
      )
      let player_can_see = (
        visibility != 'UNKNOWN'
        && visibility.indexOf(_state.viewer_name) >= 0
      )

      if (player_can_see || spectator_can_see) {
        card_name = card.json.name
      }

      msg = msg.replace(/CARD_NAME/g, card_name)
    }

    return msg
  }

  function _popup_menu_click_handler(event) {
    let target = $(event.target)
    let menu_item = target.text()

    if (menu_item == 'collapse/expand') {
      let zone = target.closest('.card-zone')
      let player_idx = _state.viewer_idx
      _state.toggle_zone_collapse(player_idx, zone.attr('id'))
      _redraw()
    }

    else if (menu_item == 'concede') {
      _state.concede(_state.viewer_idx)
      _redraw()
    }

    else if (menu_item == 'create token') {
      let zone = target.closest('.card-zone')
      let zone_name = _zone_from_id(zone.attr('id'))
      let player_idx = util.player_idx_from_elem(zone)
      dialogs.show('token-maker', {
        player_idx: player_idx,
        zone: zone_name,
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
      let card_id = dialogs.data('card-closeup').card_id
      _state.card_flip_down_up(card_id)
      _redraw()
    }

    else if (menu_item == 'mulligan') {
      let zone = target.closest('.card-zone')
      let player_idx = util.player_idx_from_elem(zone)
      _state.mulligan(player_idx)
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

    else if (menu_item == 'view top n') {
      let zone = target.closest('.card-zone')
      let player_idx = util.player_idx_from_elem(zone)
      $('#scry-modal-player-idx').text(player_idx)
      $('#scry-modal').modal('show')
    }

    else if (menu_item == 'move top n') {
      let zone = target.closest('.card-zone')
      let player_idx = util.player_idx_from_elem(zone)
      $('#library-move-modal-player-idx').text(player_idx)
      $('#library-move-modal').modal('show')
    }

    else if (menu_item == 'randomize bottom n') {
      let zone = target.closest('.card-zone')
      let player_idx = util.player_idx_from_elem(zone)
      $('#randomize-bottom-modal-player-idx').text(player_idx)
      $('#randomize-bottom-modal').modal('show')
    }

    else {
      console.log(`Unknown menu item ${menu_item}`)
    }
  }

  function _redraw() {
    let root = $('.game-root')

    _update_card_droppers()
    _update_phase()
    _update_turn_and_priority()
    _update_history()

    for (var i = 0; i < _state.num_players(); i++) {
      _update_card_zone(i, 'battlefield')
      _update_card_zone(i, 'creatures')
      _update_card_zone(i, 'land')
      _update_card_zone(i, 'exile')
      _update_card_zone(i, 'graveyard')
      _update_card_zone(i, 'hand')
      _update_card_zone(i, 'sideboard')
      _update_card_zone(i, 'command')
      _update_card_zone(i, 'stack')
      _update_player_info(i)
      _update_library(i)
    }

    dialogs.redraw()
  }

  function _save() {
    $.ajax({
      type: 'POST',
      url: $('#save-game-meta').data('save-url'),
      data: JSON.stringify(_state.save_data()),
      contentType: "application/json; charset=utf-8",
      success: function(response) {
        if (response == 'saved') {
          _state.set_history_save_point()
          _state.state.latest_version += 1
          _redraw()
        }
        else if (response == 'version conflict') {
          $('#error-title').text('Unable to Save')
          $('#error-message').text('Someone else has saved the game since you last downloaded the game data. Please reload the game in order to get the latest game data.')
          $('#error-modal').modal('show')
        }
        else {
          $('#error-title').text('Unable to Save')
          $('#error-message').text('Unknown save error')
          $('#error-modal').modal('show')
        }
      },
      error: function(error_message) {
        alert('Error Saving Game')
      }
    })
  }

  function _update_card_droppers() {
    $('.card-dropper').empty()
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
      let card = _state.card(card_list[i])
      let elem = cardui.factory(card)

      cardui.set_visibility(
        elem,
        _state.card_is_visible(card.id, zone_prefix),
        card.face_down,
      )

      if (zone == 'hand' && player_idx == _state.viewer_idx) {
        cardui.show_mana_cost(elem)
      }

      cards_elem.append(elem)
    }

    // Fill in number of cards
    count_elem.text(card_list.length)

    let is_collapsed = _state.is_collapsed(_state.viewer_idx, zone_prefix)
    if (is_collapsed) {
      cards_elem.children().hide()
    }
    else {
      cards_elem.children().show()
    }
  }

  function _update_library(player_idx) {
    let card_list = _state.card_list(player_idx, 'library')
    let zone_prefix = _zone_prefix(player_idx, 'library')

    let count_elem = $(`${zone_prefix}-count`)
    count_elem.text(card_list.length)

    let top_elem = $(`${zone_prefix}-cards`).empty()
    for (var i = 0; i < card_list.length; i++) {
      let card = _state.card(card_list[i])
      if (i == 0 || _state.card_is_visible(card.id, zone_prefix)) {
        let elem = cardui.factory(card)
        cardui.set_visibility(elem, _state.card_is_visible(card.id, zone_prefix))

        if (_state.card_is_revealed(card.id, zone_prefix)) {
          cardui.set_revealed(elem)
        }

        top_elem.append(elem)
      }

      else {
        break
      }
    }

    // Clear any cards that were dragged into the bottom of library
    $(`${zone_prefix}-cards-bottom`).empty()
  }

  function _update_history() {
    let elem = $('#messages')
    let messages = elem.children()
    let prev_message_count = elem.children().length

    if (!_state.history[0].id) {
      // No history ids means need to redraw the whole history.
      // Kept in place for existing games that didn't have history ids.
      elem.empty()
    }

    for (var i = 0; i < _state.history.length; i++) {
      let hist = _state.history[i]

      if (i < messages.length) {
        let msg = $(messages[i])
        let msg_id = msg.data('msg-id')
        if (msg.data('msg-id') == hist.id) {
          continue
        }
      }

      let message = _perform_message_substitutions(
        hist,
        _perform_message_styling(hist.message)
      )
      let message_html = $(`<span>${message}</span>`)

      let msg = $('<li></li>')
        .append(message_html)
        .addClass('message')
        .attr('data-msg-id', hist.id)

      if (hist.message.endsWith("'s turn")) {
        msg.addClass('new-turn-message')
      }
      else if (hist.message.endsWith("gets priority")) {
        msg.addClass('pass-priority-message')
      }
      else if (hist.message.startsWith('phase: ')) {
        msg.addClass('phase-message')
      }

      if (i > _state.history_index) {
        msg.addClass('future-message')
      }

      elem.append(msg)
    }

    // Trim off excess messages (typically due to undo action)
    if (_state.history.length < messages.length) {
      let num_to_cut = messages.length - _state.history.length
      console.log(`Cutting ${num_to_cut}`)
      messages.slice(-num_to_cut).remove()
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
      _init_card_click_handler()
      _init_history_navigation()

      if (!_state.spectator) {

        // UI interactions
        _init_card_closeup_interations()
        _init_card_dragging()
        _init_die_modal()
        _init_library_move_modal()
        _init_randomize_bottom_modal()
        _init_life_buttons()
        _init_popup_menus()
        _init_scry_modal()

        // Dialogs
        _init_token_maker_interactions()

        // Player activites
        _init_actions()
        _init_phase_changes()
        _init_message_box()
      }

      _redraw()
    }
  }

  return gameui
}())


module.exports = gameui
