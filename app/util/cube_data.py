
class CubeData(object):
    def __init__(self, cube):
        self.cube = cube

        self.pick_info()

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

    def _extract_subtypes(self, type_line):
        for i in range(len(type_line)):
            if not type_line[i].isalpha() and not type_line[i].isspace():
                return type_line[i+1:].strip().split()

        return []

    def pick_info(self):
        from app.models.cube_models import CubeCard
        from app.models.draft_models import Draft
        from app.models.draft_models import PackCard

        drafts = [
            x.id for x in Draft.query.filter(Draft.cube_id == self.cube.id).all()
            if x.complete
        ]
        picks = PackCard.query.filter(PackCard.draft_id.in_(drafts)).all()

        first_picks = {}
        for pick in picks:
            if pick.pick_number == 0:
                group_id = pick.cube_card.latest_id
                if group_id not in first_picks:
                    first_picks[group_id] = 0
                first_picks[group_id] += 1

        first_picks = {id: count for id, count in first_picks.items() if count > 1}

        first_picks_ready = []
        for card_id, count in first_picks.items():
            card = CubeCard.query.get(card_id)
            first_picks_ready.append((card.name(), count))

        first_picks_ready.sort(key=lambda x: (-x[1], x[0]))

        return first_picks_ready
