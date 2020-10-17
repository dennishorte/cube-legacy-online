import difflib

from app.util.scryfall import CardConsts


def card_diff(card1, card2):

    faces1 = card1.card_faces()
    faces2 = card2.card_faces()

    diffs = []
    
    for i in range(max(len(faces1),len(faces2))):
        if len(faces1) <= i:
            diffs.append({'face_added': faces2[i]})
            continue
            
        if len(faces2) <= i:
            diffs.append({'face_removed': faces1[i]})
            continue

        face_diff = {}
        diffs.append(face_diff)
        for key in CardConsts.FACE_KEYS:
            diff = list(difflib.ndiff(
                faces1[i].get(key, '').split('\n'),
                faces2[i].get(key, '').split('\n'),
            ))

            diff = [x for x in diff if x.startswith('+') or x.startswith('-')]
            if diff:
                face_diff[key] = diff

    import json
    print(json.dumps(diffs, indent=2))
