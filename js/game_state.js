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
    tokens: true,
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
    tokens: true,
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
    this.spectator = this.viewer_idx == -1
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
      message: `Annotation on CARD_NAME set to '${annotation}'`,
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
      message: `${data.json.name} created`,
      player: this.viewer_name,
    }

    return this._execute(diff)
  }

  card_factory() {
    let card_stats = {
      card_faces: [{
        flavor_text: '',
        image_url: '',
        art_crop_url: '',
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

  card_flip_down_up(card_id, delta_only=false) {
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

    let delta = [{
      action: 'set_card_value',
      card_id: card_id,
      key: 'face_down',
      old_value: card.face_down,
      new_value: !card.face_down,
    }]

    // Turning the card face-up may affect its visibility.
    if (card.face_down) {
      let card_loc = this.card_find_loc(card.id)

      // Temporarily set face up so that vis diff will calculate correctly.
      card.face_down = false
      let vis_diff = this._visibility_diff_from_move(card_loc, card)
      card.face_down = true

      if (vis_diff) {
        delta.push(vis_diff)
      }
    }

    if (delta_only)
      return delta

    let diff = {
      delta: delta,
      message: message,
      player: this.viewer_name,
    }

    return this._execute(diff)
  }

  // True if normally only the current player could see the card, but other players can
  // see it as well.
  card_is_revealed(card_id, zone_id) {
    const zone_name = this._zone_name_from_id(zone_id)
    const zone_vis = card_zones[zone_name].visibility

    const card = this.card(card_id)
    const non_owners_can_see = (
      card.visibility.length > 1
      || (card.visibility.length > 0 && card.visibility.indexOf(card.owner) < 0)
    )

    return zone_vis != 'all' && non_owners_can_see
  }

  card_is_visible(card_id, zone_id) {
    let card = this.card(card_id)
    var player_vis = card.visibility.indexOf(this.viewer_name) >= 0

    if (this.spectator) {
      player_vis = card.visibility.length >= this.num_players()
    }

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

  card_find_loc(card_id) {
    for (var i = 0; i < this.state.players.length; i++) {
      let player = this.state.players[i]
      for (let zone in card_zones) {
        if (!card_zones.hasOwnProperty(zone))
          continue

        let card_list = this.card_list(i, zone)
        let zone_idx = card_list.indexOf(card_id)
        if (zone_idx >= 0) {
          return {
            name: zone,
            zone_idx: zone_idx,
            player_idx: i,
          }
        }
      }
    }

    return undefined
  }

  concede(player_idx) {
    // For older games, ensure the eliminated field exists
    this.state.players.forEach(player => {
      if (!player.hasOwnProperty('eliminated')) {
        player.eliminated = false
      }
    })

    const player_key = `PLAYER_${this.viewer_idx}_NAME`
    const delta = [
      {
        action: 'set_player_value',
        player_idx: this.viewer_idx,
        key: 'eliminated',
        old_value: false,
        new_value: true,
      },
    ]

    const diff = {
      delta: delta,
      message: `${player_key} concedes`,
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

  hide_zone(player_idx, zone_name) {
    const card_list = this.card_list(player_idx, zone_name)
    const zone_vis = card_zones[zone_name].visibility
    let visibility
    if (zone_vis == 'all') {
      visibility = this.state.players.map(player => player.name).sort()
    }
    else if (zone_vis == 'owner') {
      visibility = [this.state.players[player_idx].name]
    }
    else {
      visiblity = []
    }

    const delta = []
    card_list.forEach(card_id => {
      const card = this.card(card_id)
      const diff = this._visibility_diff(card, visibility)
      delta.push(diff)
    })

    const diff = {
      delta: delta,
      message: `PLAYER_${this.viewer_idx}_NAME hides PLAYER_${player_idx}_NAME's ${zone_name}`,
      player: this.viewer_name,
    }

    return this._execute(diff)
  }

  is_auto_draw(player_idx) {
    const view_options = this.view_options(player_idx)

    // Set up a default value since this will start being in effect for games in progress.
    // The default option can be removed once all games start with it set.
    if (!view_options.hasOwnProperty('auto-draw')) {
      view_options['auto-draw'] = true
    }

    return view_options['auto-draw']
  }

  is_collapsed(player_idx, zone_id) {
    if (this.spectator)
      return zone_id == 'sideboard' ? true : false

    zone_id = this._clean_id(zone_id)
    let opt_name = `collapse_${zone_id}`
    return this.view_options(player_idx)[opt_name]
  }

  is_revealed(player_idx, zone_id) {
    if (this.spectator)
      return false

    zone_id = this._clean_id(zone_id)
    let opt_name = `reveal_${zone_id}`
    return this.view_options(player_idx)[opt_name]
  }

  library_zone_desc(player_idx, zone_idx) {
    let card_list = this.card_list(player_idx, 'library')
    if (zone_idx == 0) {
      return "top of library"
    }
    else if (zone_idx == -1 || zone_idx == card_list.length) {
      return "bottom of library"
    }
    else if (zone_idx < card_list.length / 2) {
      return `${zone_idx} from top of library`
    }
    else {
      let dist_from_bottom = card_list.length - zone_idx
      return `${dist_from_bottom} from bottom of library`
    }
  }

  message(text) {
    let player_key = `PLAYER_${this.viewer_idx}_NAME`

    let diff = {
      delta: [],
      message: `${player_key}: "${text}"`,
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

    let vis_diff = this._visibility_diff_from_move(dest_loc, this.card(card_id))
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
      else {
        orig_name = this.library_zone_desc(orig_loc.player_idx, orig_loc.zone_idx)
      }
    }

    if (dest_loc.name == 'library') {
      dest_name = this.library_zone_desc(dest_loc.player_idx, dest_loc.zone_idx)
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
      player_idx: this.viewer_idx,
    }
    this._execute(diff_a)

    this.shuffle(player_idx)
    this.draw(player_idx, 7)
  }

  move_top_of_library_to(
    source_tableau_idx,
    dest_tableau_idx,
    dest_zone,
    count,
    options,
  ) {
    if (count <= 0)
      return

    const library = this.card_list(source_tableau_idx, 'library')
    let delta = []

    // Build up the delta while applying each diff as it is added.
    // The applied diffs will be undone later, so that it can all be applied as a single
    // diff at the end. This is required because otherwise the diff building power of other
    // functions can't be leveraged since the game state won't be correct if the previous
    // changes haven't been applied.
    for (let i = 0; i < count; i++) {
      const card_id = library[0]

      // Flip the card face down and
      if (options.face_down) {
        const card = this.card(card_id)
        if (!card.face_down) {
          const flip_delta = this.card_flip_down_up(card_id, true)
          delta = delta.concat(flip_delta)

          // Apply the flip diffs so that each successive diff is generated correctly.
          const tmp_diff = {
            delta: flip_delta,
            msg: 'tmp',
            player: 'GM',
          }
          this._execute(tmp_diff)
        }
      }

      const orig_loc = {
        name: 'library',
        zone_idx: 0,
        player_idx: source_tableau_idx,
      }
      const dest_loc = {
        name: dest_zone,
        zone_idx: 0,
        player_idx: dest_tableau_idx,
      }

      if (dest_zone == 'library' && options.library_bottom) {
        dest_loc.zone_idx = this.card_list(dest_tableau_idx, dest_zone).length
        if (source_tableau_idx == dest_tableau_idx) {
          // Because the card is coming out of the library, the array length won't change
          dest_loc.zone_idx -= 1
        }
      }

      const move_delta = this.move_card(orig_loc, dest_loc, card_id, true)
      delta = delta.concat(move_delta)

      // Apply the move diffs so that each successive diff is generated correctly.
      const tmp_diff = {
        delta: move_delta,
        msg: 'tmp',
        player: 'GM',
      }
      this._execute(tmp_diff)
    }

    // Undo all of the temporary diffs
    while (this.history[this.history.length - 1].msg == 'tmp') {
      this.undo()
    }

    let player_key = `PLAYER_${this.viewer_idx}_NAME`
    let zone_key = `PLAYER_${dest_tableau_idx}_NAME's ${dest_zone}`
    var message = `${player_key} moves ${count} cards from library to ${zone_key}`
    if (options.face_down)
      message += ', face down'

    let diff = {
      delta: delta,
      message: message,
      player_idx: this.viewer_idx,
    }

    return this._execute(diff)
  }

  next_id() {
    let id = this.state.next_id
    this.state.next_id += 1
    return id
  }

  not_owners_zone(card, player_idx) {
    const player_name = this.player(player_idx).name
    return player_name != card.owner
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

  phase() {
    return this.state.phase
  }

  player(player_idx) {
    return this.state.players[player_idx]
  }

  player_counter_create(player_idx, counter) {
    let player = this.state.players[player_idx]
    let counters = player.tableau.counters
    assert.ok(!(counter in counters), `Can't create counter ${counter}`)
    counters[counter] = 0
  }

  player_counter_increment(player_idx, counter, amount) {
    let player = this.state.players[player_idx]
    let counters = player.tableau.counters

    let diff = {
      delta: [{
        action: 'set_player_counter',
        key: counter,
        player_idx: player_idx,
        old_value: counters[counter],
        new_value: counters[counter] + amount,
      }],
      message: `${player.name} ${counter} change ${amount}`,
      player: this.viewer_name,
    }

    return this._execute(diff)
  }

  player_idx_by_name(player_name) {
    for (var i = 0; i < this.state.players.length; i++) {
      if (this.state.players[i].name == player_name) {
        return i
      }
    }
    return -1
  }

  priority_player_idx() {
    return this.state.priority
  }

  randomize_bottom_of_library(player_idx, count) {
    if (count <= 1) {
      return
    }

    let library = this.card_list(player_idx, 'library')

    if (count > library.length) {
      count = library.length
    }

    let top = library.slice(0, library.length - count)
    let bottom = library.slice(library.length - count, library.length)

    const delta = []

    // Step 1: Clear the visibility on the cards.
    for (let i = library.length - count; i < library.length; i++) {
      const card = this.card(library[i])
      if (card.visibility.length > 0) {
        delta.push(this._visibility_diff(card, []))
      }
    }

    // Step 2: Randomize the card positions
    util.arrayShuffle(bottom)
    const updated = top.concat(bottom)

    delta.push({
      action: 'set_cards_in_zone',
      player_idx: player_idx,
      zone: 'library',
      old_value: library,
      new_value: updated,
    })

    let player_key = `PLAYER_${player_idx}_NAME`
    let diff = {
      delta: delta,
      message: `Bottom ${count} cards of ${player_key}'s library randomized`,
      player_idx: this.viewer_idx,
    }

    return this._execute(diff)
  }

  reveal_top_of_library_to(player_names, library_idx, count) {
    const card_list = this.card_list(library_idx, 'library')
    const delta = []

    if (count > card_list.length) {
      count = card_list.length
    }

    for (let i = 0; i < count; i++) {
      const card = this.card(card_list[i])

      const new_visibility = [...card.visibility]
      let was_changed = false
      player_names.forEach(name => {
        if (new_visibility.indexOf(name) == -1) {
          new_visibility.push(name)
          was_changed = true
        }
      })

      if (was_changed) {
        delta.push(this._visibility_diff(card, new_visibility))
      }
    }

    var message;
    if (this.viewer_idx == library_idx) {
      const player_key = `PLAYER_${this.viewer_idx}_NAME`
      message = `${player_key} looks at the top ${count} cards of library`
    }
    else {
      const player_key = `PLAYER_${this.viewer_idx}_NAME`
      const library_key = `PLAYER_${library_idx}_NAME`
      message = `${player_key} looks at the top ${count} cards of ${library_key}'s library`
    }

    if (player_names.length > 1) {
      message = message.replace('looks at', 'reveals')
    }

    const diff = {
      delta: delta,
      message: message,
      player: this.viewer_name,
    }

    return this._execute(diff)
  }

  reveal_next_in_library(player_idx) {
    const card_list = this.card_list(player_idx, 'library')
    const all_player_names = this.state.players.map(player => player.name).sort()

    // Find the first card in the player's library that isn't visible to all players
    for (let i = 0; i < card_list.length; i++) {
      const card = this.card(card_list[i])
      if (card.visibility.length < all_player_names.length) {
        return this.reveal_top_of_library_to(all_player_names, player_idx, i+1)
      }
    }

    throw "Library is fully revealed already"
  }

  reveal_zone(player_idx, zone_name) {
    const card_list = this.card_list(player_idx, zone_name)
    const visibility = this.state.players.map(player => player.name).sort()

    const delta = []
    card_list.forEach(card_id => {
      const card = this.card(card_id)
      if (card.visibility.length < visibility.length) {
        const diff = this._visibility_diff(card, visibility)
        delta.push(diff)
      }
    })

    const diff = {
      delta: delta,
      message: `PLAYER_${this.viewer_idx}_NAME reveals PLAYER_${player_idx}_NAME's ${zone_name}`,
      player: this.viewer_name,
    }

    return this._execute(diff)
  }

  save_data() {
    return this.state
  }

  set_auto_draw(player_idx, value) {
    this.view_options(player_idx)['auto-draw'] = value
  }

  set_history_save_point() {
    this.history_save_point = this.history_index
  }

  set_history_index(index) {
    if (index >= this.history.length || index < 1) {
      return
    }

    this._move_through_history(index)
  }

  set_phase(phase) {
    assert.ok(this._is_valid_phase(phase), `Invalid game phase: ${phase}`)

    if (this.phase() == phase)
      return

    let delta = [{
      action: 'set_game_value',
      key: 'phase',
      old_value: this.phase(),
      new_value: phase,
    }]

    let message = `phase: ${phase}`

    // Untap all the player's cards
    if (phase == 'untap') {
      let count = 0

      for (let zone in card_zones) {
        if (!card_zones.hasOwnProperty(zone))
          continue

        let card_list = this.card_list(this.state.turn, zone)
        for (let i = 0; i < card_list.length; i++) {
          const card = this.card(card_list[i])
          if (card.tapped) {
            const untap_delta = this.twiddle(card.id, true)
            delta = delta.concat(untap_delta)
            count += 1
          }
        }
      }

      if (count > 0) {
        message += `, ${count} cards untapped`
      }
    }

    else if (phase == 'draw' && this.is_auto_draw(this.state.turn)) {
      delta = delta.concat(this.draw(this.state.turn, 1, true))
      message += ', draw a card'
    }

    const diff = {
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

  start_turn() {
    var delta = [{
      action: 'set_game_value',
      key: 'turn',
      old_value: this.turn_player_idx(),
      new_value: this.viewer_idx,
    }]

    let diff = {
      delta: delta,
      message: `PLAYER_${this.viewer_idx}_NAME's turn`,
      player: 'GM',
    }

    this._execute(diff)
  }

  tie_game(player_idx) {
    // For older games, ensure the eliminated field exists
    this.state.players.forEach(player => {
      if (!player.hasOwnProperty('eliminated')) {
        player.eliminated = false
      }
    })

    const delta = []

    this.state.players.forEach((player, idx) => {
      if (!player.eliminated) {
        delta.push({
          action: 'set_player_value',
          player_idx: idx,
          key: 'eliminated',
          old_value: false,
          new_value: true,
        })
      }
    })

    const player_key = `PLAYER_${this.viewer_idx}_NAME`
    const diff = {
      delta: delta,
      message: `${player_key} declares the game a tie`,
      player: this.viewer_name,
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
      message: `${action}: CARD_NAME`,
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

  zone_meta_info() {
    return card_zones
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
    diff.id = this.next_id()
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

    const forward = index > this.history_index
    const increment = forward ? 1 : -1

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
    assert.ok(new_visibility.length <= this.num_players(), "Too much visibility.")

    return {
      action: 'set_visibility',
      card_id: card.id,
      vis: [...new_visibility].sort(),
      old: [...card.visibility]
    }
  }

  _visibility_diff_from_move(dest_loc, card) {
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

    let new_names_to_add = names_to_add.filter(name => card.visibility.indexOf(name) == -1)

    if (new_names_to_add.length > 0) {
      return this._visibility_diff(card, card.visibility.concat(new_names_to_add))
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
      const change = diff.delta[i]
      const action = change.action

      if (action == 'annihilate_card') {
        const zone = this._card_list_from_loc(change.loc)
        zone.splice(change.loc.zone_idx, 1)
      }

      else if (action == 'create_card') {
        const data = change.card_data

        // Don't assert this anymore, since we don't delete cards when going back through
        // time anymore.
        //assert.ok(!this.state.cards.hasOwnProperty(data.id), "Card has duplicate id")
        assert.equal(typeof data.json.name, 'string', "Name is not valid")

        this.state.cards[data.id] = data

        const card_list = this._card_list_from_loc({
          name: change.zone,
          player_idx: this.player_idx_by_name(data.owner),
        })

        card_list.push(data.id)
      }

      else if (action == 'concede') {
        console.log('concede')
      }

      else if (action == 'move_card') {
        const card_id = change.card_id

        // Ensure the card exists where it is supposed to be.
        const orig_zone = this._card_list_from_loc(change.orig_loc)
        let orig_idx = change.orig_loc.zone_idx
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
        const dest_zone = this._card_list_from_loc(change.dest_loc)
        let dest_idx = change.dest_loc.zone_idx
        if (dest_idx < 0) {
          dest_idx = dest_zone.length + 1 + dest_idx
        }
        dest_zone.splice(dest_idx, 0, card_id)
      }

      else if (action == 'set_game_value') {
        const key = change.key
        assert.equal(
          this.state[key], change.old_value,
          `Change old value (${change.old_value}) doesn't match current value (${this.state[key]})`
        )
        this.state[key] = change.new_value
      }

      else if (action == 'set_card_value') {
        const card = this.card(change.card_id)
        const key = change.key
        assert.equal(
          card[key], change.old_value,
          "Change old value doesn't match current card value" +
          `card: ${card.id}:${card.json.name}, key: ${key}, ` +
          `change.old: ${change.old_value}, ${card[key]}`
        )

        card[key] = change.new_value
      }

      else if (action == 'set_cards_in_zone') {
        const tableau = this.state.players[change.player_idx].tableau
        assert.ok(util.arraysEqual(tableau[change.zone], change.old_value))

        tableau[change.zone] = [...change.new_value]
      }

      else if (action == 'set_player_counter') {
        const counters = this.state.players[change.player_idx].tableau.counters
        const key = change.key
        assert.equal(counters[key], change.old_value)

        counters[key] = change.new_value
      }

      else if (action == 'set_player_value') {
        const key = change.key
        const player = this.state.players[change.player_idx]
        assert.equal(player[key], change.old_value)

        player[key] = change.new_value
      }

      else if (action == 'set_visibility') {
        const card = this.card(change.card_id)
        assert.ok(util.arraysEqual(card.visibility, change.old), "Original visibility does not match")

        card.visibility = [...change.vis]
      }

      else if (action == 'unannihilate_card') {
        const zone = this._card_list_from_loc(change.loc)
        zone.splice(change.loc.zone_idx, 0, change.card_id)
      }

      else if (action == 'uncreate_card') {
        const data = change.card_data
        const id = data.id

        const card_list = this._card_list_from_loc({
          name: change.zone,
          player_idx: this.player_idx_by_name(data.owner),
        })

        const index = card_list.indexOf(id)
        assert.ok(index != -1, 'Could not find card to uncreate')

        card_list.splice(index, 1)

        // Can't actually delete the token because if a user is just browsing the history
        // then that token needs to exist to write its name into entries in the history.
        // delete this.state.cards[id]
      }

      else {
        throw `Unknown action ${action}`
      }

    }

    // Update the diff with visibility information of the cards (after the diff was applied).
    // This ensures that when cards become visible, the message includes the card name.
    for (var i = 0; i < diff.delta.length; i++) {
      const change = diff.delta[i]
      if (change.hasOwnProperty('card_id')) {
        change.card_vis = [...this.card(change.card_id).visibility]
      }
    }

  }

  _unapply(diff) {
    // Make a copy so that we don't alter the original diff.
    const inverse = JSON.parse(JSON.stringify(diff))

    // Reverse the order of the delta so they will be unapplied in reverse order of application.
    let delta = inverse.delta || []
    delta.reverse()

    // Invert each change in the delta
    for (var i = 0; i < delta.length; i++) {
      const change = delta[i]
      const action = change.action

      if (action == 'set_game_value'
          || action == 'set_card_value'
          || action == 'set_cards_in_zone'
          || action == 'set_player_counter'
          || action == 'set_player_value'
      ) {
        const tmp = change.old_value
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
        const tmp = change.orig_loc
        change.orig_loc = change.dest_loc
        change.dest_loc = tmp
      }

      else if (action == 'set_visibility') {
        const tmp = change.vis
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
