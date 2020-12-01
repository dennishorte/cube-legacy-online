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


util.card_colors = function(data) {
  let colors = []
  let mana_cost = data.json.card_faces[0].mana_cost.toUpperCase()
  for (let i in mana_cost) {
    let ch = mana_cost.charAt(i)
    if ('WUBRG'.indexOf(ch) > -1)
      colors.push(ch)
  }

  return [...new Set(colors)]
}


util.format_rules_text = function(text) {
  /* let text = elem.text() */
  var new_html = '<span>'

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
  var grabbing = true
  var curr = ''
  let elements = []

  for (var i = 0; i < mana.length; i++) {
    let ch = mana.charAt(i)
    if (ch == '{') {
      grabbing = true
    }
    else if (ch == '}') {
      elements.push(util.mana_symbols_from_string_single(curr))
      curr = ''
    }
    else {
      curr += ch
    }
  }

  return elements
}


util.mana_symbols_from_string_single = function(mana) {
  let classes = ['ms', 'ms-cost', 'ms-shadow']

  mana = mana.replace('/', '')
  classes.push('ms-' + mana.toLowerCase())

  let elem = $('<i></i>')
  elem.addClass(classes.join(' '))

  return elem
}


util.player_idx_from_elem = function(elem) {
  let elem_id = $(elem).attr('id')
  return util.player_idx_from_elem_id(elem_id)
}


util.player_idx_from_elem_id = function(elem_id) {
  return parseInt(elem_id.split('-')[1])
}

module.exports = util
