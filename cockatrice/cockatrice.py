"""
Spec Definition:
https://github.com/Cockatrice/Cockatrice/wiki/Custom-Cards-&-Sets#to-add-your-own-custom-cards-follow-these-steps


"""

import datetime
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement

from app.models import ModCard


ALL_LAYOUTS = [
    'adventure',
    'aftermath',
    'augment',
    'flip',
    'host',
    'leveler',
    'meld',
    'modal_dfc',
    'normal',
    'planar',
    'saga',
    'scheme',
    'split',
    'transform',
    'vanguard',
]


def export_to_cockatrice(cards: list):
    """
    Output format:
    <?xml version="1.0" encoding="UTF-8"?>
    <cockatrice_carddatabase version="4">
      <sets>
        <set>...</set>
      </sets>
      <cards>
        <card>...</card>
        <card>...</card>
        <card>...</card>
      </cards>
    </cockatrice_carddatabase>
    """
    root = Element('cockatrice_carddatabase')
    root.set('version', '4')

    sets = SubElement(root, 'sets')
    cards = SubElement(root, 'cards')

    _add_sets_xml(sets)
    _add_cards_xml(cards)

    return root.tostring()
    

def _add_sets_xml(root):
    """
    Output format:
    <set>
      <name>clo</name>
      <longname>Cube Legacy Online: {date}</longname>
      <settype>Custom</settype>
      <releasedate>{date}</releasedate>
    </set>
    """
    name = SubElement(root, 'name')
    longname = SubElement(root, 'longname')
    settype = SubElement(root, 'settype')
    releasedate = SubElement(root, 'releasedate')

    date_str = str(datetime.date.today())
    
    name.text = 'clo'
    longname.text = 'Cube Legacy Online: {}'.format(date_str)
    settype.text = 'Custom'
    releasedate.text = date_str
    
    
def _add_cards_xml(root):
    for card in ModCard.latest():
        _add_cards_xmls(card, root)


def _add_card_xmls(card, root):
    """
    A card can have multiple faces, so this sometimes returns multiple cards.
    """
    faces = [card]
    if card.faces:
        raise NotImplementedError()

    for face in faces:
        elem = SubElement(root, 'card')
        _add_card_face_xml(card, elem)


def _add_card_face_xml(face, root):
    """
    Insert correct data for the face into a card.
    Root should be a SubElement of a <cards> element.

    Example output:

    <card>
      <cipt>1</cipt>      <!-- Comes into play tapped -->
      <name>Card name</name>
      <related>Another card name</related>
      <reverse-related>Another card name</reverse-related>
      <set picurl="http://.../image.jpg">XXX</set>
      <tablerow>3</tablerow>
      <text>Card description and oracle text, including actions, effects, etc..</text>
      <token>1</token>
      <upsidedown>1</upsidedown>
      <prop>
        <cmc>1</cmc>
        <coloridentity>R</coloridentity>
        <colors>R</colors>
        <layout>normal</layout>
        <loyalty>4</loyalty>
        <maintype>Instant</maintype>
        <manacost>R</manacost>
        <pt>0/2</pt>
        <side>front</side>
        <type>Instant</type>
      </prop>
    </card>
    """
    set = SubElement(root, 'set')
    name = SubElement(root, 'name')
    text = SubElement(root, 'text')
    prop = SubElement(root, 'prop')
    tablerow = SubElement(root, 'tablerow')

    set.text = 'clo'
    set.set('picurl', card.image_url)
    name.text = card.name
    text.text = card.text
    table_row.text = _get_table_row_for_card(card)

    _make_card_face_props_xml(card, prop)
    
    for related in card.related:
        r = SubElement(root, 'related')
        r.text = related
    
def _add_card_face_props_xml(face, root):
    """
    Inserts all props of the card face into root.
    Root should be a SubElement of a <card> element.
    """
    layout = SubElement(root, 'layout')
    side = SubElement(root, 'side')
    type = SubElement(root, 'type')
    maintype = SubElement(root, 'maintype')
    manacost = SubElement(root, 'manacost')
    cmc = SubElement(root, 'cmc')
    colors = SubElement(root, 'colors')
    coloridentity = SubElement(root, 'coloridentity')
    
    layout.text = face.layout
    side.text = face.face
    type.text = face.type_line
    maintype.text = face.main_type
    manacost.text = face.mana_cost
    cmc.text = face.cmc
    colors.text = face.colors
    coloridentity.text = face.color_identity

    if face.is_creature():
        pt = SubElement(root, 'pt')
        pt.text = '{}/{}'.format(face.power, face.toughness)

    if face.is_planeswalker():
        loyalty = SubElement(root, 'loyalty')
        loyalty.text = face.loyalty
        
        
def _get_table_row_for_card(card):
    if 'land' in card.super_types:
        return 0
    elif 'instant' in card.super_types or 'sorcery' in card.super_types:
        return 3
    elif 'creature' in card.super_types:
        return 2
    else:
        return 1
