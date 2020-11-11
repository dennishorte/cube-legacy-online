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


class Visibility(object):
    all = 'all'  # Visible to all
    inherit = 'inherit'  # Use the visiblity of the zone it is in.
    tableau = 'tableau'  # Visible only to the player who owns its tableau


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
            'tapped': False,
            'visibility': Visibility.inherit,
        }

        return GameCard(data)

    def annotation(self, ann=None):
        if ann:
            self.data['annotation'] = ann
        else:
            return self.data['annotation']

    def counter(self, name, value=None):
        if value:
            self.counters()[name] = int(value)
        else:
            return self.counters().get(name, 0)

    def counters(self):
        return self.data['counters']

    def id(self):
        return self.data['card_id']

    def tapped(self):
        return self.data.get('tapped', False)

    def visibility(self):
        return self.data['visibility']


class PlayerTableau(object):
    def __init__(self, json):
        self.data = json

    @staticmethod
    def factory(player_name: str):
        data = {
            'name': player_name,

            'battlefield': [],
            'exile': [],
            'graveyard': [],
            'hand': [],
            'library': [],
            'sideboard': [],
            'stack': [],

            'counters': {
                'life': 20,
            },
        }

        return PlayerTableau(data)

    ############################################################
    # Game Zones

    @property
    def battlefield(self):
        return self.data['battefield']

    @property
    def exile(self):
        return self.data['exile']

    @property
    def graveyard(self):
        return self.data['graveyard']

    @property
    def hand(self):
        return self.data['hand']

    @property
    def library(self):
        return self.data['library']

    @property
    def stack(self):
        return self.data['stack']

    ############################################################
    # Counter Data

    @property
    def counters(self):
        return self.data['counters']

    @property
    def energy(self):
        return self.counters.get('energy', 0)

    @property
    def life(self):
        return self.counters['life']

    @property
    def poison(self):
        return self.counters.get('poison', 0)

    ############################################################
    # Setters

    def load_deck(self, maindeck, sideboard):
        if not isinstance(maindeck[0], GameCard):
            raise ValueError("Decks should be lists of game_logic.GameCard objects.")

        if len(self.library) > 0:
            raise RuntimeError("User has a library. Loading a deck would overwrite it.")

        random.shuffle(maindeck)
        self.data['library'] = [x.data for x in maindeck]
        self.data['sideboard'] = [x.data for x in sideboard]


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

    def deck_builder(self):
        raise NotImplementedError()

    def has_deck(self):
        return self.deck_id is not None

    @property
    def tableau(self):
        return PlayerTableau(self.data['tableau'])


class GameState(object):
    def __init__(self, json):
        self.data = json

    @staticmethod
    def factory(name: str, player_ids: list):
        data = {
            'name': name,
            'next_id': 1,
            'players': [GamePlayer.factory(id).data for id in player_ids],
            'phase': GamePhase.deck_selection,
        }

        return GameState(data)

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

    @phase.setter
    def phase(self, value):
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
