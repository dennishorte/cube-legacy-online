

def factions_for_card(card):
    """
    Different faces of a card can belong to different factions.
    returns: [[faction,...], ...]
    """

    card_factions = []

    for face in card.card_faces():
        factions = []
        supertypes, subtypes = _split_types(face['type_line'].lower())

        if 'druid' in subtypes:
            factions.append("Xuc's Circle")

        if 'elemental' in subtypes or 'teenager' in subtypes:
            factions.append("Teenage Firestarters")

        if (
                'servo' in subtypes
                or 'thopter' in subtypes
                or 'construct' in subtypes
                or ('artifact' in supertypes
                    and 'creature' in supertypes
                    and face.get('power') == 0)
        ):
            factions.append("Sai's Robotic Swarm")

        if 'human' in subtypes:
            if face.get('flavor_text'):
                factions.append("Queen Marchesa's Band of Merry Men and Women")
            else:
                factions.append("Syr Konrad's Extremely Serious Debate Group")

        if 'sliver' in subtypes:
            factions.append("Sliver's Front of Judea")

        if 'angel' in subtypes or 'demon' in subtypes or 'dragon' in subtypes:
            factions.append("Kaalia's Army of the Vast")

        card_factions.append(factions)

    return card_factions


def _split_types(type_line):
    # First, split on whitespace to get individual tokens.
    tokens = type_line.strip().split()

    # Find the super/sub type separator
    idx = -1
    for i in range(len(tokens)):
        if not tokens[i].isalpha():
            idx = i
            break

    if idx == -1:
        return tokens, []

    else:
        return tokens[:idx], tokens[idx + 1:]
