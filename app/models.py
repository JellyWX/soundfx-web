from app import db
from sqlalchemy_json import NestedMutableJson
from sqlalchemy.dialects.mysql import MEDIUMBLOB

Favorites = db.Table('favorites',
                     db.Column('user_id', db.BigInteger),
                     db.Column('sound_id', db.Integer, db.ForeignKey('sounds.id', ondelete='cascade')),
                     )


class Server(db.Model):
    __tablename__ = 'servers'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    prefix = db.Column(db.String(5))
    roles = db.Column(NestedMutableJson)
    sounds = db.relationship('Sound', backref='server', lazy='dynamic')


class Sound(db.Model):
    __tablename__ = 'sounds'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)

    src = db.Column(MEDIUMBLOB, nullable=False)
    plays = db.Column(db.Integer)

    server_id = db.Column(db.BigInteger, db.ForeignKey('servers.id'))
    uploader_id = db.Column(db.BigInteger)

    public = db.Column(db.Boolean, nullable=False, default=True)
