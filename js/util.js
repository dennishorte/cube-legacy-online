let assert = require('assert')


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


util.string_reverse = function(str) {
  return str.split("").reverse().join("")
}


////////////////////////////////////////////////////////////////////////////////
//


util.mana_cost_colors = function(mana_cost) {
  mana_cost = mana_cost.toUpperCase()
  let colors = []
  for (let i in mana_cost) {
    let ch = mana_cost.charAt(i)
    if ('WUBRG'.indexOf(ch) > -1)
      colors.push(ch)
  }

  return [...new Set(colors)].join('')
}


util.format_rules_text = function(text) {
  /* let text = elem.text() */
  var new_html = '<span>'

  if (text.startsWith('+ ')) {
    new_html = '<span class="rule-scar">'
    text = text.slice(2)
  }

  var last_commit = -1;
  var open_curly = -1;
  var open_paren = -1;

  var i;
  for (i = 0; i < text.length; i++) {
    let ch = text.charAt(i)

    if (ch == '{') {
      assert.equal(open_curly, -1, "Format rules text: A")
      open_curly = i

      if (last_commit < i) {
        new_html += text.substr(last_commit + 1, i - last_commit - 1)
        last_commit = i - 1
      }
    }

    else if (ch == '}') {
      assert.ok(open_curly >= 0, "Format rules text: B")
      let icon_string = util.icon_from_text(text.substr(open_curly, i - open_curly + 1))
      new_html += icon_string
      last_commit = i
      open_curly = -1
    }

    else if (ch == '(') {
      assert.equal(open_curly, -1, "Format rules text: C")
      assert.equal(open_paren, -1, "Format rules text: D")

      if (last_commit < i) {
        new_html += text.substr(last_commit + 1, i - last_commit - 1)
        last_commit = i - 1
      }

      new_html += '<em class="frame-reminder-text">'
      open_paren = i
    }

    else if (ch == ')') {
      assert.equal(open_curly, -1, "Format rules text: E")
      assert.ok(open_paren > -1, "Format rules text: F")

      new_html += text.substr(last_commit + 1, i - last_commit)
      new_html += '</em>'

      last_commit = i
      open_paren = -1
    }

  }

  assert.equal(open_curly, -1, "Format rules text: Y")
  assert.equal(open_paren, -1, "Format rules text: Z")

  if (last_commit != i) {
    new_html += text.substr(last_commit + 1)
  }

  new_html += "</span>"

  return new_html
}


util.icon_from_text = function(text) {
  assert.equal(text.charAt(0), '{')
  assert.equal(text.charAt(text.length-1), '}')

  text = text.substr(1, text.length-2)

  let classes = ['ms', 'ms-cost']

  if (text == '1/2') {
    classes.add('1-2')
  }
  else {
    text = text.replace('/', '').toLowerCase().trim()

    if (text == 't') {
      classes.push('ms-tap')
    }
    else if (text == 'q') {
      classes.push('ms-untap')
    }
    else if (text == 'inf') {
      classes.push('ms-infinity')
    }
    else {
      if (['uw', 'wg', 'gr', 'rb', 'bu', 'w2', 'u2', 'b2', 'r2', 'g2'].indexOf(text) >= 0) {
        text = util.string_reverse(text)
      }

      classes.push(`ms-${text}`)
    }
  }

  let class_string = classes.join(' ')
  return `<i class="${class_string}"></i>`
}


util.mana_symbols_from_string = function(mana) {
  var curr = ''
  let elements = []

  for (var i = 0; i < mana.length; i++) {
    let ch = mana.charAt(i)
    curr += ch

    if (ch == '}') {
      elements.push(util.icon_from_text(curr))
      curr = ''
    }
  }

  return elements
}


util.player_idx_from_elem = function(elem) {
  let elem_id = $(elem).attr('id')
  return util.player_idx_from_elem_id(elem_id)
}


util.player_idx_from_elem_id = function(elem_id) {
  return parseInt(elem_id.split('-')[1])
}


////////////////////////////////////////////////////////////////////////////////
// Card drawing functions

util.draw_card_face = function(container, face_data) {
  // Elements to be updated
  const name_elem = container.find('.frame-card-name')
  const mana_elem = container.find('.frame-mana-cost')
  const type_elem = container.find('.frame-card-type')
  const rules_elem = container.find('.frame-description-wrapper')
  const flavor_elem = container.find('.frame-flavor-wrapper')
  const image_elem = container.find('.frame-art')
  const ptl_elem = container.find('.frame-pt-loyalty')
  const ach_elem = container.find('.frame-achievements-wrapper')
  const pick_info = container.find('.card-pick-info')

  if (face_data.scarred) {
    container.addClass('scarred')
  }

  // Name, Mana, Type
  name_elem.text(face_data.name)
  type_elem.text(face_data.type_line)

  // Mana
  mana_elem.empty().append(util.mana_symbols_from_string(face_data.mana_cost))

  // Image
  const art_crop = face_data.art_crop_url || face_data.image_url.replace('normal', 'art_crop')
  image_elem.attr('src', art_crop)

  // Rules Text
  rules_elem.empty()
  let rules;
  if (face_data.scarred_oracle_text) {
    rules = face_data.scarred_oracle_text.split('\n')
  }
  else {
    rules = face_data.oracle_text.split('\n')
  }

  for (let i = 0; i < rules.length; i++) {
    const rule = rules[i].trim()
    const html_string = util.format_rules_text(rule)

    if (rule.length == 0)
      continue

    const rule_elem = $('<p>')
    rule_elem.addClass('frame-description')
    rule_elem.html(html_string)
    rules_elem.append(rule_elem)
  }

  // Flavor text
  flavor_elem.empty()
  const flavor = face_data.flavor_text.split('\n')
  for (let i = 0; i < flavor.length; i++) {
    const flav = flavor[i].trim()
    if (flav.length == 0)
      continue

    const flav_elem = $('<p>')
    flav_elem.addClass('frame-flavor-text')
    flav_elem.text(flav)
    flavor_elem.append(flav_elem)
  }

  // Linked achievements
  ach_elem.empty()
  if (face_data.achievements) {
    face_data.achievements.forEach(ach => {
      const elem = $('<p>')
      elem.addClass('frame-achievement-desc')
      elem.text(' ' + ach.conditions)
      elem.prepend($('<i class="fab fa-font-awesome-flag"></i>'))

      ach_elem.append(elem)
    })
  }

  // Power/Toughness or Loyalty
  if (face_data.power) {
    const pt = `${face_data.power}/${face_data.toughness}`
    ptl_elem.text(pt)
    ptl_elem.show()
  }
  else if (face_data.loyalty) {
    ptl_elem.text(face_data.loyalty)
    ptl_elem.show()
  }
  else {
    ptl_elem.hide()
  }

  // Pick Info
  if (face_data.pick_info) {
    pick_info.text(`picks: ${face_data.pick_info.num_picks}, avg: ${face_data.pick_info.average_pick}`)
  }
  else {
    pick_info.text('')
  }

  // Container classes
  container.removeClass([
    'land-card',
    'white-card',
    'blue-card',
    'black-card',
    'red-card',
    'green-card',
    'gold-card',
    'artifact-card',
  ])

  if (face_data.type_line.toLowerCase().indexOf('land') >= 0) {
    container.addClass('land-card')
  }
  else {
    const colors = util.mana_cost_colors(face_data.mana_cost)

    if (colors == 'W')
      container.addClass('white-card')

    else if (colors == 'U')
      container.addClass('blue-card')

    else if (colors == 'B')
      container.addClass('black-card')

    else if (colors == 'R')
      container.addClass('red-card')

    else if (colors == 'G')
      container.addClass('green-card')

    else if (colors.length > 1)
      container.addClass('gold-card')

    else
      container.addClass('artifact-card')
  }
}


util.draw_card_frame = function(container, card_json) {
  let front = container.find('.closeup-front')
  let back = container.find('.closeup-back')

  // Draw front
  util.draw_card_face(front, card_json.card_faces[0])

  // Draw back
  if (card_json.card_faces.length > 1) {
    util.draw_card_face(back, card_json.card_faces[1])
    back.show()
  }
  else {
    back.hide()
  }
}


module.exports = util
