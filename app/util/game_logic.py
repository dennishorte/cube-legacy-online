import functools
import random


class GamePhase(object):
    # Pre-game phases
    deck_selection = 'deck_selection'

    # Phases during the game
    untap = 'untap'
    upkeep = 'upkeep'
    draw = 'draw'
    main1 = 'main1'
    combat_begin = 'combat_begin'
    combat_attack = 'combat_attack'
    combat_defend = 'combat_defend'
    combat_damage = 'combat_damage'
    combat_end = 'combat_end'
    main2 = 'main2'
    end = 'end'


class GameCard(object):
    def __init__(self, json):
        self.data = json

    @staticmethod
    def factory(unique_id, cube_card_id):
        from app.models.cube import CubeCard
        card = CubeCard.query.get(cube_card_id)

        data = {
            'id': unique_id,
            'cube_card_id': int(cube_card_id),
            'cube_card_version': int(card.version),
            'json': card.get_json(),

            'annotation': None,  # str
            'counters': {},
            'owner': None,  # str, name of player
            'tapped': False,
            'token': False,
            'visibility': [],
        }

        return GameCard(data)

    def id(self):
        return self.data['id']


class PlayerTableau(object):
    def __init__(self, json):
        self.data = json

    @staticmethod
    def factory(player_name: str):
        data = {
            'name': player_name,

            'battlefield': [],
            'land': [],
            'exile': [],
            'graveyard': [],
            'hand': [],
            'library': [],
            'sideboard': [],
            'stack': [],
            'command': [],

            'counters': {
                'life': 20,
            },
        }

        return PlayerTableau(data)

    @property
    def library(self):
        return self.data['library']

    @property
    def name(self):
        return self.data['name']

    @property
    def sideboard(self):
        return self.data['sideboard']


class GamePlayer(object):
    def __init__(self, json):
        self.data = json

    @staticmethod
    def factory(player_id: int):
        from app.models.user import User
        user = User.query.get(player_id)

        if not user:
            raise ValueError(f"Invalid user id: {player_id}.")

        data = {
            'id': player_id,
            'deck_id': None,
            'name': user.name,
            'ready_to_start': False,
            'tableau': PlayerTableau.factory(user.name).data,
        }

        return GamePlayer(data)

    @property
    def deck_id(self):
        return self.data['deck_id']

    @deck_id.setter
    def deck_id(self, deck_id):
        self.data['deck_id'] = deck_id

    @property
    def id(self):
        return self.data['id']

    @property
    def name(self):
        return self.data['name']

    @property
    def ready_to_start(self):
        return self.data['ready_to_start']

    @ready_to_start.setter
    def ready_to_start(self, ready: bool):
        self.data['ready_to_start'] = ready

    def has_deck(self):
        return self.deck_id is not None

    @property
    def tableau(self):
        return PlayerTableau(self.data['tableau'])


class GameState(object):
    def __init__(self, json):
        self.data = json

    @staticmethod
    def factory(game_id: int, name: str, player_ids: list):
        data = {
            'id': game_id,
            'history': [{
                'message': 'Game Created',
                'player': 'GM',
            }],
            'cards': {},  # id -> card.data
            'name': name,
            'next_id': 1,
            'players': [GamePlayer.factory(id).data for id in player_ids],
            'phase': GamePhase.deck_selection,

            'turn': 0,  # Whose turn is it? (player_idx)
            'priority': 0,  # Which player has priority? (player_idx)
        }

        data['history'].append({
            'message': f"{data['players'][0]['name']}'s turn",
            'player': 'GM',
        })

        return GameState(data)

    def card(self, card_id):
        return GameCard(self.data['cards'][card_id])

    def make_card(self, cube_card_id):
        card = GameCard.factory(self.next_id(), cube_card_id)
        self.data['cards'][card.id()] = card.data
        return card.id()

    def load_deck(self, player_id, maindeck, sideboard):
        if not isinstance(maindeck[0], int):
            raise ValueError("Decks should be lists of GameCard.id int values.")

        player = self.player_by_id(player_id)
        tableau = player.tableau

        if len(tableau.library) > 0:
            raise RuntimeError("User has a library. Loading a deck would overwrite it.")

        tableau.data['library'] = maindeck[:]
        tableau.data['sideboard'] = sideboard[:]

        random.shuffle(tableau.data['library'])

        for card_id in (tableau.library + tableau.sideboard):
            card = self.card(card_id)
            card.data['owner'] = player.name

    @property
    def name(self):
        return self.data['name']

    def next_id(self):
        id = self.data['next_id']
        self.data['next_id'] += 1
        return id

    @property
    def phase(self):
        return self.data['phase']

    def set_phase(self, value):
        self.data['phase'] = value

    def player_by_id(self, player_id):
        for p in self.players:
            if int(p.id) == int(player_id):
                return p

        return None

    @property
    def players(self):
        return [GamePlayer(x) for x in self.data['players']]

    def ready_to_start(self):
        return all([x.ready_to_start for x in self.players])
