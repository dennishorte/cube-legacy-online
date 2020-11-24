
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
  return elem_id.split('-')[1]
}


module.exports = util
