


class CubeData(object):
    def __init__(self, cube):
        self.cube = cube

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
