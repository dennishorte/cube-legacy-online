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
from lxml.etree import parse
from lxml.etree import tostring

from app.util.card_util import CardConsts
from app.util.enum import Layout


CONTRAPTION_SET_NAME = 'CNTRP'

def contraption_extractor(cards_xml_filename):
    tree = parse(cards_xml_filename)
    root = tree.getroot()
    cards = root.find('cards')

    # Set up special contraptions set
    root.remove(root.find('sets'))
    sets = SubElement(root, 'sets')
    _add_sets_xml(
        sets,
        set_name=CONTRAPTION_SET_NAME,
        set_longname='Contraptions',
        set_settype='Custom Contraptions',
    )

    _filter_non_contraptions(cards)


    return tostring(tree, xml_declaration=True, encoding='UTF-8').decode('utf-8')


def _filter_non_contraptions(cards):
    count = 1
    for card in cards.findall('card'):
        text = card.find('prop').find('type').text
        if text.startswith('Artifact ') and text.endswith(' Contraption'):
            token_elem = SubElement(card, 'token')
            token_elem.text = '1'
            card.find('tablerow').text = '-1'
            card.find('set').text = CONTRAPTION_SET_NAME
            card.find('name').text = f"CN{count:02} {card.find('name').text}"
            count += 1
        else:
            card.getparent().remove(card)


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

    _add_sets_xml(
        sets_root,
        set_name='clo',
        set_longname=f'Cube Legacy Online',
        set_settype='Custom Legacy',
    )
    _add_cards_xml(cards_root, cube)

    return tostring(root, pretty_print=True).decode('utf-8')


def _add_sets_xml(
        root,
        set_name,
        set_longname,
        set_settype,
):
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

    name.text = set_name
    longname.text = set_longname
    settype.text = set_settype
    releasedate.text = date_str


def _add_cards_xml(root, cube):
    for card in cube.cards():
        _add_one_card_xmls(card, root)


def _add_one_card_xmls(card, root):
    """
    In cockatrice, each physical face of a card has its own object. This doesn't apply
    to the abstract faces of a split card like Fire // Ice or to adventures, only to
    cards that physically have two sides with game content on them.
    (All physical cards have two physical sides.)
    """
    card_data = card.get_json()
    layout = card_data['layout']
    is_scarred = card.version != 1

    if Layout.double_sided_layout(layout):
        face_indices = [0, 1]
    else:
        face_indices = [0]

    for face_index in face_indices:
        card_elem = SubElement(root, 'card')

        name = SubElement(card_elem, 'name')
        name.text = _card_name(
            card_data,
            face_index,
            scarred=is_scarred,
        )

        set = SubElement(card_elem, 'set')
        set.text = 'clo'
        set.set('picurl', _image_url(card_data, face_index))

        tablerow = SubElement(card_elem, 'tablerow')
        tablerow.text = _table_row(card_data, face_index)

        text = SubElement(card_elem, 'text')
        text.text = _oracle_text(card, card_data, face_index)

        # Props
        props = SubElement(card_elem, 'prop')

        props_cmc = SubElement(props, 'cmc')
        props_cmc.text = str(card_data['cmc'])

        props_layout = SubElement(props, 'layout')
        props_layout.text = layout

        props_side = SubElement(props, 'side')
        props_side.text = 'front' if face_index == 0 else 'back'

        props_maintype = SubElement(props, 'maintype')
        props_maintype.text = _card_maintype(card)

        mana_cost = _mana_cost(card_data, face_index)
        if mana_cost:  # Most double faced cards have no mana cost on the back.
            props_manacost = SubElement(props, 'manacost')
            props_manacost.text = mana_cost

        card_face = card_data['card_faces'][face_index]
        if card_face.get('loyalty'):
            props_loyalty = SubElement(props, 'loyalty')
            props_loyalty.text = card_face['loyalty']

        if card_face.get('power'):
            props_pt = SubElement(props, 'pt')
            props_pt.text = '{}/{}'.format(card_face['power'], card_face['toughness'])

        if Layout.double_sided_layout(layout):
            other_face_index = (face_index + 1) % 2
            related = SubElement(card_elem, 'related')
            related.set('attach', 'attach')
            related.text = _card_name(card_data, other_face_index, is_scarred)


def _card_name(card_data, face_index, scarred):
    layout = card_data['layout']

    if Layout.simple_faced_layout(layout) or Layout.double_sided_layout(layout):
        name = card_data['card_faces'][face_index]['name']
    elif Layout.split_faced_layout(layout):
        name = card_data['name']
    else:
        raise NotImplementedError(f"Don't have a Cockatrice pattern for image_url of: {layout}")

    if scarred:
        return f"{name}++"
    else:
        return f"{name}'"


def _card_maintype(card):
    front_face = card.card_faces()[0]
    type_line = front_face['type_line'].lower()
    for typ in CardConsts.CARD_TYPES:
        if typ in type_line:
            return typ.title()

    return 'UNKNOWN'


def _image_url(card_data, face_index):
    layout = card_data['layout']

    if Layout.simple_faced_layout(layout) \
       or Layout.split_faced_layout(layout) \
       or Layout.double_sided_layout(layout):

        return card_data['card_faces'][face_index]['image_url']

    else:
        raise NotImplementedError(f"Don't have a Cockatrice pattern for image_url of: {layout}")


def _mana_cost(card_data, face_index):
    layout = card_data['layout']

    if Layout.simple_faced_layout(layout) or Layout.split_faced_layout(layout):
        mana_costs = [_clean_mana_cost(x['mana_cost']) for x in card_data['card_faces']]
        return ' // '.join(mana_costs)
    elif Layout.double_sided_layout(layout):
        return _clean_mana_cost(card_data['card_faces'][face_index].get('mana_cost', ''))
    else:
        raise NotImplementedError(f"Don't have a Cockatrice pattern for image_url of: {layout}")


def _oracle_text(card, card_data, face_index):
    layout = card_data['layout']

    if Layout.simple_faced_layout(layout) or Layout.double_sided_layout(layout):
        rules_text = card_data['card_faces'][face_index]['oracle_text']
    elif Layout.split_faced_layout(layout):
        rules_text = card_data['oracle_text']
    else:
        raise NotImplementedError(f"Don't have a Cockatrice pattern for text of: {layout}")

    achievement_lines = []
    if card.linked_achievements():
        achievement_lines.append("\n\n***")
        for ach in card.linked_achievements():
            achievement_lines.append(ach.conditions)

        rules_text += '\n\n'.join(achievement_lines)

    return rules_text


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


def _table_row(card_data, face_index):
    types = card_data['card_faces'][face_index]['type_line'].lower().split()

    if 'land' in types:
        return '0'
    elif 'instant' in types or 'sorcery' in types:
        return '3'
    elif 'creature' in types:
        return '2'
    else:
        return '1'
