import random


class GamePhase(object):
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
        from app.models.cube_models import CubeCard
        card = CubeCard.query.get(cube_card_id)

        data = {
            'id': unique_id,
            'cube_card_id': int(cube_card_id),
            'cube_card_version': int(card.version),
            'json': card.get_json(),

            'annotation': '',
            'counters': {},
            'face_down': False,
            'owner': None,  # str, name of player
            'scarred': card.is_scarred(),
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
            'creatures': [],
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

            'view_options': {},
        }

        return PlayerTableau(data)

    @property
    def command(self):
        return self.data['command']

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
        from app.models.user_models import User
        user = User.query.get(player_id)

        if not user:
            raise ValueError(f"Invalid user id: {player_id}.")

        data = {
            'id': player_id,
            'deck_id': None,
            'eliminated': False,
            'name': user.name,
            'ready_to_start': False,
            'tableau': PlayerTableau.factory(user.name).data,
            'view_options': {},
        }

        return GamePlayer(data)

    @property
    def deck_id(self):
        return self.data['deck_id']

    @deck_id.setter
    def deck_id(self, deck_id):
        self.data['deck_id'] = deck_id

    @property
    def eliminated(self):
        return self.data.get('eliminated', False)

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
        return bool(self.data.get('deck_id', False))

    @property
    def tableau(self):
        return PlayerTableau(self.data['tableau'])

    @property
    def view_options(self):
        return self.data['view_options']


class GameState(object):
    def __init__(self, json):
        self.data = json

    @staticmethod
    def factory(game_id: int, name: str):
        data = {
            'id': game_id,
            'history': [],
            'cards': {},  # id -> card.data
            'name': name,
            'next_id': 1,
            'players': [],
            'phase': GamePhase.untap,

            'turn': 0,  # Whose turn is it? (player_idx)
            'priority': 0,  # Which player has priority? (player_idx)

            'latest_version': 1, # Safety check to avoid data overwrites

            'started': False,
            'finished': False,  # deprecated; use self.is_finished()
            'winner': '',  # deprecated; user self.result_for(user)
        }

        game = GameState(data)

        data['history'].append({
            'id': game.next_id(),
            'delta': [],
            'message': 'Game Created',
            'player': 'GM',
        })

        return game

    def add_player(self, player_id):
        player = GamePlayer.factory(player_id)
        for i in range(4):
            player.view_options[f"collapse_player-{i}-sideboard"] = True
        self.data['players'].append(player.data)

    def card(self, card_id):
        return GameCard(self.data['cards'][card_id])

    def is_finished(self):
        # This is legacy for games where finished was being set manually.
        if self.data['finished']:
            return True

        if 'started' in self.data and not self.data['started']:
            return False

        return [x.eliminated for x in self.players].count(False) <= 1

    def make_card(self, cube_card_id):
        card = GameCard.factory(self.next_id(), cube_card_id)
        self.data['cards'][card.id()] = card.data
        return card.id()

    @property
    def latest_version(self):
        return self.data.get('latest_version')

    def load_deck(self, player_id, maindeck, sideboard, command):
        if not isinstance(maindeck[0], int):
            raise ValueError("Decks should be lists of GameCard.id int values.")

        player = self.player_by_id(player_id)
        tableau = player.tableau

        if len(tableau.library) > 0:
            raise RuntimeError("User has a library. Loading a deck would overwrite it.")

        tableau.data['library'] = maindeck[:]
        tableau.data['sideboard'] = sideboard[:]
        tableau.data['command'] = command[:]

        random.shuffle(tableau.data['library'])

        for card_id in (tableau.library + tableau.sideboard + tableau.command):
            card = self.card(card_id)
            card.data['owner'] = player.name

        for card_id in tableau.sideboard:
            card = self.card(card_id)
            card.data['visibility'].append(player.name)

        for card_id in tableau.command:
            card = self.card(card_id)
            card.data['visibility'] = sorted([x.name for x in self.players])

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

    def priority_player(self):
        player_idx = self.data['priority']
        return self.players[player_idx]

    @property
    def players(self):
        return [GamePlayer(x) for x in self.data['players']]

    def player_names(self):
        return [x.name for x in self.players]

    def ready_to_start(self):
        return all([x.ready_to_start for x in self.players])

    def result_for(self, user_id):
        """
        Return either win, loss, draw, or in_progress
        """
        elim = { x.id: x.eliminated for x in self.players }
        num_alive = list(elim.values()).count(False)

        if num_alive == 0:
            return 'draw'
        elif num_alive > 1:
            return 'in_progress'
        elif elim.get(user_id) == True:
            return 'loss'
        else:
            return 'win'

    def seat_index_by_user_id(self, user_id):
        for i, p in enumerate(self.players):
            if int(p.id) == int(user_id):
                return i

        return -1

    def start_game(self):
        self.data['started'] = True
        self.data['turn'] = random.randrange(len(self.players))
        self.data['priority'] = self.data['turn']
        first_player_name = self.players[self.data['turn']].data['name']
        self.data['history'] += [
            {
                'id': self.next_id(),
                'delta': [],
                'message': f"{first_player_name} randomly chosen to go first",
                'player': 'GM',
            },
            {
                'id': self.next_id(),
                'delta': [],
                'message': "Reminders!",
                'player': 'GM',
            },
            {
                'id': self.next_id(),
                'delta': [],
                'message': "1. Declare your persona",
                'player': 'GM',
            },
            {
                'id': self.next_id(),
                'delta': [],
                'message': "2. Companions?",
                'player': 'GM',
            },
            {
                'id': self.next_id(),
                'delta': [],
                'message': "3. Hidden Agendas?",
                'player': 'GM',
            },
            {
                'id': self.next_id(),
                'delta': [],
                'message': "4. Other weird stuff?",
                'player': 'GM',
            },
        ]


    # Deprecated
    def is_winner(self, user):
        return self.winner() == user.name

    # Deprecated
    def winner(self):
        return self.data.get('winner', '')
