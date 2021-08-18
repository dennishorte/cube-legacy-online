import enum


class DraftFaceUp(enum.Enum):
    false = 0
    true = 1
    optional = 2


class Layout(enum.Enum):
    normal = 0  # A standard Magic card with one face
    split = 1  # A split-faced card
    flip = 2  # Cards that invert vertically with the flip keyword
    transform = 3  # Double-sided cards that transform
    modal_dfc = 4  # Double-sided cards that can be played either-side
    meld = 5  # Cards with meld parts printed on the back
    leveler = 6  # Cards with Level Up
    saga = 7  # Saga-type cards
    adventure = 8  # Cards with an Adventure spell part
    # planar = 9  # Plane and Phenomenon-type cards
    # scheme = 10  # Scheme-type cards
    vanguard = 11  # Vanguard-type cards
    token = 12  # Token cards
    # double_faced_token = 13  # Tokens with another token printed on the back
    # emblem = 14  # Emblem cards
    augment = 15  # Cards with Augment
    host = 16  # Host-type cards
    # art_series = 17  # Art Series collectable double-faced cards
    # double_sided = 18  # A Magic card with two sides that are unrelated
    clazz = 19

    @classmethod
    def choices(cls):
        return [x.name for x in cls]

    @staticmethod
    def simple_faced_layout(layout):
        if isinstance(layout, Layout):
            layout = layout.name

        return layout in (
            Layout.normal.name,
            Layout.leveler.name,
            Layout.saga.name,
            Layout.meld.name,
            Layout.token.name,
            Layout.host.name,
            Layout.augment.name,
            Layout.vanguard.name,
            "class",
        )

    @staticmethod
    def split_faced_layout(layout):
        if isinstance(layout, Layout):
            layout = layout.name

        return layout in (
            Layout.split.name,
            Layout.adventure.name,
        )

    @staticmethod
    def double_sided_layout(layout):
        if isinstance(layout, Layout):
            layout = layout.name

        return layout in (
            Layout.flip.name,
            Layout.transform.name,
            Layout.modal_dfc.name,
        )
