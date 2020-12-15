'use strict'

let clo = (function() {

  let clo_public = {
    game: require('./game_ui.js'),
    util: require('./util.js'),
  }

  return clo_public
}())


module.exports = clo
