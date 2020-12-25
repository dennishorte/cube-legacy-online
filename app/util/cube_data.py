
class CardPickInfo(object):
    def __init__(self, card):
        self.card = card
        self.picks = []

    def average_pick(self, normalize=9):
        total = 0
        for pick in self.picks:
            total += ((pick.pick_number + 1) / pick.pack_size) * normalize

        return total / self.num_picks()

    def first_picks(self):
        return len([x for x in self.picks if x.pick_number == 0])

    def num_picks(self):
        return len(self.picks)


class CubeData(object):
    def __init__(self, cube):
        self.cube = cube
        self.info = self._pick_info()

    def creature_types(self):
        types = {}

        for card in self.cube.cards():
            for face in card.card_faces():
                if 'creature' in face['type_line'].lower():
                    subtypes = self._extract_subtypes(face['type_line'])
                    for type in subtypes:
                        types.setdefault(type, []).append(card)

        for key in types:
            types[key] = list(set(types[key]))
            types[key].sort(key=lambda x: x.name())

        types_list = list(types.items())
        types_list.sort()

        return types_list

    def first_picks(self):
        more_than_one = [x for x in self.info.values() if x.first_picks() > 1]
        counts = [(x.card.name(), x.first_picks()) for x in more_than_one]
        counts.sort(key=lambda x: (-x[1], x[0]))
        return counts

    def highest_picks(self):
        sorted_picks = [x for x in self.info.values() if len(x.picks) > 1]
        sorted_picks.sort(key=lambda x: x.average_pick(), reverse=True)
        return sorted_picks[:20]

    def _extract_subtypes(self, type_line):
        for i in range(len(type_line)):
            if not type_line[i].isalpha() and not type_line[i].isspace():
                return type_line[i+1:].strip().split()

        return []

    def _pick_info(self):
        from app.models.cube_models import CubeCard
        from app.models.draft_models import Draft
        from app.models.draft_models import PackCard

        drafts = [
            x.id for x in Draft.query.filter(Draft.cube_id == self.cube.id).all()
            if x.complete
        ]
        picks = PackCard.query.filter(PackCard.draft_id.in_(drafts)).all()

        pick_info = {}
        for pick in picks:
            info = pick_info.setdefault(pick.cube_card.latest_id, CardPickInfo(pick.cube_card))
            info.picks.append(pick)

        return pick_info
