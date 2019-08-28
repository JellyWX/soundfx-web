from app import db
from sqlalchemy_json import NestedMutableJson
from sqlalchemy.dialects.mysql import LONGBLOB


favorites = db.Table('favorites',
    db.Column('user_id', db.BigInteger, db.ForeignKey('users.id')),
    db.Column('sound_id', db.Integer, db.ForeignKey('sounds.id', ondelete='cascade')),
)

collections_associated = db.Table('collections_associated',
    db.Column('collection_id', db.Integer, db.ForeignKey('collections.id', ondelete='cascade')),
    db.Column('sound_id', db.Integer, db.ForeignKey('sounds.id', ondelete='cascade')),
)

class Server(db.Model):
    __tablename__ = 'servers'

    map_id = db.Column( db.Integer, primary_key=True)
    id = db.Column( db.BigInteger, unique=True)
    prefix = db.Column( db.String(5) )
    roles = db.Column( NestedMutableJson )
    sounds = db.relationship('Sound', backref='server', lazy='dynamic')


class Sound(db.Model):
    __tablename__ = 'sounds'

    id = db.Column( db.Integer, primary_key=True )
    name = db.Column( db.String(20) )

    src = db.Column( LONGBLOB )
    plays = db.Column( db.Integer )

    server_id = db.Column( db.BigInteger, db.ForeignKey('servers.id') )
    uploader_id = db.Column( db.BigInteger, db.ForeignKey('users.id') )

    public = db.Column( db.Boolean, nullable=False, default=True )


class Collection(db.Model):
    __tablename__ = 'collections'

    id = db.Column( db.Integer, primary_key=True )
    name = db.Column( db.String(32) )
    creator = db.Column( db.String(32) )
    creation_date = db.Column( db.String(32) )

    description = db.Column( db.Text )

    sounds = db.relationship('Sound', secondary=collections_associated)


class User(db.Model):
    __tablename__ = 'users'

    map_id = db.Column( db.Integer, primary_key=True)
    id = db.Column( db.BigInteger, unique=True)

    join_sound_id = db.Column( db.Integer, db.ForeignKey('sounds.id', ondelete='SET NULL'), nullable=True )
    join_sound = db.relationship('Sound', foreign_keys=[join_sound_id])

    sounds = db.relationship('Sound', backref='owner', foreign_keys=[Sound.uploader_id])
    favorites = db.relationship('Sound', secondary=favorites, backref='favorites')
