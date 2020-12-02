'use strict'
let assert = require('assert')
let util = require('./util.js')


let card_zones = {
  battlefield: {
    visibility: 'all',
    taps: true,
    tokens: true,
  },
  creatures: {
    visibility: 'all',
    taps: true,
    tokens: true,
  },
  command: {
    visibility: 'all',
    taps: false,
    tokens: false,
  },
  land: {
    visibility: 'all',
    taps: true,
    tokens: true,
  },
  exile: {
    visibility: 'all',
    taps: false,
    tokens: false,
  },
  graveyard: {
    visibility: 'all',
    taps: false,
    tokens: false,
  },
  hand: {
    visibility: 'owner',
    taps: false,
    tokens: false,
  },
  library: {
    visibility: 'none',
    taps: false,
    tokens: false,
  },
  sideboard: {
    visibility: 'owner',
    taps: false,
    tokens: false,
  },
  stack: {
    visibility: 'all',
    taps: false,
    tokens: true,
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

  card_annotation(card_id, annotation) {
    let card = this.card(card_id)

    if (!card.annotation) {
      card.annotation = ''
    }

    if (annotation == card.annotation) {
      return
    }

    let diff = {
      delta: [{
        action: 'set_card_value',
        card_id: card_id,
        key: 'annotation',
        old_value: card.annotation,
        new_value: annotation,
      }],
      message: `Annotation on ${card.json.name} set to '${annotation}'`,
      player: this.viewer_name,
    }

    return this._execute(diff)
  }

  /*
   * Use card_factory to generate the basic data, and fill in the required fields.
   */
  card_create(data, zone) {
    let delta = [{
      action: 'create_card',
      card_data: data,
      zone: zone,
    }]

    let diff = {
      delta: delta,
      message: `${data.json.name} token created`,
      player: this.viewer_name,
    }

    return this._execute(diff)
  }

  card_factory() {
    let card_stats = {
      card_faces: [{
        flavor_text: '',
        image_url: '',
        loyalty: '',
        mana_cost: '',
        name: '',
        object: '',
        oracle_text: '',
        power: '',
        toughness: '',
        type_line: '',
      }],
      cmc: 0,
      layout: '',
      name: '',
      object: 'token',
      oracle_text: '',
      rarity: '',
      type_line: '',
    }

    let id = this.next_id()
    let data = {
      id: id,
      cube_card_id: undefined,
      cube_card_version: undefined,
      json: card_stats,

      annotation: '',
      counters: {},
      face_down: false,
      owner: undefined,  // name of player
      tapped: false,
      token: true,
      visibility: [],
    }

    return data
  }

  card_flip_down_up(card_id) {
    let card = this.card(card_id)

    if (!card.hasOwnProperty('face_down')) {
      card.face_down = false
    }

    let old_value = card.face_down;
    let new_value = !old_value;

    var message;
    let player_key = `PLAYER_${this.viewer_idx}_NAME`
    if (new_value == true) {
      message = `${player_key} turns CARD_NAME face down`
    }
    else {
      message = `${player_key} flips CARD_NAME face up`
    }

    let diff = {
      delta: [{
        action: 'set_card_value',
        card_id: card_id,
        key: 'face_down',
        old_value: card.face_down,
        new_value: !card.face_down,
      }],
      message: message,
      player: this.viewer_name,
    }

    return this._execute(diff)
  }

  // True if the current player has more visibility than other players
  // AND the card is in a zone with zero visibility.
  card_is_revealed(card_id, zone_id) {
    let card = this.card(card_id)
    let player_vis = card.visibility.indexOf(this.viewer_name) >= 0
    let limited_vis = card.visibility.length < this.state.players.length

    let zone_name = this._zone_name_from_id(zone_id)
    let zone_vis = card_zones[zone_name].visibility

    return (
      limited_vis
      && player_vis
      && zone_vis == 'none'
    )
  }

  card_is_visible(card_id, zone_id) {
    let card = this.card(card_id)
    let player_vis = card.visibility.indexOf(this.viewer_name) >= 0

    // Being face down overrides the local zone visibility
    if (card.face_down)
      return player_vis

    // A player can reveal a non-visible zone, such as the library.
    var zone_vis = false
    if (zone_id) {
      zone_vis = this.is_revealed(this.viewer_idx, zone_id)
    }

    return player_vis || zone_vis
  }

  card_list(player_idx, zone_name) {
    let tableau = this.state.players[player_idx].tableau
    if (!tableau.hasOwnProperty(zone_name))
      tableau[zone_name] = []

    return tableau[zone_name]
  }

  concede(player_idx) {
    if (!this.state.hasOwnProperty('finished')) {
      this.state.finished = false
      this.state.winner = ''
    }

    let winner_idx = (this.viewer_idx + 1) % 2
    let winner_name = this.state.players[winner_idx].name
    let winner_key = `PLAYER_${winner_idx}_NAME`

    let player_key = `PLAYER_${this.viewer_idx}_NAME`

    let diff = {
      delta: [
        {
          action: 'set_game_value',
          key: 'finished',
          old_value: false,
          new_value: true,
        },
        {
          action: 'set_game_value',
          key: 'winner',
          old_value: '',
          new_value: winner_name,
        }
      ],
      message: `${player_key} concedes. ${winner_key} wins!`,
      player: this.viewer_name,
    }

    return this._execute(diff)
  }

  draw(player_idx, count, delta_only=false) {
    let player = this.state.players[player_idx]
    let library = player.tableau.library
    let hand = player.tableau.hand

    var delta = []

    for (var i = 0; i < count; i++) {
      let card_id = library[i]
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

      delta = delta.concat(this.move_card(orig_loc, dest_loc, card_id, true))
    }

    if (delta_only) {
      return delta
    }

    let diff = {
      delta: delta,
      message: `PLAYER_${player_idx}_NAME draws ${count} cards`,
      player: player_idx,
    }

    return this._execute(diff)
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

  is_revealed(player_idx, zone_id) {
    zone_id = this._clean_id(zone_id)
    let opt_name = `reveal_${zone_id}`
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

  move_card(orig_loc, dest_loc, card_id, delta_only=false) {
    /* loc format:
     * zone = {
     *   name: 'hand',
     *   zone_idx: 0,  // -1 supported to mean bottom
     *   player_idx: 0,
     * }
     */

    let card = this.card(card_id)

    let delta = []

    delta.push({
      action: 'move_card',
      card_id: card_id,
      orig_loc: orig_loc,
      dest_loc: dest_loc,
    })

    if (card.tapped && !card_zones[dest_loc.name].taps) {
      let tap_delta = this.twiddle(card_id, true)
      delta = delta.concat(tap_delta)
    }

    let vis_diff = this._visibility_diff_from_move(orig_loc, dest_loc, this.card(card_id))
    if (vis_diff) {
      delta.push(vis_diff)
    }

    if (delta_only)
      return delta

    // Message
    let viewer_key = `PLAYER_${this.viewer_idx}_NAME`
    var message = `${viewer_key} moves CARD_NAME from ORIG_NAME to DEST_NAME`
    var orig_name = orig_loc.name
    var dest_name = dest_loc.name

    if (orig_loc.name == 'library') {
      if (
        dest_loc.name == 'hand'
        && dest_loc.player_idx == this.viewer_idx
        && orig_loc.zone_idx == 0
      ) {

        message = `${viewer_key} draws CARD_NAME`
      }
    }

    if (orig_loc.player_idx != this.viewer_idx) {
      let player_key = `PLAYER_${orig_loc.player_idx}_NAME`
      orig_name = `${player_key}'s ` + orig_name
    }

    if (dest_loc.player_idx != this.viewer_idx) {
      let player_key = `PLAYER_${dest_loc.player_idx}_NAME`
      dest_name = `${player_key}'s ` + dest_name
    }

    message = message.replace('ORIG_NAME', orig_name)
    message = message.replace('DEST_NAME', dest_name)

    if (card.token && !card_zones[dest_loc.name].tokens) {
      message += ". Token disappears"

      delta.push({
        action: 'annihilate_card',
        card_id: card.id,
        loc: dest_loc,
      })
    }

    // Diff
    let diff = {
      delta: delta,
      message: message,
      player: this.viewer_name,
    }

    return this._execute(diff)
  }

  mulligan(player_idx) {
    let message_diff = {
      delta: [],
      message: `PLAYER_${player_idx}_NAME takes a mulligan`,
      player: 'GM',
    }
    this._execute(message_diff)


    let delta_a = []

    // Put cards back on library
    this.card_list(player_idx, 'hand').forEach(card_id => {
      let orig = {
        name: 'hand',
        zone_idx: 0,
        player_idx: player_idx,
      }

      let dest = {
        name: 'library',
        zone_idx: 0,
        player_idx: player_idx,
      }

      delta_a = delta_a.concat(this.move_card(orig, dest, card_id, true))
    })

    let diff_a = {
      delta: delta_a,
      message: `PLAYER_${player_idx}_NAME returns all cards in hand`,
      player_idx: player_idx,
    }
    this._execute(diff_a)

    this.shuffle(player_idx)
    this.draw(player_idx, 7)
  }

  next_id() {
    let id = this.state.next_id
    assert.ok(!this.state.cards.hasOwnProperty(id), 'Card ID already exists')

    this.state.next_id += 1
    return id
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

  reveal_top_of_library_to(player_idx, library_idx, count) {
    let card_list = this.card_list(library_idx, 'library')
    let player_name = this.player(player_idx).name

    let delta = []

    for (var i = 0; i < count; i++) {
      let card = this.card(card_list[i])

      if (card.visibility.indexOf(player_name) == -1) {
        let new_visibility = card.visibility.concat([player_name])
        delta.push(this._visibility_diff(card, new_visibility))
      }
    }

    var message;
    if (player_idx == library_idx) {
      let player_key = `PLAYER_${player_idx}_NAME`
      message = `${player_key} looks at the top ${count} cards of library`
    }
    else {
      let player_key = `PLAYER_${player_idx}_NAME`
      let library_key = `PLAYER_${library_idx}_NAME`
      message = `${player_key} looks at the top ${count} cards of ${library_key}'s library`
    }

    let diff = {
      delta: delta,
      message: message,
      player: this.viewer_name,
    }

    return this._execute(diff)
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

    if (this.phase() == phase)
      return

    var delta = [{
      action: 'set_game_value',
      key: 'phase',
      old_value: this.phase(),
      new_value: phase,
    }]

    var message = `phase: ${phase}`

    // Untap all the player's cards
    if (phase == 'untap') {
      var count = 0

      for (let zone in card_zones) {
        if (!card_zones.hasOwnProperty(zone))
          continue

        let card_list = this.card_list(this.state.turn, zone)
        for (var i = 0; i < card_list.length; i++) {
          let card = this.card(card_list[i])
          if (card.tapped) {
            let untap_delta = this.twiddle(card.id, true)
            delta = delta.concat(untap_delta)
            count += 1
          }
        }
      }

      if (count > 0) {
        message += `, ${count} cards untapped`
      }
    }

    let diff = {
      delta: delta,
      message: message,
      player: this.viewer_name
    }

    return this._execute(diff)
  }

  shuffle(player_idx, delta_only=false) {
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

    if (delta_only)
      return delta

    let diff = {
      delta: delta,
      message: `PLAYER_${player_idx}_NAME shuffles library`,
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

  toggle_zone_reveal(player_idx, zone_id) {
    zone_id = this._clean_id(zone_id)

    let opt_name = `reveal_${zone_id}`


    if (this.is_revealed(player_idx, zone_id)) {
      delete this.view_options(player_idx)[opt_name]
    }
    else {
      this.view_options(player_idx)[opt_name] = true
    }
  }

  turn_player_idx() {
    return this.state.turn
  }

  twiddle(card_id, delta_only=false) {
    let card = this.card(card_id)
    let action = card.tapped ? 'untap': 'tap'

    let delta = [{
      action: 'set_card_value',
      card_id: card_id,
      key: 'tapped',
      old_value: card.tapped,
      new_value: !card.tapped,
    }]

    if (delta_only)
      return delta

    let diff = {
      delta: delta,
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

    if (card.face_down) {
      return undefined
    }

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

  _zone_name_from_id(zone_id) {
    return zone_id.replace(/^#?player-[0-9]-/, '')
  }


  ////////////////////////////////////////////////////////////////////////////////
  // Apply and Unapply

  _apply(diff) {
    for (var i = 0; i < diff.delta.length; i++) {
      let change = diff.delta[i]
      let action = change.action

      if (action == 'annihilate_card') {
        let zone = this._card_list_from_loc(change.loc)
        zone.splice(change.loc.zone_idx, 1)
      }

      else if (action == 'create_card') {
        let data = change.card_data

        assert.ok(!this.state.cards.hasOwnProperty(data.id), "Card has duplicate id")
        assert.equal(typeof data.json.name, 'string', "Name is not valid")

        this.state.cards[data.id] = data

        let card_list = this._card_list_from_loc({
          name: change.zone,
          player_idx: this.player_idx_by_name(data.owner),
        })

        card_list.push(data.id)
      }

      else if (action == 'concede') {
        console.log('concede')
      }

      else if (action == 'move_card') {
        let card_id = change.card_id

        // Ensure the card exists where it is supposed to be.
        let orig_zone = this._card_list_from_loc(change.orig_loc)
        var orig_idx = change.orig_loc.zone_idx
        if (orig_idx == -1) {
          orig_idx = orig_zone.length - 1
        }

        assert.equal(
          orig_zone[orig_idx], card_id,
          `Card ${card_id} not found at ${orig_idx} in ${change.orig_loc.name} ${orig_zone}`
        )

        // Remove the card from its existing zone
        orig_zone.splice(orig_idx, 1)

        // Add the card to the new zone.
        let dest_zone = this._card_list_from_loc(change.dest_loc)
        var dest_idx = change.dest_loc.zone_idx
        if (dest_idx == -1) {
          dest_idx = dest_zone.length
        }
        dest_zone.splice(dest_idx, 0, card_id)
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

      else if (action == 'unannihilate_card') {
        let zone = this._card_list_from_loc(change.loc)
        zone.splice(change.loc.zone_idx, 0, change.card_id)
      }

      else if (action == 'uncreate_card') {
        let data = change.card_data
        let id = data.id

        let card_list = this._card_list_from_loc({
          name: change.zone,
          player_idx: this.player_idx_by_name(data.owner),
        })

        let index = card_list.indexOf(id)
        assert.ok(index != -1, 'Could not find card to uncreate')

        card_list.splice(index, 1)

        delete this.state.cards[id]
      }

      else {
        throw `Unknown action ${action}`
      }

    }

    // Update the diff with visibility information of the cards (after the diff was applied).
    // This ensures that when cards become visible, the message includes the card name.
    for (var i = 0; i < diff.delta.length; i++) {
      let change = diff.delta[i]
      if (change.hasOwnProperty('card_id')) {
        change.card_vis = [...this.card(change.card_id).visibility]
      }
    }

  }

  _unapply(diff) {
    // Make a copy so that we don't alter the original diff.
    let inverse = JSON.parse(JSON.stringify(diff))

    // Reverse the order of the delta so they will be unapplied in reverse order of application.
    let delta = inverse.delta || []
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

      else if (action == 'create_card') {
        change.action = 'uncreate_card'
      }

      else if (action == 'annihilate_card') {
        change.action = 'unannihilate_card'
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
