"""
Spec Definition:
https://github.com/Cockatrice/Cockatrice/wiki/Custom-Cards-&-Sets#to-add-your-own-custom-cards-follow-these-steps

Example card

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

import datetime
from lxml.etree import Element
from lxml.etree import SubElement
from lxml.etree import tostring

from app.util.enum import Layout


def export_to_cockatrice(cube):
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

    sets_root = SubElement(root, 'sets')
    cards_root = SubElement(root, 'cards')

    _add_sets_xml(sets_root)
    _add_cards_xml(cards_root, cube)

    return tostring(root, pretty_print=True).decode('utf-8')
    

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
    set_elem = SubElement(root, 'set')
    name = SubElement(set_elem, 'name')
    longname = SubElement(set_elem, 'longname')
    settype = SubElement(set_elem, 'settype')
    releasedate = SubElement(set_elem, 'releasedate')

    date_str = str(datetime.date.today())
    
    name.text = 'clo'
    longname.text = 'Cube Legacy Online: {}'.format(date_str)
    settype.text = 'Custom'
    releasedate.text = date_str
    
    
def _add_cards_xml(root, cube):
    for card in cube.cards():
        _add_one_card_xmls(card, root)


def _add_one_card_xmls(card, root):
    """
    In cockatrice, each physical face of a card has its own object. This doesn't apply
    to the abstract faces of a split card like Fire // Ice or to adventures, only to
    cards that physically have two sides with game content on them.
    (All cards have two physical sides.)
    """
    card_data = card.get_json()

    if card_data['layout'] == Layout.normal.name:
        card_face = card_data['card_faces'][0]
        card_elem = SubElement(root, 'card')

        name = SubElement(card_elem, 'name')
        if card.version == 1:
            name.text = "{}'".format(card_face['name'])
        else:
            name.text = "{}++".format(card_face['name'])
        
        set = SubElement(card_elem, 'set')
        set.text = 'clo'
        set.set('picurl', card_face['image_url'])

        tablerow = SubElement(card_elem, 'tablerow')
        tablerow.text = _get_table_row_for_card(card_face)

        text = SubElement(card_elem, 'text')
        text.text = card_face['oracle_text']

        # Props
        props = SubElement(card_elem, 'prop')
        
        props_cmc = SubElement(props, 'cmc')
        props_cmc.text = str(card_data['cmc'])

        props_layout = SubElement(props, 'layout')
        props_layout.text = card_data['layout']

        if 'loyalty' in card_face:
            props_loyalty = SubElement(props, 'loyalty')
            props_loyalty.text = card_face['loyalty']

        if 'mana_cost' in card_face:
            props_manacost = SubElement(props, 'manacost')
            props_manacost.text = _clean_mana_cost(card_face['mana_cost'])
            
        if 'power' in card_face:
            props_pt = SubElement(props, 'pt')
            props_pt.text = '{}/{}'.format(card_face['power'], card_face['toughness'])

        props_side = SubElement(props, 'side')
        props_side.text = 'front'

    else:
        return


def _clean_mana_cost(mana_cost):
    tokens = mana_cost.split('}')
    for i in range(len(tokens)):
        token = tokens[i]
        if not token:
            continue
        elif token.startswith('{') and len(token) == 2:
            tokens[i] = token[1]
        else:
            tokens[i] = token + '}'
    return ''.join(tokens)


def _get_table_row_for_card(card_face):
    types = card_face['type_line'].lower().split()
    
    if 'land' in types:
        return '0'
    elif 'instant' in types or 'sorcery' in types:
        return '3'
    elif 'creature' in types:
        return '2'
    else:
        return '1'
