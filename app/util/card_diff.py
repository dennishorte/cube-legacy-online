import difflib
import functools


class BaseDiffer(object):
    def __init__(self, old_json, new_json):
        self.old = old_json
        self.new = new_json
        self.no_changes = self.old == self.new

    def __getitem__(self, field):
        diff = self._ndiff(field)
        diff = [x for x in diff if not x.startswith('  ') and not x.startswith('? ')]
        return diff

    def changed_fields(self):
        if self.no_changes:
            return {}

        changes = {}

        for field in self.old:
            if self.is_changed(field):
                changes[field] = True

        return changes

    def is_changed(self, field):
        if self.no_changes:
            return False

        for line in self._ndiff(field):
            if not line.startswith('  '):
                return True

        return False

    def plus(self, field):
        return [x for x in self._ndiff(field) if x.startswith('+ ')]

    @functools.lru_cache
    def _ndiff(self, field):
        return list(difflib.ndiff(
            self.old.get(field, '').strip().split('\n'),
            self.new.get(field, '').strip().split('\n'),
        ))


class FaceDiffer(BaseDiffer):
    def is_flavor(self):
        """Only flavor text is changed."""
        changes = self.changed_fields()
        return len(changes) == 1 and 'flavor_text' in changes

    def is_minor(self):
        if self.is_significant() or self.is_flavor():
            return False

        return len(self.changed_fields()) > 0

    def is_significant(self):
        # Card face added or removed is always significant.
        if (self.old or self.new) and (not self.old or not self.new):
            return True

        if self.is_changed('oracle_text') \
           or self.is_changed('mana_cost') \
           or self.is_changed('power') \
           or self.is_changed('toughness') \
           or self.is_changed('loyalty'):

            return True

        return False

    def oracle_text_ndiff(self):
        simplified = []
        for diff in self._ndiff('oracle_text'):
            if diff.startswith('+ '):
                if diff.strip() != '+':
                    simplified.append(diff)
            elif diff.startswith('? ') or diff.startswith('- '):
                pass
            else:
                simplified.append(diff[2:])
        return simplified

    def summary(self):
        summary = []

        def field_plus(field):
            return [f"+ {field}: {x[2:]}" for x in self.plus(field)]

        def pt():
            power = self.plus('power')
            tough = self.plus('toughness')

            if power or tough:
                return [f"+ pt: {self.new['power']} / {self.new['toughness']}"]
            else:
                return []

        summary += field_plus('name')
        summary += field_plus('mana_cost')
        summary += field_plus('type_line')
        summary += field_plus('flavor_text')
        summary += self['oracle_text']
        summary += field_plus('loyalty')
        summary += pt()

        return summary


class CardDiffer(object):
    def __init__(self, old_card, new_card):
        self.old_card = old_card
        self.new_card = new_card
        self.face_differs = []

        self._init_face_diffs()

    def face(self, index):
        if index < len(self.face_differs):
            return self.face_differs[index]

    def is_changed(self, field):
        return any([x.is_changed(field) for x in self.face_differs])

    def is_minor(self):
        """
        True if the diff has some change, but not likely to impact gameplay.
        A common example is when just the name is changed.
        """
        return (
            not self.is_significant()
            and any([x.is_minor() for x in self.face_differs])
        )

    def is_significant(self):
        """True if the diff is likely to have an effect on gameplay."""
        return any([x.is_significant() for x in self.face_differs])

    def _init_face_diffs(self):
        for i in range(10):
            old_face = self._get_face(self.old_card, i)
            new_face = self._get_face(self.new_card, i)
            self.face_differs.append(FaceDiffer(old_face, new_face))

    def _get_face(self, card, face_index):
        faces = card.card_faces()
        if len(faces) <= face_index:
            return {}
        else:
            return faces[face_index]
