import os
os.environ['FLASK_ENV']='development'


from app import db
from app.models.cube import Achievement


def empty_unlock_json():
    return [
        {
            'timing': '',
            'text': '',
        },
        {
            'timing': '',
            'text': '',
        },
        {
            'timing': '',
            'text': '',
        },
        {
            'timing': '',
            'text': '',
        },
        {
            'timing': '',
            'text': '',
        },
    ]




for ach in Achievement.query.all():
    if ach.unlock_json:
        print('Already converted')
        continue

    data = empty_unlock_json()
    data[0]['timing'] = "After Matches"
    data[0]['text'] = ach.unlock

    ach.set_json(data)
    db.session.add(ach)

db.session.commit()
