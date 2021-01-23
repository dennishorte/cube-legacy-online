from app import db
from app.models.cube_models import Cube
from app.models.user_models import User
from app.util import cube_util


def basic_lands_cube():
    cube = Cube.query.filter(Cube.name == 'basic lands').first()

    if not cube:
        cube = Cube()
        cube.name = 'basic lands'
        cube.admin = True
        cube.active = False
        cube.style_a = 'standard'
        cube.created_by_id = starter_user().id
        db.session.add(cube)
        db.session.commit()

        # Import the basic lands
        basic_names = ['Forest', 'Island', 'Mountain', 'Plains', 'Swamp', 'Wastes']
        cube_util.add_cards_to_cube(cube.id, basic_names, starter_user())

    return cube


def scryfall_cube():
    cube = Cube.query.filter(Cube.name == 'scryfall').first()

    if not cube:
        cube = Cube()
        cube.name = 'scryfall'
        cube.admin = True
        cube.active = False
        cube.style_a = 'standard'
        cube.created_by_id = starter_user().id
        db.session.add(cube)
        db.session.commit()

    return cube


def starter_user():
    user = User.query.filter(User.name == 'starter').first()

    if not user:
        user = User()
        user.name = 'starter'
        db.session.add(user)
        db.session.commit()

    return user
