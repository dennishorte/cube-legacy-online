(function(f){if(typeof exports==="object"&&typeof module!=="undefined"){module.exports=f()}else if(typeof define==="function"&&define.amd){define([],f)}else{var g;if(typeof window!=="undefined"){g=window}else if(typeof global!=="undefined"){g=global}else if(typeof self!=="undefined"){g=self}else{g=this}g.ui = f()}})(function(){var define,module,exports;return (function(){function r(e,n,t){function o(i,f){if(!n[i]){if(!e[i]){var c="function"==typeof require&&require;if(!f&&c)return c(i,!0);if(u)return u(i,!0);var a=new Error("Cannot find module '"+i+"'");throw a.code="MODULE_NOT_FOUND",a}var p=n[i]={exports:{}};e[i][0].call(p.exports,function(r){var n=e[i][1][r];return o(n||r)},p,p.exports,r,e,n,t)}return n[i].exports}for(var u="function"==typeof require&&require,i=0;i<t.length;i++)o(t[i]);return o}return r})()({1:[function(require,module,exports){
'use strict'
let assert = require('assert')
let util = require('./util.js')


let card_zones = {
  battlefield: {
    visibility: 'all',
    taps: true,
  },
  land: {
    visibility: 'all',
    taps: true,
  },
  exile: {
    visibility: 'all',
    taps: false,
  },
  graveyard: {
    visibility: 'all',
    taps: false,
  },
  hand: {
    visibility: 'owner',
    taps: false,
  },
  library: {
    visiblity: 'none',
    taps: false,
  },
  sideboard: {
    visiblity: 'owner',
    taps: false,
  },
  stack: {
    visibility: 'all',
    taps: false,
  },
}


let phases = {
  untap: 'untap',
  upkeep: 'upkeep',
  draw: 'draw',
  main1: 'main1',
  combat_begin: 'combat-begin',
  combat_attack: 'combat-attack',
  combat_defend: 'combat-defend',
  combat_damage: 'combat-damage',
  combat_end: 'combat-end',
  main2: 'main2',
  end: 'end',
}


class GameState {
  constructor(state_in, viewer_name) {
    assert.ok(Array.isArray(state_in.history), "State requires a history")
    assert.ok(typeof viewer_name === 'string', "viewer_name should be a string")

    this.state = state_in
    this.history = state_in.history
    this.history_index = state_in.history.length - 1
    this.viewer_name = viewer_name
    this.viewer_idx = this.player_idx_by_name(viewer_name)
    this.history_save_point = this.history_index
  }

  ////////////////////////////////////////////////////////////////////////////////
  // Public Interface

  card(card_id) {
    return this.state.cards[card_id]
  }

  card_list(player_idx, zone_name) {
    return this.state.players[player_idx].tableau[zone_name]
  }

  draw(player_idx, count) {
    let player = this.state.players[player_idx]
    let library = player.tableau.library
    let hand = player.tableau.hand

    for (var i = 0; i < count; i++) {
      let card_id = library[0]
      let orig_loc = {
        name: 'library',
        zone_idx: 0,
        player_idx: player_idx,
      }
      let dest_loc = {
        name: 'hand',
        zone_idx: hand.length,
        player_idx: player_idx,
      }

      this.move_card(orig_loc, dest_loc, card_id)
    }
  }

  increment_life(player_idx, amount) {
    let player = this.state.players[player_idx]
    let counters = player.tableau.counters

    let diff = {
      delta: [{
        action: 'set_player_counter',
        key: 'life',
        player_idx: player_idx,
        old_value: counters.life,
        new_value: counters.life + amount,
      }],
      message: `${player.name} life change ${amount}`,
      player: this.viewer_name,
    }

    return this._execute(diff)
  }

  is_collapsed(player_idx, zone_id) {
    zone_id = this._clean_id(zone_id)
    let opt_name = `collapse_${zone_id}`
    return this.view_options(player_idx)[opt_name]
  }

  message(text) {
    let diff = {
      delta: [],
      message: `${this.viewer_name}: "${text}"`,
      player: this.viewer_name,
    }

    this._execute(diff)
  }

  move_card(orig_loc, dest_loc, card_id) {
    /* loc format:
     * zone = {
     *   name: 'hand',
     *   zone_idx: 0,
     *   player_idx: 0,
     * }
     */

    let delta = []

    delta.push({
      action: 'move_card',
      card_id: card_id,
      orig_loc: orig_loc,
      dest_loc: dest_loc,
    })

    let vis_diff = this._visibility_diff_from_move(orig_loc, dest_loc, this.card(card_id))
    if (vis_diff) {
      delta.push(vis_diff)
    }

    let diff = {
      delta: delta,
      message: `move card from ${orig_loc.name} to ${dest_loc.name}`,
      player: this.viewer_name,
    }

    return this._execute(diff)
  }

  num_players() {
    return this.state.players.length
  }

  pass_priority(execute=true) {
    let next_priority_idx = (this.priority_player_idx() + 1) % this.num_players()
    let delta = [{
      action: 'set_game_value',
      key: 'priority',
      old_value: this.priority_player_idx(),
      new_value: next_priority_idx,
    }]

    if (execute) {
      let player_name = this.player(next_priority_idx).name
      let diff = {
        delta: delta,
        message: `${player_name} gets priority`,
        player: 'GM',
      }

      return this._execute(diff)
    }
    else {
      return delta
    }
  }

  pass_turn() {
    let next_player_idx = (this.turn_player_idx() + 1) % this.num_players()
    var delta = [{
      action: 'set_game_value',
      key: 'turn',
      old_value: this.turn_player_idx(),
      new_value: next_player_idx,
    }]

    /* if (this.priority_player_idx() != next_player_idx) {
     *   delta = delta.concat(this.pass_priority(false))
     * } */

    let next_player_name = this.player(next_player_idx).name
    let diff = {
      delta: delta,
      message: `${next_player_name}'s turn`,
      player: 'GM',
    }

    this._execute(diff)
  }

  phase() {
    return this.state.phase
  }

  player(player_idx) {
    return this.state.players[player_idx]
  }

  player_idx_by_name(player_name) {
    for (var i = 0; i < this.state.players.length; i++) {
      if (this.state.players[i].name == player_name) {
        return i
      }
    }
  }

  priority_player_idx() {
    return this.state.priority
  }

  save_data() {
    return this.state
  }

  set_history_save_point() {
    this.history_save_point = this.history_index
  }

  set_history_index(index) {
    this._move_through_history(index)
  }

  set_phase(phase) {
    assert.ok(this._is_valid_phase(phase), `Invalid game phase: ${phase}`)

    if (this.phase() != phase) {
      let diff = {
        delta: [{
          action: 'set_game_value',
          key: 'phase',
          old_value: this.phase(),
          new_value: phase,
        }],
        message: `phase: ${phase}`,
        player: this.viewer_name
      }

      return this._execute(diff)
    }
  }

  shuffle(player_idx) {
    let player = this.state.players[player_idx]
    let library_copy = [...player.tableau.library]
    let library_new = [...library_copy]
    util.arrayShuffle(library_new)

    let delta = [{
      action: 'set_cards_in_zone',
      player_idx: player_idx,
      zone: 'library',
      old_value: library_copy,
      new_value: library_new,
    }]

    library_copy.forEach(card_id => {
      let card = this.card(card_id)
      if (card.visibility.length > 0) {
        delta.push(this._visibility_diff(card, []))
      }
    })

    let diff = {
      delta: delta,
      message: `${player.name} shuffles library`,
      player: this.viewer_game,
    }

    return this._execute(diff)
  }

  toggle_zone_collapse(player_idx, zone_id) {
    zone_id = this._clean_id(zone_id)

    let opt_name = `collapse_${zone_id}`


    if (this.is_collapsed(player_idx, zone_id)) {
      delete this.view_options(player_idx)[opt_name]
    }
    else {
      this.view_options(player_idx)[opt_name] = true
    }
  }

  turn_player_idx() {
    return this.state.turn
  }

  twiddle(card_id) {
    let card = this.card(card_id)
    let action = card.tapped ? 'untap': 'tap'

    let diff = {
      delta: [{
        action: 'set_card_value',
        card_id: card_id,
        key: 'tapped',
        old_value: card.tapped,
        new_value: !card.tapped,
      }],
      message: `${action}: ${card.json.name}`,
      player: this.viewer_name,
    }

    return this._execute(diff)
  }

  undo() {
    this._ensure_history_up_to_date()
    this._move_through_history(this.history_index - 1)
    this.history.splice(-1, 1)
  }

  view_options(player_idx) {
    let player = this.state.players[player_idx]
    if (!player.hasOwnProperty('view_options')) {
      player.view_options = {}
    }

    return player.view_options
  }

  ////////////////////////////////////////////////////////////////////////////////
  // Private Functions

  _card_list_from_loc(loc) {
    return this.card_list(loc.player_idx, loc.name)
  }

  _clear_visibility_diff(player_idx, zone, card) {

  }

  _clean_id(elem_id) {
    if (elem_id.startsWith('#')) {
      return elem_id.substr(1)
    }
    else {
      return elem_id
    }
  }

  _execute(diff) {
    this._ensure_history_up_to_date()
    this.history.push(diff)
    this._move_through_history(this.history.length - 1)
  }

  _ensure_history_up_to_date() {
    assert.ok(this.history_index + 1 == this.history.length, "History is not up-to-date")
  }

  _is_valid_phase(phase) {
    return Object.values(phases).indexOf(phase) > -1
  }

  _move_through_history(index) {
    assert.ok(index >= 0, "negative history index")
    assert.ok(index < this.history.length, "too large history index")

    let forward = index > this.history_index
    let increment = forward ? 1 : -1

    while (index != this.history_index) {
      if (forward) {
        this.history_index += increment
        this._apply(this.history[this.history_index])
      }
      else {
        this._unapply(this.history[this.history_index])
        this.history_index += increment
      }
    }
  }

  _visibility_diff(card, new_visibility) {
    return {
      action: 'set_visibility',
      card_id: card.id,
      vis: [...new_visibility].sort(),
      old: [...card.visibility]
    }
  }

  _visibility_diff_from_move(orig_loc, dest_loc, card) {
    let dest_visibility = card_zones[dest_loc.name].visibility

    let names_to_add = []

    if (dest_visibility == 'all') {
      names_to_add = this.state.players.map(player => player.name)
    }
    else if (dest_visibility == 'owner') {
      names_to_add.push(this.state.players[dest_loc.player_idx].name)
    }

    if (names_to_add.length > 0) {
      return this._visibility_diff(card, card.visibility.concat(names_to_add))
    }
    else {
      return undefined
    }
  }


  ////////////////////////////////////////////////////////////////////////////////
  // Apply and Unapply

  _apply(diff) {
    for (var i = 0; i < diff.delta.length; i++) {
      let change = diff.delta[i]
      let action = change.action

      if (action == 'move_card') {
        let card_id = change.card_id

        // Ensure the card exists where it is supposed to be.
        let orig_zone = this._card_list_from_loc(change.orig_loc)
        let orig_idx = change.orig_loc.zone_idx
        assert.equal(
          orig_zone[orig_idx], card_id,
          `Card ${card_id} not found at ${orig_idx} in ${change.orig_loc.name} ${orig_zone}`
        )

        // Remove the card from its existing zone
        orig_zone.splice(orig_idx, 1)

        // Add the card to the new zone.
        let dest_zone = this._card_list_from_loc(change.dest_loc)
        dest_zone.splice(change.dest_loc.zone_idx, 0, card_id)
      }

      else if (action == 'set_game_value') {
        let key = change.key
        assert.equal(
          this.state[key], change.old_value,
          `Change old value (${change.old_value}) doesn't match current value (${this.state[key]})`
        )
        this.state[key] = change.new_value
      }

      else if (action == 'set_card_value') {
        let card = this.card(change.card_id)
        let key = change.key
        assert.equal(
          card[key], change.old_value,
          "Change old value doesn't match current card value" +
          `card: ${card.id}:${card.json.name}, key: ${key}, ` +
          `change.old: ${change.old_value}, ${card[key]}`
        )

        card[key] = change.new_value
      }

      else if (action == 'set_cards_in_zone') {
        let tableau = this.state.players[change.player_idx].tableau
        assert.ok(util.arraysEqual(tableau[change.zone], change.old_value))

        tableau[change.zone] = [...change.new_value]
      }

      else if (action == 'set_player_counter') {
        let counters = this.state.players[change.player_idx].tableau.counters
        let key = change.key
        assert.equal(counters[key], change.old_value)

        counters[key] = change.new_value
      }

      else if (action == 'set_visibility') {
        let card = this.card(change.card_id)
        assert.ok(util.arraysEqual(card.visibility, change.old), "Original visibility does not match")

        card.visibility = [...change.vis]
      }

      else {
        throw `Unknown action ${action}`
      }
    }
  }

  _unapply(diff) {
    // Make a copy so that we don't alter the original diff.
    let inverse = JSON.parse(JSON.stringify(diff));

    // Reverse the order of the delta so they will be unapplied in reverse order of application.
    let delta = inverse.delta
    delta.reverse()

    // Invert each change in the delta
    for (var i = 0; i < delta.length; i++) {
      let change = delta[i]
      let action = change.action

      if (action == 'set_game_value'
          || action == 'set_card_value'
          || action == 'set_cards_in_zone'
          || action == 'set_player_counter'
      ) {
        let tmp = change.old_value
        change.old_value = change.new_value
        change.new_value = tmp
      }

      else if (action == 'move_card') {
        let tmp = change.orig_loc
        change.orig_loc = change.dest_loc
        change.dest_loc = tmp
      }

      else if (action == 'set_visibility') {
        let tmp = change.vis
        change.vis = change.old
        change.old = tmp
      }

      else {
        throw `Unknown action ${action}`
      }
    }

    // Apply the inverted diff
    this._apply(inverse)
  }

}

module.exports = GameState

},{"./util.js":3,"assert":4}],2:[function(require,module,exports){
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

    twiddle(elem) {
      let id = _card.id(elem)
      _state.twiddle(id)
    },
  }

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

  let _popup_viewer_state = {
    active: false,
    source_id: undefined,
  }

  let _card_closeup_state = {
    active: true,
    card_id: 1,
  }

  ////////////////////////////////////////////////////////////////////////////////
  // Functions

  function _card_closeup(card) {
    _card_closeup_state.active = true
    _card_closeup_state.card_id = _card.id(card)
  }

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

          _card_closeup(card)
          _redraw()
        }, _click_state.delay)
      }

      else {
        clearTimeout(_click_state.timer)
        _click_state.clicks = 0
        _click_state.timer = undefined

        _card.twiddle(card)
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

  function _init_popup_views() {
    $('#popup-viewer-zone').draggable({
      handle: '.card-section-header',
    })

    $('#popup-viewer-zone-close-button').click(function () {
      _popup_viewer_state.active = false
      _popup_viewer_state.source_id = undefined
      _redraw()
    })


    $('#card-closeup').draggable({
      handle: '.card-section-header',
    })

    $('#card-closeup-close-button').click(function () {
      _card_closeup_state.active = false
      _card_closeup_state.source_id = undefined
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
    let zone_name = _zone_from_id(zone.attr('id'))
    let player_idx = _player_idx_from_elem(zone)

    if (menu_item == 'collapse/expand') {
      _state.toggle_zone_collapse(player_idx, zone.attr('id'))
      _redraw()
    }

    else if (menu_item == 'draw') {
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

    _update_card_closeup()
    _update_phase()
    _update_popup_viewer()
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

  function _update_card_closeup() {
    let closeup = $('#card-closeup')

    if (!_card_closeup_state.active) {
      closeup.hide()
      return
    }
    else {
      closeup.show()
      assert.ok(
        _card_closeup_state.card_id,
        "card closeup should have source id when active"
      )
    }

    let data = _state.card(_card_closeup_state.card_id).json
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

      // UI interactions
      _init_card_click_handler()
      _init_card_dragging()
      _init_life_buttons()
      _init_popup_menus()
      _init_popup_views()

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

},{"./game_state.js":1,"assert":4}],3:[function(require,module,exports){

let util = {}

util.arraysEqual = function(a, b) {
  if (a === b) return true;
  if (a == null || b == null) return false;
  if (a.length !== b.length) return false;

  // If you don't care about the order of the elements inside
  // the array, you should sort both arrays here.
  // Please note that calling sort on an array will modify that array.
  // you might want to clone your array first.


  for (var i = 0; i < a.length; ++i) {
    if (a[i] !== b[i]) return false;
  }
  return true;
}


util.arrayShuffle = function(array) {
  var currentIndex = array.length, temporaryValue, randomIndex;

  // While there remain elements to shuffle...
  while (0 !== currentIndex) {

    // Pick a remaining element...
    randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex -= 1;

    // And swap it with the current element.
    temporaryValue = array[currentIndex];
    array[currentIndex] = array[randomIndex];
    array[randomIndex] = temporaryValue;
  }

  return array;
}


module.exports = util

},{}],4:[function(require,module,exports){
(function (global){(function (){
'use strict';

var objectAssign = require('object-assign');

// compare and isBuffer taken from https://github.com/feross/buffer/blob/680e9e5e488f22aac27599a57dc844a6315928dd/index.js
// original notice:

/*!
 * The buffer module from node.js, for the browser.
 *
 * @author   Feross Aboukhadijeh <feross@feross.org> <http://feross.org>
 * @license  MIT
 */
function compare(a, b) {
  if (a === b) {
    return 0;
  }

  var x = a.length;
  var y = b.length;

  for (var i = 0, len = Math.min(x, y); i < len; ++i) {
    if (a[i] !== b[i]) {
      x = a[i];
      y = b[i];
      break;
    }
  }

  if (x < y) {
    return -1;
  }
  if (y < x) {
    return 1;
  }
  return 0;
}
function isBuffer(b) {
  if (global.Buffer && typeof global.Buffer.isBuffer === 'function') {
    return global.Buffer.isBuffer(b);
  }
  return !!(b != null && b._isBuffer);
}

// based on node assert, original notice:
// NB: The URL to the CommonJS spec is kept just for tradition.
//     node-assert has evolved a lot since then, both in API and behavior.

// http://wiki.commonjs.org/wiki/Unit_Testing/1.0
//
// THIS IS NOT TESTED NOR LIKELY TO WORK OUTSIDE V8!
//
// Originally from narwhal.js (http://narwhaljs.org)
// Copyright (c) 2009 Thomas Robinson <280north.com>
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the 'Software'), to
// deal in the Software without restriction, including without limitation the
// rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
// sell copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
// ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
// WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

var util = require('util/');
var hasOwn = Object.prototype.hasOwnProperty;
var pSlice = Array.prototype.slice;
var functionsHaveNames = (function () {
  return function foo() {}.name === 'foo';
}());
function pToString (obj) {
  return Object.prototype.toString.call(obj);
}
function isView(arrbuf) {
  if (isBuffer(arrbuf)) {
    return false;
  }
  if (typeof global.ArrayBuffer !== 'function') {
    return false;
  }
  if (typeof ArrayBuffer.isView === 'function') {
    return ArrayBuffer.isView(arrbuf);
  }
  if (!arrbuf) {
    return false;
  }
  if (arrbuf instanceof DataView) {
    return true;
  }
  if (arrbuf.buffer && arrbuf.buffer instanceof ArrayBuffer) {
    return true;
  }
  return false;
}
// 1. The assert module provides functions that throw
// AssertionError's when particular conditions are not met. The
// assert module must conform to the following interface.

var assert = module.exports = ok;

// 2. The AssertionError is defined in assert.
// new assert.AssertionError({ message: message,
//                             actual: actual,
//                             expected: expected })

var regex = /\s*function\s+([^\(\s]*)\s*/;
// based on https://github.com/ljharb/function.prototype.name/blob/adeeeec8bfcc6068b187d7d9fb3d5bb1d3a30899/implementation.js
function getName(func) {
  if (!util.isFunction(func)) {
    return;
  }
  if (functionsHaveNames) {
    return func.name;
  }
  var str = func.toString();
  var match = str.match(regex);
  return match && match[1];
}
assert.AssertionError = function AssertionError(options) {
  this.name = 'AssertionError';
  this.actual = options.actual;
  this.expected = options.expected;
  this.operator = options.operator;
  if (options.message) {
    this.message = options.message;
    this.generatedMessage = false;
  } else {
    this.message = getMessage(this);
    this.generatedMessage = true;
  }
  var stackStartFunction = options.stackStartFunction || fail;
  if (Error.captureStackTrace) {
    Error.captureStackTrace(this, stackStartFunction);
  } else {
    // non v8 browsers so we can have a stacktrace
    var err = new Error();
    if (err.stack) {
      var out = err.stack;

      // try to strip useless frames
      var fn_name = getName(stackStartFunction);
      var idx = out.indexOf('\n' + fn_name);
      if (idx >= 0) {
        // once we have located the function frame
        // we need to strip out everything before it (and its line)
        var next_line = out.indexOf('\n', idx + 1);
        out = out.substring(next_line + 1);
      }

      this.stack = out;
    }
  }
};

// assert.AssertionError instanceof Error
util.inherits(assert.AssertionError, Error);

function truncate(s, n) {
  if (typeof s === 'string') {
    return s.length < n ? s : s.slice(0, n);
  } else {
    return s;
  }
}
function inspect(something) {
  if (functionsHaveNames || !util.isFunction(something)) {
    return util.inspect(something);
  }
  var rawname = getName(something);
  var name = rawname ? ': ' + rawname : '';
  return '[Function' +  name + ']';
}
function getMessage(self) {
  return truncate(inspect(self.actual), 128) + ' ' +
         self.operator + ' ' +
         truncate(inspect(self.expected), 128);
}

// At present only the three keys mentioned above are used and
// understood by the spec. Implementations or sub modules can pass
// other keys to the AssertionError's constructor - they will be
// ignored.

// 3. All of the following functions must throw an AssertionError
// when a corresponding condition is not met, with a message that
// may be undefined if not provided.  All assertion methods provide
// both the actual and expected values to the assertion error for
// display purposes.

function fail(actual, expected, message, operator, stackStartFunction) {
  throw new assert.AssertionError({
    message: message,
    actual: actual,
    expected: expected,
    operator: operator,
    stackStartFunction: stackStartFunction
  });
}

// EXTENSION! allows for well behaved errors defined elsewhere.
assert.fail = fail;

// 4. Pure assertion tests whether a value is truthy, as determined
// by !!guard.
// assert.ok(guard, message_opt);
// This statement is equivalent to assert.equal(true, !!guard,
// message_opt);. To test strictly for the value true, use
// assert.strictEqual(true, guard, message_opt);.

function ok(value, message) {
  if (!value) fail(value, true, message, '==', assert.ok);
}
assert.ok = ok;

// 5. The equality assertion tests shallow, coercive equality with
// ==.
// assert.equal(actual, expected, message_opt);

assert.equal = function equal(actual, expected, message) {
  if (actual != expected) fail(actual, expected, message, '==', assert.equal);
};

// 6. The non-equality assertion tests for whether two objects are not equal
// with != assert.notEqual(actual, expected, message_opt);

assert.notEqual = function notEqual(actual, expected, message) {
  if (actual == expected) {
    fail(actual, expected, message, '!=', assert.notEqual);
  }
};

// 7. The equivalence assertion tests a deep equality relation.
// assert.deepEqual(actual, expected, message_opt);

assert.deepEqual = function deepEqual(actual, expected, message) {
  if (!_deepEqual(actual, expected, false)) {
    fail(actual, expected, message, 'deepEqual', assert.deepEqual);
  }
};

assert.deepStrictEqual = function deepStrictEqual(actual, expected, message) {
  if (!_deepEqual(actual, expected, true)) {
    fail(actual, expected, message, 'deepStrictEqual', assert.deepStrictEqual);
  }
};

function _deepEqual(actual, expected, strict, memos) {
  // 7.1. All identical values are equivalent, as determined by ===.
  if (actual === expected) {
    return true;
  } else if (isBuffer(actual) && isBuffer(expected)) {
    return compare(actual, expected) === 0;

  // 7.2. If the expected value is a Date object, the actual value is
  // equivalent if it is also a Date object that refers to the same time.
  } else if (util.isDate(actual) && util.isDate(expected)) {
    return actual.getTime() === expected.getTime();

  // 7.3 If the expected value is a RegExp object, the actual value is
  // equivalent if it is also a RegExp object with the same source and
  // properties (`global`, `multiline`, `lastIndex`, `ignoreCase`).
  } else if (util.isRegExp(actual) && util.isRegExp(expected)) {
    return actual.source === expected.source &&
           actual.global === expected.global &&
           actual.multiline === expected.multiline &&
           actual.lastIndex === expected.lastIndex &&
           actual.ignoreCase === expected.ignoreCase;

  // 7.4. Other pairs that do not both pass typeof value == 'object',
  // equivalence is determined by ==.
  } else if ((actual === null || typeof actual !== 'object') &&
             (expected === null || typeof expected !== 'object')) {
    return strict ? actual === expected : actual == expected;

  // If both values are instances of typed arrays, wrap their underlying
  // ArrayBuffers in a Buffer each to increase performance
  // This optimization requires the arrays to have the same type as checked by
  // Object.prototype.toString (aka pToString). Never perform binary
  // comparisons for Float*Arrays, though, since e.g. +0 === -0 but their
  // bit patterns are not identical.
  } else if (isView(actual) && isView(expected) &&
             pToString(actual) === pToString(expected) &&
             !(actual instanceof Float32Array ||
               actual instanceof Float64Array)) {
    return compare(new Uint8Array(actual.buffer),
                   new Uint8Array(expected.buffer)) === 0;

  // 7.5 For all other Object pairs, including Array objects, equivalence is
  // determined by having the same number of owned properties (as verified
  // with Object.prototype.hasOwnProperty.call), the same set of keys
  // (although not necessarily the same order), equivalent values for every
  // corresponding key, and an identical 'prototype' property. Note: this
  // accounts for both named and indexed properties on Arrays.
  } else if (isBuffer(actual) !== isBuffer(expected)) {
    return false;
  } else {
    memos = memos || {actual: [], expected: []};

    var actualIndex = memos.actual.indexOf(actual);
    if (actualIndex !== -1) {
      if (actualIndex === memos.expected.indexOf(expected)) {
        return true;
      }
    }

    memos.actual.push(actual);
    memos.expected.push(expected);

    return objEquiv(actual, expected, strict, memos);
  }
}

function isArguments(object) {
  return Object.prototype.toString.call(object) == '[object Arguments]';
}

function objEquiv(a, b, strict, actualVisitedObjects) {
  if (a === null || a === undefined || b === null || b === undefined)
    return false;
  // if one is a primitive, the other must be same
  if (util.isPrimitive(a) || util.isPrimitive(b))
    return a === b;
  if (strict && Object.getPrototypeOf(a) !== Object.getPrototypeOf(b))
    return false;
  var aIsArgs = isArguments(a);
  var bIsArgs = isArguments(b);
  if ((aIsArgs && !bIsArgs) || (!aIsArgs && bIsArgs))
    return false;
  if (aIsArgs) {
    a = pSlice.call(a);
    b = pSlice.call(b);
    return _deepEqual(a, b, strict);
  }
  var ka = objectKeys(a);
  var kb = objectKeys(b);
  var key, i;
  // having the same number of owned properties (keys incorporates
  // hasOwnProperty)
  if (ka.length !== kb.length)
    return false;
  //the same set of keys (although not necessarily the same order),
  ka.sort();
  kb.sort();
  //~~~cheap key test
  for (i = ka.length - 1; i >= 0; i--) {
    if (ka[i] !== kb[i])
      return false;
  }
  //equivalent values for every corresponding key, and
  //~~~possibly expensive deep test
  for (i = ka.length - 1; i >= 0; i--) {
    key = ka[i];
    if (!_deepEqual(a[key], b[key], strict, actualVisitedObjects))
      return false;
  }
  return true;
}

// 8. The non-equivalence assertion tests for any deep inequality.
// assert.notDeepEqual(actual, expected, message_opt);

assert.notDeepEqual = function notDeepEqual(actual, expected, message) {
  if (_deepEqual(actual, expected, false)) {
    fail(actual, expected, message, 'notDeepEqual', assert.notDeepEqual);
  }
};

assert.notDeepStrictEqual = notDeepStrictEqual;
function notDeepStrictEqual(actual, expected, message) {
  if (_deepEqual(actual, expected, true)) {
    fail(actual, expected, message, 'notDeepStrictEqual', notDeepStrictEqual);
  }
}


// 9. The strict equality assertion tests strict equality, as determined by ===.
// assert.strictEqual(actual, expected, message_opt);

assert.strictEqual = function strictEqual(actual, expected, message) {
  if (actual !== expected) {
    fail(actual, expected, message, '===', assert.strictEqual);
  }
};

// 10. The strict non-equality assertion tests for strict inequality, as
// determined by !==.  assert.notStrictEqual(actual, expected, message_opt);

assert.notStrictEqual = function notStrictEqual(actual, expected, message) {
  if (actual === expected) {
    fail(actual, expected, message, '!==', assert.notStrictEqual);
  }
};

function expectedException(actual, expected) {
  if (!actual || !expected) {
    return false;
  }

  if (Object.prototype.toString.call(expected) == '[object RegExp]') {
    return expected.test(actual);
  }

  try {
    if (actual instanceof expected) {
      return true;
    }
  } catch (e) {
    // Ignore.  The instanceof check doesn't work for arrow functions.
  }

  if (Error.isPrototypeOf(expected)) {
    return false;
  }

  return expected.call({}, actual) === true;
}

function _tryBlock(block) {
  var error;
  try {
    block();
  } catch (e) {
    error = e;
  }
  return error;
}

function _throws(shouldThrow, block, expected, message) {
  var actual;

  if (typeof block !== 'function') {
    throw new TypeError('"block" argument must be a function');
  }

  if (typeof expected === 'string') {
    message = expected;
    expected = null;
  }

  actual = _tryBlock(block);

  message = (expected && expected.name ? ' (' + expected.name + ').' : '.') +
            (message ? ' ' + message : '.');

  if (shouldThrow && !actual) {
    fail(actual, expected, 'Missing expected exception' + message);
  }

  var userProvidedMessage = typeof message === 'string';
  var isUnwantedException = !shouldThrow && util.isError(actual);
  var isUnexpectedException = !shouldThrow && actual && !expected;

  if ((isUnwantedException &&
      userProvidedMessage &&
      expectedException(actual, expected)) ||
      isUnexpectedException) {
    fail(actual, expected, 'Got unwanted exception' + message);
  }

  if ((shouldThrow && actual && expected &&
      !expectedException(actual, expected)) || (!shouldThrow && actual)) {
    throw actual;
  }
}

// 11. Expected to throw an error:
// assert.throws(block, Error_opt, message_opt);

assert.throws = function(block, /*optional*/error, /*optional*/message) {
  _throws(true, block, error, message);
};

// EXTENSION! This is annoying to write outside this module.
assert.doesNotThrow = function(block, /*optional*/error, /*optional*/message) {
  _throws(false, block, error, message);
};

assert.ifError = function(err) { if (err) throw err; };

// Expose a strict only variant of assert
function strict(value, message) {
  if (!value) fail(value, true, message, '==', strict);
}
assert.strict = objectAssign(strict, assert, {
  equal: assert.strictEqual,
  deepEqual: assert.deepStrictEqual,
  notEqual: assert.notStrictEqual,
  notDeepEqual: assert.notDeepStrictEqual
});
assert.strict.strict = assert.strict;

var objectKeys = Object.keys || function (obj) {
  var keys = [];
  for (var key in obj) {
    if (hasOwn.call(obj, key)) keys.push(key);
  }
  return keys;
};

}).call(this)}).call(this,typeof global !== "undefined" ? global : typeof self !== "undefined" ? self : typeof window !== "undefined" ? window : {})
},{"object-assign":8,"util/":7}],5:[function(require,module,exports){
if (typeof Object.create === 'function') {
  // implementation from standard node.js 'util' module
  module.exports = function inherits(ctor, superCtor) {
    ctor.super_ = superCtor
    ctor.prototype = Object.create(superCtor.prototype, {
      constructor: {
        value: ctor,
        enumerable: false,
        writable: true,
        configurable: true
      }
    });
  };
} else {
  // old school shim for old browsers
  module.exports = function inherits(ctor, superCtor) {
    ctor.super_ = superCtor
    var TempCtor = function () {}
    TempCtor.prototype = superCtor.prototype
    ctor.prototype = new TempCtor()
    ctor.prototype.constructor = ctor
  }
}

},{}],6:[function(require,module,exports){
module.exports = function isBuffer(arg) {
  return arg && typeof arg === 'object'
    && typeof arg.copy === 'function'
    && typeof arg.fill === 'function'
    && typeof arg.readUInt8 === 'function';
}
},{}],7:[function(require,module,exports){
(function (process,global){(function (){
// Copyright Joyent, Inc. and other Node contributors.
//
// Permission is hereby granted, free of charge, to any person obtaining a
// copy of this software and associated documentation files (the
// "Software"), to deal in the Software without restriction, including
// without limitation the rights to use, copy, modify, merge, publish,
// distribute, sublicense, and/or sell copies of the Software, and to permit
// persons to whom the Software is furnished to do so, subject to the
// following conditions:
//
// The above copyright notice and this permission notice shall be included
// in all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
// OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
// MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
// NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
// DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
// OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
// USE OR OTHER DEALINGS IN THE SOFTWARE.

var formatRegExp = /%[sdj%]/g;
exports.format = function(f) {
  if (!isString(f)) {
    var objects = [];
    for (var i = 0; i < arguments.length; i++) {
      objects.push(inspect(arguments[i]));
    }
    return objects.join(' ');
  }

  var i = 1;
  var args = arguments;
  var len = args.length;
  var str = String(f).replace(formatRegExp, function(x) {
    if (x === '%%') return '%';
    if (i >= len) return x;
    switch (x) {
      case '%s': return String(args[i++]);
      case '%d': return Number(args[i++]);
      case '%j':
        try {
          return JSON.stringify(args[i++]);
        } catch (_) {
          return '[Circular]';
        }
      default:
        return x;
    }
  });
  for (var x = args[i]; i < len; x = args[++i]) {
    if (isNull(x) || !isObject(x)) {
      str += ' ' + x;
    } else {
      str += ' ' + inspect(x);
    }
  }
  return str;
};


// Mark that a method should not be used.
// Returns a modified function which warns once by default.
// If --no-deprecation is set, then it is a no-op.
exports.deprecate = function(fn, msg) {
  // Allow for deprecating things in the process of starting up.
  if (isUndefined(global.process)) {
    return function() {
      return exports.deprecate(fn, msg).apply(this, arguments);
    };
  }

  if (process.noDeprecation === true) {
    return fn;
  }

  var warned = false;
  function deprecated() {
    if (!warned) {
      if (process.throwDeprecation) {
        throw new Error(msg);
      } else if (process.traceDeprecation) {
        console.trace(msg);
      } else {
        console.error(msg);
      }
      warned = true;
    }
    return fn.apply(this, arguments);
  }

  return deprecated;
};


var debugs = {};
var debugEnviron;
exports.debuglog = function(set) {
  if (isUndefined(debugEnviron))
    debugEnviron = process.env.NODE_DEBUG || '';
  set = set.toUpperCase();
  if (!debugs[set]) {
    if (new RegExp('\\b' + set + '\\b', 'i').test(debugEnviron)) {
      var pid = process.pid;
      debugs[set] = function() {
        var msg = exports.format.apply(exports, arguments);
        console.error('%s %d: %s', set, pid, msg);
      };
    } else {
      debugs[set] = function() {};
    }
  }
  return debugs[set];
};


/**
 * Echos the value of a value. Trys to print the value out
 * in the best way possible given the different types.
 *
 * @param {Object} obj The object to print out.
 * @param {Object} opts Optional options object that alters the output.
 */
/* legacy: obj, showHidden, depth, colors*/
function inspect(obj, opts) {
  // default options
  var ctx = {
    seen: [],
    stylize: stylizeNoColor
  };
  // legacy...
  if (arguments.length >= 3) ctx.depth = arguments[2];
  if (arguments.length >= 4) ctx.colors = arguments[3];
  if (isBoolean(opts)) {
    // legacy...
    ctx.showHidden = opts;
  } else if (opts) {
    // got an "options" object
    exports._extend(ctx, opts);
  }
  // set default options
  if (isUndefined(ctx.showHidden)) ctx.showHidden = false;
  if (isUndefined(ctx.depth)) ctx.depth = 2;
  if (isUndefined(ctx.colors)) ctx.colors = false;
  if (isUndefined(ctx.customInspect)) ctx.customInspect = true;
  if (ctx.colors) ctx.stylize = stylizeWithColor;
  return formatValue(ctx, obj, ctx.depth);
}
exports.inspect = inspect;


// http://en.wikipedia.org/wiki/ANSI_escape_code#graphics
inspect.colors = {
  'bold' : [1, 22],
  'italic' : [3, 23],
  'underline' : [4, 24],
  'inverse' : [7, 27],
  'white' : [37, 39],
  'grey' : [90, 39],
  'black' : [30, 39],
  'blue' : [34, 39],
  'cyan' : [36, 39],
  'green' : [32, 39],
  'magenta' : [35, 39],
  'red' : [31, 39],
  'yellow' : [33, 39]
};

// Don't use 'blue' not visible on cmd.exe
inspect.styles = {
  'special': 'cyan',
  'number': 'yellow',
  'boolean': 'yellow',
  'undefined': 'grey',
  'null': 'bold',
  'string': 'green',
  'date': 'magenta',
  // "name": intentionally not styling
  'regexp': 'red'
};


function stylizeWithColor(str, styleType) {
  var style = inspect.styles[styleType];

  if (style) {
    return '\u001b[' + inspect.colors[style][0] + 'm' + str +
           '\u001b[' + inspect.colors[style][1] + 'm';
  } else {
    return str;
  }
}


function stylizeNoColor(str, styleType) {
  return str;
}


function arrayToHash(array) {
  var hash = {};

  array.forEach(function(val, idx) {
    hash[val] = true;
  });

  return hash;
}


function formatValue(ctx, value, recurseTimes) {
  // Provide a hook for user-specified inspect functions.
  // Check that value is an object with an inspect function on it
  if (ctx.customInspect &&
      value &&
      isFunction(value.inspect) &&
      // Filter out the util module, it's inspect function is special
      value.inspect !== exports.inspect &&
      // Also filter out any prototype objects using the circular check.
      !(value.constructor && value.constructor.prototype === value)) {
    var ret = value.inspect(recurseTimes, ctx);
    if (!isString(ret)) {
      ret = formatValue(ctx, ret, recurseTimes);
    }
    return ret;
  }

  // Primitive types cannot have properties
  var primitive = formatPrimitive(ctx, value);
  if (primitive) {
    return primitive;
  }

  // Look up the keys of the object.
  var keys = Object.keys(value);
  var visibleKeys = arrayToHash(keys);

  if (ctx.showHidden) {
    keys = Object.getOwnPropertyNames(value);
  }

  // IE doesn't make error fields non-enumerable
  // http://msdn.microsoft.com/en-us/library/ie/dww52sbt(v=vs.94).aspx
  if (isError(value)
      && (keys.indexOf('message') >= 0 || keys.indexOf('description') >= 0)) {
    return formatError(value);
  }

  // Some type of object without properties can be shortcutted.
  if (keys.length === 0) {
    if (isFunction(value)) {
      var name = value.name ? ': ' + value.name : '';
      return ctx.stylize('[Function' + name + ']', 'special');
    }
    if (isRegExp(value)) {
      return ctx.stylize(RegExp.prototype.toString.call(value), 'regexp');
    }
    if (isDate(value)) {
      return ctx.stylize(Date.prototype.toString.call(value), 'date');
    }
    if (isError(value)) {
      return formatError(value);
    }
  }

  var base = '', array = false, braces = ['{', '}'];

  // Make Array say that they are Array
  if (isArray(value)) {
    array = true;
    braces = ['[', ']'];
  }

  // Make functions say that they are functions
  if (isFunction(value)) {
    var n = value.name ? ': ' + value.name : '';
    base = ' [Function' + n + ']';
  }

  // Make RegExps say that they are RegExps
  if (isRegExp(value)) {
    base = ' ' + RegExp.prototype.toString.call(value);
  }

  // Make dates with properties first say the date
  if (isDate(value)) {
    base = ' ' + Date.prototype.toUTCString.call(value);
  }

  // Make error with message first say the error
  if (isError(value)) {
    base = ' ' + formatError(value);
  }

  if (keys.length === 0 && (!array || value.length == 0)) {
    return braces[0] + base + braces[1];
  }

  if (recurseTimes < 0) {
    if (isRegExp(value)) {
      return ctx.stylize(RegExp.prototype.toString.call(value), 'regexp');
    } else {
      return ctx.stylize('[Object]', 'special');
    }
  }

  ctx.seen.push(value);

  var output;
  if (array) {
    output = formatArray(ctx, value, recurseTimes, visibleKeys, keys);
  } else {
    output = keys.map(function(key) {
      return formatProperty(ctx, value, recurseTimes, visibleKeys, key, array);
    });
  }

  ctx.seen.pop();

  return reduceToSingleString(output, base, braces);
}


function formatPrimitive(ctx, value) {
  if (isUndefined(value))
    return ctx.stylize('undefined', 'undefined');
  if (isString(value)) {
    var simple = '\'' + JSON.stringify(value).replace(/^"|"$/g, '')
                                             .replace(/'/g, "\\'")
                                             .replace(/\\"/g, '"') + '\'';
    return ctx.stylize(simple, 'string');
  }
  if (isNumber(value))
    return ctx.stylize('' + value, 'number');
  if (isBoolean(value))
    return ctx.stylize('' + value, 'boolean');
  // For some reason typeof null is "object", so special case here.
  if (isNull(value))
    return ctx.stylize('null', 'null');
}


function formatError(value) {
  return '[' + Error.prototype.toString.call(value) + ']';
}


function formatArray(ctx, value, recurseTimes, visibleKeys, keys) {
  var output = [];
  for (var i = 0, l = value.length; i < l; ++i) {
    if (hasOwnProperty(value, String(i))) {
      output.push(formatProperty(ctx, value, recurseTimes, visibleKeys,
          String(i), true));
    } else {
      output.push('');
    }
  }
  keys.forEach(function(key) {
    if (!key.match(/^\d+$/)) {
      output.push(formatProperty(ctx, value, recurseTimes, visibleKeys,
          key, true));
    }
  });
  return output;
}


function formatProperty(ctx, value, recurseTimes, visibleKeys, key, array) {
  var name, str, desc;
  desc = Object.getOwnPropertyDescriptor(value, key) || { value: value[key] };
  if (desc.get) {
    if (desc.set) {
      str = ctx.stylize('[Getter/Setter]', 'special');
    } else {
      str = ctx.stylize('[Getter]', 'special');
    }
  } else {
    if (desc.set) {
      str = ctx.stylize('[Setter]', 'special');
    }
  }
  if (!hasOwnProperty(visibleKeys, key)) {
    name = '[' + key + ']';
  }
  if (!str) {
    if (ctx.seen.indexOf(desc.value) < 0) {
      if (isNull(recurseTimes)) {
        str = formatValue(ctx, desc.value, null);
      } else {
        str = formatValue(ctx, desc.value, recurseTimes - 1);
      }
      if (str.indexOf('\n') > -1) {
        if (array) {
          str = str.split('\n').map(function(line) {
            return '  ' + line;
          }).join('\n').substr(2);
        } else {
          str = '\n' + str.split('\n').map(function(line) {
            return '   ' + line;
          }).join('\n');
        }
      }
    } else {
      str = ctx.stylize('[Circular]', 'special');
    }
  }
  if (isUndefined(name)) {
    if (array && key.match(/^\d+$/)) {
      return str;
    }
    name = JSON.stringify('' + key);
    if (name.match(/^"([a-zA-Z_][a-zA-Z_0-9]*)"$/)) {
      name = name.substr(1, name.length - 2);
      name = ctx.stylize(name, 'name');
    } else {
      name = name.replace(/'/g, "\\'")
                 .replace(/\\"/g, '"')
                 .replace(/(^"|"$)/g, "'");
      name = ctx.stylize(name, 'string');
    }
  }

  return name + ': ' + str;
}


function reduceToSingleString(output, base, braces) {
  var numLinesEst = 0;
  var length = output.reduce(function(prev, cur) {
    numLinesEst++;
    if (cur.indexOf('\n') >= 0) numLinesEst++;
    return prev + cur.replace(/\u001b\[\d\d?m/g, '').length + 1;
  }, 0);

  if (length > 60) {
    return braces[0] +
           (base === '' ? '' : base + '\n ') +
           ' ' +
           output.join(',\n  ') +
           ' ' +
           braces[1];
  }

  return braces[0] + base + ' ' + output.join(', ') + ' ' + braces[1];
}


// NOTE: These type checking functions intentionally don't use `instanceof`
// because it is fragile and can be easily faked with `Object.create()`.
function isArray(ar) {
  return Array.isArray(ar);
}
exports.isArray = isArray;

function isBoolean(arg) {
  return typeof arg === 'boolean';
}
exports.isBoolean = isBoolean;

function isNull(arg) {
  return arg === null;
}
exports.isNull = isNull;

function isNullOrUndefined(arg) {
  return arg == null;
}
exports.isNullOrUndefined = isNullOrUndefined;

function isNumber(arg) {
  return typeof arg === 'number';
}
exports.isNumber = isNumber;

function isString(arg) {
  return typeof arg === 'string';
}
exports.isString = isString;

function isSymbol(arg) {
  return typeof arg === 'symbol';
}
exports.isSymbol = isSymbol;

function isUndefined(arg) {
  return arg === void 0;
}
exports.isUndefined = isUndefined;

function isRegExp(re) {
  return isObject(re) && objectToString(re) === '[object RegExp]';
}
exports.isRegExp = isRegExp;

function isObject(arg) {
  return typeof arg === 'object' && arg !== null;
}
exports.isObject = isObject;

function isDate(d) {
  return isObject(d) && objectToString(d) === '[object Date]';
}
exports.isDate = isDate;

function isError(e) {
  return isObject(e) &&
      (objectToString(e) === '[object Error]' || e instanceof Error);
}
exports.isError = isError;

function isFunction(arg) {
  return typeof arg === 'function';
}
exports.isFunction = isFunction;

function isPrimitive(arg) {
  return arg === null ||
         typeof arg === 'boolean' ||
         typeof arg === 'number' ||
         typeof arg === 'string' ||
         typeof arg === 'symbol' ||  // ES6 symbol
         typeof arg === 'undefined';
}
exports.isPrimitive = isPrimitive;

exports.isBuffer = require('./support/isBuffer');

function objectToString(o) {
  return Object.prototype.toString.call(o);
}


function pad(n) {
  return n < 10 ? '0' + n.toString(10) : n.toString(10);
}


var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep',
              'Oct', 'Nov', 'Dec'];

// 26 Feb 16:19:34
function timestamp() {
  var d = new Date();
  var time = [pad(d.getHours()),
              pad(d.getMinutes()),
              pad(d.getSeconds())].join(':');
  return [d.getDate(), months[d.getMonth()], time].join(' ');
}


// log is just a thin wrapper to console.log that prepends a timestamp
exports.log = function() {
  console.log('%s - %s', timestamp(), exports.format.apply(exports, arguments));
};


/**
 * Inherit the prototype methods from one constructor into another.
 *
 * The Function.prototype.inherits from lang.js rewritten as a standalone
 * function (not on Function.prototype). NOTE: If this file is to be loaded
 * during bootstrapping this function needs to be rewritten using some native
 * functions as prototype setup using normal JavaScript does not work as
 * expected during bootstrapping (see mirror.js in r114903).
 *
 * @param {function} ctor Constructor function which needs to inherit the
 *     prototype.
 * @param {function} superCtor Constructor function to inherit prototype from.
 */
exports.inherits = require('inherits');

exports._extend = function(origin, add) {
  // Don't do anything if add isn't an object
  if (!add || !isObject(add)) return origin;

  var keys = Object.keys(add);
  var i = keys.length;
  while (i--) {
    origin[keys[i]] = add[keys[i]];
  }
  return origin;
};

function hasOwnProperty(obj, prop) {
  return Object.prototype.hasOwnProperty.call(obj, prop);
}

}).call(this)}).call(this,require('_process'),typeof global !== "undefined" ? global : typeof self !== "undefined" ? self : typeof window !== "undefined" ? window : {})
},{"./support/isBuffer":6,"_process":9,"inherits":5}],8:[function(require,module,exports){
/*
object-assign
(c) Sindre Sorhus
@license MIT
*/

'use strict';
/* eslint-disable no-unused-vars */
var getOwnPropertySymbols = Object.getOwnPropertySymbols;
var hasOwnProperty = Object.prototype.hasOwnProperty;
var propIsEnumerable = Object.prototype.propertyIsEnumerable;

function toObject(val) {
	if (val === null || val === undefined) {
		throw new TypeError('Object.assign cannot be called with null or undefined');
	}

	return Object(val);
}

function shouldUseNative() {
	try {
		if (!Object.assign) {
			return false;
		}

		// Detect buggy property enumeration order in older V8 versions.

		// https://bugs.chromium.org/p/v8/issues/detail?id=4118
		var test1 = new String('abc');  // eslint-disable-line no-new-wrappers
		test1[5] = 'de';
		if (Object.getOwnPropertyNames(test1)[0] === '5') {
			return false;
		}

		// https://bugs.chromium.org/p/v8/issues/detail?id=3056
		var test2 = {};
		for (var i = 0; i < 10; i++) {
			test2['_' + String.fromCharCode(i)] = i;
		}
		var order2 = Object.getOwnPropertyNames(test2).map(function (n) {
			return test2[n];
		});
		if (order2.join('') !== '0123456789') {
			return false;
		}

		// https://bugs.chromium.org/p/v8/issues/detail?id=3056
		var test3 = {};
		'abcdefghijklmnopqrst'.split('').forEach(function (letter) {
			test3[letter] = letter;
		});
		if (Object.keys(Object.assign({}, test3)).join('') !==
				'abcdefghijklmnopqrst') {
			return false;
		}

		return true;
	} catch (err) {
		// We don't expect any of the above to throw, but better to be safe.
		return false;
	}
}

module.exports = shouldUseNative() ? Object.assign : function (target, source) {
	var from;
	var to = toObject(target);
	var symbols;

	for (var s = 1; s < arguments.length; s++) {
		from = Object(arguments[s]);

		for (var key in from) {
			if (hasOwnProperty.call(from, key)) {
				to[key] = from[key];
			}
		}

		if (getOwnPropertySymbols) {
			symbols = getOwnPropertySymbols(from);
			for (var i = 0; i < symbols.length; i++) {
				if (propIsEnumerable.call(from, symbols[i])) {
					to[symbols[i]] = from[symbols[i]];
				}
			}
		}
	}

	return to;
};

},{}],9:[function(require,module,exports){
// shim for using process in browser
var process = module.exports = {};

// cached from whatever global is present so that test runners that stub it
// don't break things.  But we need to wrap it in a try catch in case it is
// wrapped in strict mode code which doesn't define any globals.  It's inside a
// function because try/catches deoptimize in certain engines.

var cachedSetTimeout;
var cachedClearTimeout;

function defaultSetTimout() {
    throw new Error('setTimeout has not been defined');
}
function defaultClearTimeout () {
    throw new Error('clearTimeout has not been defined');
}
(function () {
    try {
        if (typeof setTimeout === 'function') {
            cachedSetTimeout = setTimeout;
        } else {
            cachedSetTimeout = defaultSetTimout;
        }
    } catch (e) {
        cachedSetTimeout = defaultSetTimout;
    }
    try {
        if (typeof clearTimeout === 'function') {
            cachedClearTimeout = clearTimeout;
        } else {
            cachedClearTimeout = defaultClearTimeout;
        }
    } catch (e) {
        cachedClearTimeout = defaultClearTimeout;
    }
} ())
function runTimeout(fun) {
    if (cachedSetTimeout === setTimeout) {
        //normal enviroments in sane situations
        return setTimeout(fun, 0);
    }
    // if setTimeout wasn't available but was latter defined
    if ((cachedSetTimeout === defaultSetTimout || !cachedSetTimeout) && setTimeout) {
        cachedSetTimeout = setTimeout;
        return setTimeout(fun, 0);
    }
    try {
        // when when somebody has screwed with setTimeout but no I.E. maddness
        return cachedSetTimeout(fun, 0);
    } catch(e){
        try {
            // When we are in I.E. but the script has been evaled so I.E. doesn't trust the global object when called normally
            return cachedSetTimeout.call(null, fun, 0);
        } catch(e){
            // same as above but when it's a version of I.E. that must have the global object for 'this', hopfully our context correct otherwise it will throw a global error
            return cachedSetTimeout.call(this, fun, 0);
        }
    }


}
function runClearTimeout(marker) {
    if (cachedClearTimeout === clearTimeout) {
        //normal enviroments in sane situations
        return clearTimeout(marker);
    }
    // if clearTimeout wasn't available but was latter defined
    if ((cachedClearTimeout === defaultClearTimeout || !cachedClearTimeout) && clearTimeout) {
        cachedClearTimeout = clearTimeout;
        return clearTimeout(marker);
    }
    try {
        // when when somebody has screwed with setTimeout but no I.E. maddness
        return cachedClearTimeout(marker);
    } catch (e){
        try {
            // When we are in I.E. but the script has been evaled so I.E. doesn't  trust the global object when called normally
            return cachedClearTimeout.call(null, marker);
        } catch (e){
            // same as above but when it's a version of I.E. that must have the global object for 'this', hopfully our context correct otherwise it will throw a global error.
            // Some versions of I.E. have different rules for clearTimeout vs setTimeout
            return cachedClearTimeout.call(this, marker);
        }
    }



}
var queue = [];
var draining = false;
var currentQueue;
var queueIndex = -1;

function cleanUpNextTick() {
    if (!draining || !currentQueue) {
        return;
    }
    draining = false;
    if (currentQueue.length) {
        queue = currentQueue.concat(queue);
    } else {
        queueIndex = -1;
    }
    if (queue.length) {
        drainQueue();
    }
}

function drainQueue() {
    if (draining) {
        return;
    }
    var timeout = runTimeout(cleanUpNextTick);
    draining = true;

    var len = queue.length;
    while(len) {
        currentQueue = queue;
        queue = [];
        while (++queueIndex < len) {
            if (currentQueue) {
                currentQueue[queueIndex].run();
            }
        }
        queueIndex = -1;
        len = queue.length;
    }
    currentQueue = null;
    draining = false;
    runClearTimeout(timeout);
}

process.nextTick = function (fun) {
    var args = new Array(arguments.length - 1);
    if (arguments.length > 1) {
        for (var i = 1; i < arguments.length; i++) {
            args[i - 1] = arguments[i];
        }
    }
    queue.push(new Item(fun, args));
    if (queue.length === 1 && !draining) {
        runTimeout(drainQueue);
    }
};

// v8 likes predictible objects
function Item(fun, array) {
    this.fun = fun;
    this.array = array;
}
Item.prototype.run = function () {
    this.fun.apply(null, this.array);
};
process.title = 'browser';
process.browser = true;
process.env = {};
process.argv = [];
process.version = ''; // empty string to avoid regexp issues
process.versions = {};

function noop() {}

process.on = noop;
process.addListener = noop;
process.once = noop;
process.off = noop;
process.removeListener = noop;
process.removeAllListeners = noop;
process.emit = noop;
process.prependListener = noop;
process.prependOnceListener = noop;

process.listeners = function (name) { return [] }

process.binding = function (name) {
    throw new Error('process.binding is not supported');
};

process.cwd = function () { return '/' };
process.chdir = function (dir) {
    throw new Error('process.chdir is not supported');
};
process.umask = function() { return 0; };

},{}]},{},[2])(2)
});
