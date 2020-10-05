from app.models import *


class DraftDebugger(object):
    def __init__(self, draft_id):
        self.draft = Draft.query.get(draft_id)

        self.participants = Participant.query.filter(Participant.draft_id == draft_id).all()
        self.participants.sort(key=lambda x: x.seat)
        
        self.packs = Pack.query.filter(Pack.draft_id == draft_id).all()

        self.pack_cards = PackCard.query.filter(PackCard.draft_id == draft_id).all()

    def packs_for(self, participant):
        packs = [x for x in self.packs if x.seat_number == participant.seat]
        packs.sort(key=lambda x: x.pack_number)
        return packs

    def picked_cards_for_pack(self, pack):
        cards = [x for x in self.pack_cards if x.pack_id == pack.id and x.picked()]
        cards.sort(key=lambda x: x.pick_number)
        return cards

    def unpicked_cards_for_pack(self, pack):
        cards = [x for x in self.pack_cards if x.pack_id == pack.id and not x.picked()]
        return cards
