import json
import unittest

from app.util import scryfall
from app.util.card_util import CardConsts


def _normal_example():
    return json.loads("""
{"object":"card","id":"ce711943-c1a1-43a0-8b89-8d169cfb8e06","oracle_id":"4457ed35-7c10-48c8-9776-456485fdf070","multiverse_ids":[489532],"tcgplayer_id":216484,"cardmarket_id":473959,"name":"Lightning Bolt","lang":"en","released_at":"2020-07-17","uri":"https://api.scryfall.com/cards/ce711943-c1a1-43a0-8b89-8d169cfb8e06","scryfall_uri":"https://scryfall.com/card/jmp/342/lightning-bolt?utm_source=api","layout":"normal","highres_image":true,"image_uris":{"small":"https://c1.scryfall.com/file/scryfall-cards/small/front/c/e/ce711943-c1a1-43a0-8b89-8d169cfb8e06.jpg?1601078281","normal":"https://c1.scryfall.com/file/scryfall-cards/normal/front/c/e/ce711943-c1a1-43a0-8b89-8d169cfb8e06.jpg?1601078281","large":"https://c1.scryfall.com/file/scryfall-cards/large/front/c/e/ce711943-c1a1-43a0-8b89-8d169cfb8e06.jpg?1601078281","png":"https://c1.scryfall.com/file/scryfall-cards/png/front/c/e/ce711943-c1a1-43a0-8b89-8d169cfb8e06.png?1601078281","art_crop":"https://c1.scryfall.com/file/scryfall-cards/art_crop/front/c/e/ce711943-c1a1-43a0-8b89-8d169cfb8e06.jpg?1601078281","border_crop":"https://c1.scryfall.com/file/scryfall-cards/border_crop/front/c/e/ce711943-c1a1-43a0-8b89-8d169cfb8e06.jpg?1601078281"},"mana_cost":"{R}","cmc":1.0,"type_line":"Instant","oracle_text":"Lightning Bolt deals 3 damage to any target.","colors":["R"],"color_identity":["R"],"keywords":[],"legalities":{"standard":"not_legal","future":"not_legal","historic":"not_legal","pioneer":"not_legal","modern":"legal","legacy":"legal","pauper":"legal","vintage":"legal","penny":"not_legal","commander":"legal","brawl":"not_legal","duel":"legal","oldschool":"not_legal"},"games":["paper"],"reserved":false,"foil":false,"nonfoil":true,"oversized":false,"promo":false,"reprint":true,"variation":false,"set":"jmp","set_name":"Jumpstart","set_type":"draft_innovation","set_uri":"https://api.scryfall.com/sets/0f6ccf25-a627-4263-86df-5757137f1696","set_search_uri":"https://api.scryfall.com/cards/search?order=set\u0026q=e%3Ajmp\u0026unique=prints","scryfall_set_uri":"https://scryfall.com/sets/jmp?utm_source=api","rulings_uri":"https://api.scryfall.com/cards/ce711943-c1a1-43a0-8b89-8d169cfb8e06/rulings","prints_search_uri":"https://api.scryfall.com/cards/search?order=released\u0026q=oracleid%3A4457ed35-7c10-48c8-9776-456485fdf070\u0026unique=prints","collector_number":"342","digital":false,"rarity":"uncommon","flavor_text":"The sparkmage shrieked, calling on the rage of the storms of his youth. To his surprise, the sky responded with a fierce energy he'd never thought to see again.","card_back_id":"0aeebaf5-8c7d-4636-9e82-8c27447861f7","artist":"Christopher Moeller","artist_ids":["21e10012-06ae-44f2-b38d-3824dd2e73d4"],"illustration_id":"013e7eda-ef8e-44cd-9832-4033d9de1c34","border_color":"black","frame":"2015","full_art":false,"textless":false,"booster":true,"story_spotlight":false,"edhrec_rank":675,"preview":{"source":"Wizards of the Coast","source_uri":"https://magic.wizards.com/en/articles/archive/card-image-gallery/jumpstart","previewed_at":"2020-06-19"},"prices":{"usd":"1.84","usd_foil":null,"eur":"2.50","eur_foil":null,"tix":null},"related_uris":{"gatherer":"https://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid=489532","tcgplayer_decks":"https://decks.tcgplayer.com/magic/deck/search?contains=Lightning+Bolt\u0026page=1\u0026utm_campaign=affiliate\u0026utm_medium=api\u0026utm_source=scryfall","edhrec":"https://edhrec.com/route/?cc=Lightning+Bolt","mtgtop8":"https://mtgtop8.com/search?MD_check=1\u0026SB_check=1\u0026cards=Lightning+Bolt"},"purchase_uris":{"tcgplayer":"https://shop.tcgplayer.com/product/productsearch?id=216484\u0026utm_campaign=affiliate\u0026utm_medium=api\u0026utm_source=scryfall","cardmarket":"https://www.cardmarket.com/en/Magic/Products/Singles/Jumpstart/Lightning-Bolt?referrer=scryfall\u0026utm_campaign=card_prices\u0026utm_medium=text\u0026utm_source=scryfall","cardhoarder":"https://www.cardhoarder.com/cards?affiliate_id=scryfall\u0026data%5Bsearch%5D=Lightning+Bolt\u0026ref=card-profile\u0026utm_campaign=affiliate\u0026utm_medium=card\u0026utm_source=scryfall"}}
""".strip())

def _flip_example():
    return json.loads("""
{"object":"card","id":"f2ddf1a3-e6fa-4dd0-b80d-1a585b51b934","oracle_id":"b269770d-2b48-4314-a1b8-0d79beb879a3","multiverse_ids":[78695],"mtgo_id":21239,"mtgo_foil_id":21240,"tcgplayer_id":12067,"cardmarket_id":12086,"name":"Kitsune Mystic // Autumn-Tail, Kitsune Sage","lang":"en","released_at":"2004-10-01","uri":"https://api.scryfall.com/cards/f2ddf1a3-e6fa-4dd0-b80d-1a585b51b934","scryfall_uri":"https://scryfall.com/card/chk/28/kitsune-mystic-autumn-tail-kitsune-sage?utm_source=api","layout":"flip","highres_image":true,"image_uris":{"small":"https://c1.scryfall.com/file/scryfall-cards/small/front/f/2/f2ddf1a3-e6fa-4dd0-b80d-1a585b51b934.jpg?1562765664","normal":"https://c1.scryfall.com/file/scryfall-cards/normal/front/f/2/f2ddf1a3-e6fa-4dd0-b80d-1a585b51b934.jpg?1562765664","large":"https://c1.scryfall.com/file/scryfall-cards/large/front/f/2/f2ddf1a3-e6fa-4dd0-b80d-1a585b51b934.jpg?1562765664","png":"https://c1.scryfall.com/file/scryfall-cards/png/front/f/2/f2ddf1a3-e6fa-4dd0-b80d-1a585b51b934.png?1562765664","art_crop":"https://c1.scryfall.com/file/scryfall-cards/art_crop/front/f/2/f2ddf1a3-e6fa-4dd0-b80d-1a585b51b934.jpg?1562765664","border_crop":"https://c1.scryfall.com/file/scryfall-cards/border_crop/front/f/2/f2ddf1a3-e6fa-4dd0-b80d-1a585b51b934.jpg?1562765664"},"mana_cost":"{3}{W}","cmc":4.0,"type_line":"Creature — Fox Wizard // Legendary Creature — Fox Wizard","power":"2","toughness":"3","colors":["W"],"color_identity":["W"],"keywords":[],"card_faces":[{"object":"card_face","name":"Kitsune Mystic","mana_cost":"{3}{W}","type_line":"Creature — Fox Wizard","oracle_text":"At the beginning of the end step, if Kitsune Mystic is enchanted by two or more Auras, flip it.","power":"2","toughness":"3","artist":"Jim Murray","artist_id":"1c906f9b-5bbe-4643-8f5c-90eb1c7f0c43","illustration_id":"82ab75e1-da49-4252-9ae7-00df976acf39"},{"object":"card_face","name":"Autumn-Tail, Kitsune Sage","mana_cost":"","type_line":"Legendary Creature — Fox Wizard","oracle_text":"{1}: Attach target Aura attached to a creature to another creature.","power":"4","toughness":"5","artist":"Jim Murray","artist_id":"1c906f9b-5bbe-4643-8f5c-90eb1c7f0c43"}],"legalities":{"standard":"not_legal","future":"not_legal","historic":"not_legal","pioneer":"not_legal","modern":"legal","legacy":"legal","pauper":"not_legal","vintage":"legal","penny":"legal","commander":"legal","brawl":"not_legal","duel":"legal","oldschool":"not_legal"},"games":["paper","mtgo"],"reserved":false,"foil":true,"nonfoil":true,"oversized":false,"promo":false,"reprint":false,"variation":false,"set":"chk","set_name":"Champions of Kamigawa","set_type":"expansion","set_uri":"https://api.scryfall.com/sets/6183d21f-a0af-4118-ba58-aca1d8719c01","set_search_uri":"https://api.scryfall.com/cards/search?order=set\u0026q=e%3Achk\u0026unique=prints","scryfall_set_uri":"https://scryfall.com/sets/chk?utm_source=api","rulings_uri":"https://api.scryfall.com/cards/f2ddf1a3-e6fa-4dd0-b80d-1a585b51b934/rulings","prints_search_uri":"https://api.scryfall.com/cards/search?order=released\u0026q=oracleid%3Ab269770d-2b48-4314-a1b8-0d79beb879a3\u0026unique=prints","collector_number":"28","digital":false,"rarity":"rare","card_back_id":"0aeebaf5-8c7d-4636-9e82-8c27447861f7","artist":"Jim Murray","artist_ids":["1c906f9b-5bbe-4643-8f5c-90eb1c7f0c43"],"illustration_id":"82ab75e1-da49-4252-9ae7-00df976acf39","border_color":"black","frame":"2003","full_art":false,"textless":false,"booster":true,"story_spotlight":false,"edhrec_rank":9468,"prices":{"usd":"0.48","usd_foil":"1.99","eur":"0.09","eur_foil":"0.49","tix":"0.01"},"related_uris":{"gatherer":"https://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid=78695","tcgplayer_decks":"https://decks.tcgplayer.com/magic/deck/search?contains=Kitsune+Mystic\u0026page=1\u0026utm_campaign=affiliate\u0026utm_medium=api\u0026utm_source=scryfall","edhrec":"https://edhrec.com/route/?cc=Kitsune+Mystic","mtgtop8":"https://mtgtop8.com/search?MD_check=1\u0026SB_check=1\u0026cards=Kitsune+Mystic"},"purchase_uris":{"tcgplayer":"https://shop.tcgplayer.com/product/productsearch?id=12067\u0026utm_campaign=affiliate\u0026utm_medium=api\u0026utm_source=scryfall","cardmarket":"https://www.cardmarket.com/en/Magic/Products/Singles/Champions-of-Kamigawa/Kitsune-Mystic?referrer=scryfall\u0026utm_campaign=card_prices\u0026utm_medium=text\u0026utm_source=scryfall","cardhoarder":"https://www.cardhoarder.com/cards/21239?affiliate_id=scryfall\u0026ref=card-profile\u0026utm_campaign=affiliate\u0026utm_medium=card\u0026utm_source=scryfall"}}
""".strip())

def _transform_example():
    return json.loads(r"""
{"object":"card","id":"02d6d693-f1f3-4317-bcc0-c21fa8490d38","oracle_id":"594f6881-c059-46f8-aa4e-7151d502de73","multiverse_ids":[398434,398435],"mtgo_id":57880,"mtgo_foil_id":57881,"tcgplayer_id":100191,"cardmarket_id":283370,"name":"Jace, Vryn's Prodigy // Jace, Telepath Unbound","lang":"en","released_at":"2015-07-17","uri":"https://api.scryfall.com/cards/02d6d693-f1f3-4317-bcc0-c21fa8490d38","scryfall_uri":"https://scryfall.com/card/ori/60/jace-vryns-prodigy-jace-telepath-unbound?utm_source=api","layout":"transform","highres_image":true,"cmc":2.0,"type_line":"Legendary Creature — Human Wizard // Legendary Planeswalker — Jace","color_identity":["U"],"keywords":["Mill"],"card_faces":[{"object":"card_face","name":"Jace, Vryn's Prodigy","mana_cost":"{1}{U}","type_line":"Legendary Creature — Human Wizard","oracle_text":"{T}: Draw a card, then discard a card. If there are five or more cards in your graveyard, exile Jace, Vryn's Prodigy, then return him to the battlefield transformed under his owner's control.","colors":["U"],"power":"0","toughness":"2","flavor_text":"\"People's thoughts just come to me. Sometimes I don't know if it's them or me thinking.\"","artist":"Jaime Jones","artist_id":"92f6c2c1-fa57-4b52-99c4-0fd866c13dc9","illustration_id":"ea8de167-ee93-4282-95b4-d82291dbfe1f","image_uris":{"small":"https://c1.scryfall.com/file/scryfall-cards/small/front/0/2/02d6d693-f1f3-4317-bcc0-c21fa8490d38.jpg?1590511929","normal":"https://c1.scryfall.com/file/scryfall-cards/normal/front/0/2/02d6d693-f1f3-4317-bcc0-c21fa8490d38.jpg?1590511929","large":"https://c1.scryfall.com/file/scryfall-cards/large/front/0/2/02d6d693-f1f3-4317-bcc0-c21fa8490d38.jpg?1590511929","png":"https://c1.scryfall.com/file/scryfall-cards/png/front/0/2/02d6d693-f1f3-4317-bcc0-c21fa8490d38.png?1590511929","art_crop":"https://c1.scryfall.com/file/scryfall-cards/art_crop/front/0/2/02d6d693-f1f3-4317-bcc0-c21fa8490d38.jpg?1590511929","border_crop":"https://c1.scryfall.com/file/scryfall-cards/border_crop/front/0/2/02d6d693-f1f3-4317-bcc0-c21fa8490d38.jpg?1590511929"}},{"object":"card_face","name":"Jace, Telepath Unbound","mana_cost":"","type_line":"Legendary Planeswalker — Jace","oracle_text":"+1: Up to one target creature gets -2/-0 until your next turn.\n−3: You may cast target instant or sorcery card from your graveyard this turn. If that spell would be put into your graveyard this turn, exile it instead.\n−9: You get an emblem with \"Whenever you cast a spell, target opponent mills five cards.\"","colors":["U"],"color_indicator":["U"],"loyalty":"5","artist":"Jaime Jones","artist_id":"92f6c2c1-fa57-4b52-99c4-0fd866c13dc9","illustration_id":"8ce7af86-2a0b-426b-8f7b-a49d6c956141","image_uris":{"small":"https://c1.scryfall.com/file/scryfall-cards/small/back/0/2/02d6d693-f1f3-4317-bcc0-c21fa8490d38.jpg?1590511929","normal":"https://c1.scryfall.com/file/scryfall-cards/normal/back/0/2/02d6d693-f1f3-4317-bcc0-c21fa8490d38.jpg?1590511929","large":"https://c1.scryfall.com/file/scryfall-cards/large/back/0/2/02d6d693-f1f3-4317-bcc0-c21fa8490d38.jpg?1590511929","png":"https://c1.scryfall.com/file/scryfall-cards/png/back/0/2/02d6d693-f1f3-4317-bcc0-c21fa8490d38.png?1590511929","art_crop":"https://c1.scryfall.com/file/scryfall-cards/art_crop/back/0/2/02d6d693-f1f3-4317-bcc0-c21fa8490d38.jpg?1590511929","border_crop":"https://c1.scryfall.com/file/scryfall-cards/border_crop/back/0/2/02d6d693-f1f3-4317-bcc0-c21fa8490d38.jpg?1590511929"}}],"all_parts":[{"object":"related_card","id":"02d6d693-f1f3-4317-bcc0-c21fa8490d38","component":"combo_piece","name":"Jace, Vryn's Prodigy // Jace, Telepath Unbound","type_line":"Legendary Creature — Human Wizard // Legendary Planeswalker — Jace","uri":"https://api.scryfall.com/cards/02d6d693-f1f3-4317-bcc0-c21fa8490d38"},{"object":"related_card","id":"458e37b1-a849-41ae-b63c-3e09ffd814e4","component":"combo_piece","name":"Jace, Telepath Unbound Emblem","type_line":"Emblem — Jace","uri":"https://api.scryfall.com/cards/458e37b1-a849-41ae-b63c-3e09ffd814e4"}],"legalities":{"standard":"not_legal","future":"not_legal","historic":"not_legal","pioneer":"legal","modern":"legal","legacy":"legal","pauper":"not_legal","vintage":"legal","penny":"not_legal","commander":"legal","brawl":"not_legal","duel":"legal","oldschool":"not_legal"},"games":["paper","mtgo"],"reserved":false,"foil":true,"nonfoil":true,"oversized":false,"promo":false,"reprint":false,"variation":false,"set":"ori","set_name":"Magic Origins","set_type":"core","set_uri":"https://api.scryfall.com/sets/0eeb9a9a-20ac-404d-b55f-aeb7a43a7f62","set_search_uri":"https://api.scryfall.com/cards/search?order=set\u0026q=e%3Aori\u0026unique=prints","scryfall_set_uri":"https://scryfall.com/sets/ori?utm_source=api","rulings_uri":"https://api.scryfall.com/cards/02d6d693-f1f3-4317-bcc0-c21fa8490d38/rulings","prints_search_uri":"https://api.scryfall.com/cards/search?order=released\u0026q=oracleid%3A594f6881-c059-46f8-aa4e-7151d502de73\u0026unique=prints","collector_number":"60","digital":false,"rarity":"mythic","card_back_id":"0aeebaf5-8c7d-4636-9e82-8c27447861f7","artist":"Jaime Jones","artist_ids":["92f6c2c1-fa57-4b52-99c4-0fd866c13dc9"],"border_color":"black","frame":"2015","frame_effects":["originpwdfc"],"full_art":false,"textless":false,"booster":true,"story_spotlight":false,"edhrec_rank":1313,"prices":{"usd":"17.72","usd_foil":"46.31","eur":"16.00","eur_foil":"33.49","tix":"3.64"},"related_uris":{"gatherer":"https://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid=398434","tcgplayer_decks":"https://decks.tcgplayer.com/magic/deck/search?contains=Jace%2C+Vryn%27s+Prodigy\u0026page=1\u0026utm_campaign=affiliate\u0026utm_medium=api\u0026utm_source=scryfall","edhrec":"https://edhrec.com/route/?cc=Jace%2C+Vryn%27s+Prodigy","mtgtop8":"https://mtgtop8.com/search?MD_check=1\u0026SB_check=1\u0026cards=Jace%2C+Vryn%27s+Prodigy"},"purchase_uris":{"tcgplayer":"https://shop.tcgplayer.com/product/productsearch?id=100191\u0026utm_campaign=affiliate\u0026utm_medium=api\u0026utm_source=scryfall","cardmarket":"https://www.cardmarket.com/en/Magic/Products/Singles/Magic-Origins/Jace-Vryns-Prodigy-Jace-Telepath-Unbound?referrer=scryfall\u0026utm_campaign=card_prices\u0026utm_medium=text\u0026utm_source=scryfall","cardhoarder":"https://www.cardhoarder.com/cards/57880?affiliate_id=scryfall\u0026ref=card-profile\u0026utm_campaign=affiliate\u0026utm_medium=card\u0026utm_source=scryfall"}}
""".strip())


class ConvertToCloStandardNormalFrameTestCase(unittest.TestCase):
    def setUp(self):
        self.example = _normal_example()

    def test_has_expected_root_fields(self):
        scryfall.convert_to_clo_standard_json(self.example)

        # Post-conditions
        for key in scryfall.CardConsts.ROOT_KEYS:
            self.assertIn(key, self.example)

    def test_has_expected_face_fields(self):
        scryfall.convert_to_clo_standard_json(self.example)
        face = self.example['card_faces'][0]

        # Post-conditions
        self.assertEqual(1, len(self.example['card_faces']))

        for face in self.example['card_faces']:
            for key in scryfall.CardConsts.FACE_KEYS:
                self.assertIn(key, face)


class ConvertToCloStandardFlipFrameTestCase(unittest.TestCase):
    def setUp(self):
        self.example = _flip_example()

    def test_has_expected_root_fields(self):
        scryfall.convert_to_clo_standard_json(self.example)

        # Post-conditions
        for key in scryfall.CardConsts.ROOT_KEYS:
            self.assertIn(key, self.example)

    def test_has_expected_face_fields(self):
        scryfall.convert_to_clo_standard_json(self.example)

        # Post-conditions
        self.assertEqual(2, len(self.example['card_faces']))

        for face in self.example['card_faces']:
            for key in scryfall.CardConsts.FACE_KEYS:
                self.assertIn(key, face)


class ConvertToCloStandardTransformFrameTestCase(unittest.TestCase):
    def setUp(self):
        self.example = _transform_example()

    def test_has_expected_root_fields(self):
        scryfall.convert_to_clo_standard_json(self.example)

        # Post-conditions
        for key in scryfall.CardConsts.ROOT_KEYS:
            self.assertIn(key, self.example)

    def test_has_expected_face_fields(self):
        scryfall.convert_to_clo_standard_json(self.example)

        # Post-conditions
        self.assertEqual(2, len(self.example['card_faces']))

        for face in self.example['card_faces']:
            for key in scryfall.CardConsts.FACE_KEYS:
                self.assertIn(key, face)
