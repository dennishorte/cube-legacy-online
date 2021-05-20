
class DraftInfo(object):
    def __init__(self, data):
        assert isinstance(data, dict), "Data must be of type dict"
        self.data = data

    ############################################################
    # Setup Functions

    def name_set(self, name):
        self.data['name'] = name

    def user_add(self, user):
        self.data.setdefault('user_ids', []).append(user.id)

    ############################################################
    # Draft Functions

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

    def user_decline(self, user):
        pass

    def user_ids(self):
        return self.data['user_ids']

    def waiting(self, user):
        return True

    ############################################################
    # Debug Functions

    def dump(self):
        import json
        json.dumps(self.data, indent=2, sort_keys=True)


# class PackDraft(DraftInfo):
#     DRAFT_STYLE = 'pack'

#     @classmethod
#     def factory(cls, **kwargs):
#         data = super().factory(**kwargs)
#         data['cube_id'] = kwargs['cube'].id
#         data['num_packs'] = kwargs['num_packs']
#         data['pack_size'] = kwargs['pack_size']
#         data['picks_per_pack'] = kwargs.get('picks_per_pack', 1)
#         data['scar_rounds'] = kwargs.get('scar_rounds', '')
#         data['packs'] = pack_maker(
#             cube = kwargs['cube'],
#             num_packs = data['num_packs'],
#             pack_size = data['pack_size'],
#         )

#         return PackDraft(data)

#     @property
#     def num_packs(self):
#         return self.data['num_packs']

#     @property
#     def pack_size(self):
#         return self.data['pack_size']

#     @property
#     def picks_per_pack(self):
#         return self.data['picks_per_pack']

#     @property
#     def scar_rounds(self):
#         return self.data['scar_rounds']


# class RotisserieDraft(DraftInfo):
#     DRAFT_STYLE = 'rotisserie'

#     @classmethod
#     def factory(cls, **kwargs):
#         data = super().factory(**kwargs)
#         data['cube_id'] = kwargs['cube'].id
#         data['cards'] = cls._make_card_data(kwargs['cube'])
