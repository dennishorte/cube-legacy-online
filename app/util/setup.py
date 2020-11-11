"""
Utility to ensure the basic lands are included in the database for games and set export.
"""
from app import db
from app.models.cube import *
from app.models.user import *
from app.util.cube_util import add_cards_to_cube


def ensure_starter_user():
    user = User.query.filter(User.name == 'starter').first()

    if user:
        return

    print('Creating starter user')

    user = User()
    user.name = 'starter'
    db.session.add(user)
    db.session.commit()
    

def ensure_basic_lands():
    cube = Cube.query.filter(Cube.name == 'basic lands').first()

    if cube:
        return

    print('Loading basic lands')

    starter = User.query.filter(User.name == 'starter').first()

    # Create a cube to hold the basic lands
    cube = Cube()
    cube.name = 'basic lands'
    cube.admin = True
    cube.active = False
    cube.style = CubeStyle.standard
    cube.created_by_id = starter.id
    db.session.add(cube)
    db.session.commit()

    # Import the basic lands
    basic_names = ['Forest', 'Island', 'Mountain', 'Plains', 'Swamp', 'Wastes']
    add_cards_to_cube(cube.id, basic_names, starter)
