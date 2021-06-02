from app.models.cube_models import Achievement
from app.models.cube_models import Cube


class SortKey(object):
    def __init__(self, f, reverse=False):
        self.f = f
        self.reverse = reverse


class AchievementsWrapper(object):
    def __init__(self, achs, filters=[], sort_key=None, apply_not=False):
        self.achs = achs
        self.apply_not = apply_not
        self.filters = filters
        self.sort_key = sort_key

    def __iter__(self):
        return iter(self.get())

    def get(self):
        filtered = []
        for ach in self.achs:
            if all([f(ach) for f in self.filters]):
                filtered.append(ach)

        if self.sort_key:
            filtered.sort(key=self.sort_key.f, reverse=self.sort_key.reverse)

        return filtered

    @staticmethod
    def from_cube(cube):
        if isinstance(cube, int):
            cube = Cube.query.get(cube)

        return AchievementsWrapper(Achievement.query.filter(Achievement.cube_id == cube.id).all())

    def andnot(self):
        return AchievementsWrapper(
            self.achs,
            self.filters,
            apply_not = True,
            sort_key = self.sort_key
        )

    def available(self):
        return self._with_filter(
            lambda x: x.available(),
            sort_key = SortKey(lambda x: (-x.xp, x.name)),
        )

    def linked(self):
        return self._with_filter(lambda x: bool(x.linked_cards))

    def standard(self):
        return self.available().andnot().linked()

    def starred_by(self, user_id):
        return self._with_filter(
            lambda x: x.available() and x.starred_by_user(user_id),
            sort_key = SortKey(lambda x: x.name),
        )

    def unlocked(self):
        return self._with_filter(
            lambda x: not x.available(),
            sort_key = SortKey(lambda x: x.unlocked_timestamp, reverse=True),
        )

    def unlocked_by(self, user_id):
        return self._with_filter(
            lambda x: x.unlocked_by_id == user_id,
            sort_key = SortKey(lambda x: x.unlocked_timestamp, reverse=True),
        )

    def _with_filter(self, f, sort_key=None):
        if self.apply_not:
            g = lambda x: not f(x)
            sort_key = self.sort_key
        else:
            g = f

        return AchievementsWrapper(
            self.achs,
            filters = self.filters + [g],
            sort_key = sort_key or self.sort_key,
        )
