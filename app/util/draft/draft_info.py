from app.util.draft.pack_maker import pack_maker


class DraftInfoBase(object):
    DRAFT_STYLE = None

    def __init__(self, data):
        self.data = data

    @classmethod
    def factory(cls, **kwargs):
        return {
            'name': kwargs['name'],
            'style': cls.DRAFT_STYLE,
            'user_ids': kwargs.get('user_ids', []),
        }

    @staticmethod
    def from_data(data):
        if data['style'] == 'pack':
            return PackDraft(data)
        elif data['style'] == 'rotisserie':
            return RotisserieDraft(data)
        else:
            raise ValueError(f"Unknown draft style: {data['style']}")

    def is_complete(self):
        pass

    def json_string(self):
        return json.dumps(self.data)

    def num_picked(self):
        pass

    def pick_do(self, user, card_id):
        pass

    def pick_undo(self, user):
        pass

    def user_add(self, user):
        pass

    def user_decline(self, user):
        pass

    def user_ids(self):
        return self.data['user_ids']


class PackDraft(DraftInfoBase):
    DRAFT_STYLE = 'pack'

    @classmethod
    def factory(cls, **kwargs):
        data = super().factory(**kwargs)
        data['cube_id'] = kwargs['cube'].id
        data['num_packs'] = kwargs['num_packs']
        data['pack_size'] = kwargs['pack_size']
        data['picks_per_pack'] = kwargs.get('picks_per_pack', 1)
        data['scar_rounds'] = kwargs.get('scar_rounds', '')
        data['packs'] = pack_maker(
            cube = kwargs['cube'],
            num_packs = data['num_packs'],
            pack_size = data['pack_size'],
        )

        return PackDraft(data)

    @property
    def num_packs(self):
        return self.data['num_packs']

    @property
    def pack_size(self):
        return self.data['pack_size']

    @property
    def picks_per_pack(self):
        return self.data['picks_per_pack']

    @property
    def scar_rounds(self):
        return self.data['scar_rounds']


class RotisserieDraft(DraftInfoBase):
    DRAFT_STYLE = 'rotisserie'

    @classmethod
    def factory(cls, **kwargs):
        data = super().factory(**kwargs)
        data['cube_id'] = kwargs['cube'].id
        data['cards'] = cls._make_card_data(kwargs['cube'])
