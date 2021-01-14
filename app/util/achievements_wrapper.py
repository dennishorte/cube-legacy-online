from app.models.cube_models import Achievement
from app.models.cube_models import Cube


class AchievementsWrapper(object):
    def __init__(self, achs, filters=[], apply_not=False):
        self.achs = achs
        self.apply_not = apply_not
        self.filters = filters

    def __iter__(self):
        return iter(self.get())

    def get(self):
        filtered = []
        for ach in self.achs:
            if all([f(ach) for f in self.filters]):
                filtered.append(ach)

        return filtered

    @staticmethod
    def from_cube(cube):
        if isinstance(cube, int):
            cube = Cube.query.get(cube)

        return AchievementsWrapper(Achievement.query.filter(Achievement.cube_id == cube.id).all())

    def andnot(self):
        return AchievementsWrapper(self.achs, self.filters, apply_not=True)

    def available(self):
        return self._with_filter(lambda x: x.available())

    def faction(self):
        return self._with_filter(lambda x: x.available() and 'faction' in x.conditions.lower())

    def levelup(self):
        return self._with_filter(lambda x: bool(x.levelup))

    def linked(self):
        return self._with_filter(lambda x: bool(x.linked_cards))

    def standard(self):
        return self.available().andnot().linked().andnot().levelup()

    def starred_by(self, user_id):
        return self._with_filter(lambda x: x.starred_by_user(user_id))

    def unlocked(self):
        return self._with_filter(lambda x: not x.available())

    def unlocked_by(self, user_id):
        return self._with_filter(lambda x: x.unlocked_by_id == user_id)

    def _with_filter(self, f):
        if self.apply_not:
            g = lambda x: not f(x)
            return AchievementsWrapper(self.achs, self.filters + [g])
        else:
            return AchievementsWrapper(self.achs, self.filters + [f])
