import difflib
from collections import UserDict
from collections import UserList

from app.util.scryfall import CardConsts


class FaceDiff(UserDict):
    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]
        else:
            return []


class CardDiff(UserList):
    def __getitem__(self, index):
        if index < len(self.data):
            return self.data[index]
        else:
            return FaceDiff()

    def dumps(self):
        import json
        a = []
        for elem in self.data:
            a.append(dict(elem))
        return json.dumps(a, indent=2)
        

def card_diff(card1, card2):

    faces1 = card1.card_faces().copy()
    faces2 = card2.card_faces().copy()

    diffs = CardDiff()
    
    for i in range(max(len(faces1),len(faces2))):
        face_diff = FaceDiff()
        diffs.append(face_diff)

        if len(faces1) <= i:
            faces1.append({})
            
        if len(faces2) <= i:
            faces2.append({})

        for key in CardConsts.FACE_KEYS:
            diff = list(difflib.ndiff(
                faces1[i].get(key, '').split('\n'),
                faces2[i].get(key, '').split('\n'),
            ))

            diff = [x.rstrip() for x in diff if len(x.rstrip()) > 1]
            diff = [(x[0], x[2:]) for x in diff if x.startswith('+ ') or x.startswith('- ')]
            face_diff[key] = diff

    return diffs
