import difflib


class BaseDiffer(object):
    def __init__(self, old_json, new_json):
        self.old = old_json
        self.new = new_json

    def _ndiff(self, field):
        return list(difflib.ndiff(
            self.old.get(field, '').strip().split('\n'),
            self.new.get(field, '').strip().split('\n'),
        ))


class FaceDiffer(BaseDiffer):
    pass
    

class CardDiffer(object):
    def __init__(self, old_card, new_card):
        self.old_card = old_card
        self.new_card = new_card
        self.face_differs = self._init_face_diffs()

    def _init_face_diffs(self):
        num_faces = max(len(self.old_card.card_faces()), len(self.new_card.card_faces()))
        face_diffs = []
        for i in range(num_faces):
            old_face = self._get_face(self.old_card, i)
            new_face = self._get_face(self.new_card, i)
            face_diffs.append(FaceDiffer(old_face, new_face))

        return face_diffs

    @staticmethod
    def _get_face(card, face_index):
        faces = card.card_faces()
        if len(faces) <= face_index:
            new_face = {}
        else:
            new_face = faces[face_index]

