let clo = require('./game_state.js')


describe('GameState Class', () => {

  describe('constructor', () => {

    test('requires a history array', () => {
      expect(() => GameState({}, '')).toThrow(Error)
    })

    test('requires a string for viewer_name', () => {
      expect(() => GameState({history: []}, null)).toThrow(Error)
    })

  })

})
