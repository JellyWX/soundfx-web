from app import db
from sqlalchemy_json import NestedMutableJson
from sqlalchemy.dialects.mysql import LONGBLOB


class Server(db.Model):
    __tablename__ = 'servers'

    map_id = db.Column( db.Integer, primary_key=True)
    id = db.Column( db.BigInteger, unique=True)
    prefix = db.Column( db.String(5) )
    roles = db.Column( NestedMutableJson )
    sounds = db.relationship('Sound', backref='server', lazy='dynamic')

    def __repr__(self):
        return '<Server {}>'.format(self.id)


class Sound(db.Model):
    __tablename__ = 'sounds'

    id = db.Column( db.Integer, primary_key=True )
    name = db.Column( db.String(20) )

    url = db.Column( db.Text )
    src = db.Column( LONGBLOB )
    last_used = db.Column( db.Integer )
    plays = db.Column( db.Integer )

    server_id = db.Column( db.BigInteger, db.ForeignKey('servers.id') )
    uploader_id = db.Column( db.BigInteger, db.ForeignKey('users.id') )

    public = db.Column( db.Boolean, nullable=False, default=True )

    big = db.Column( db.Boolean, nullable=False, default=False )


class User(db.Model):
    __tablename__ = 'users'

    map_id = db.Column( db.Integer, primary_key=True)
    id = db.Column( db.BigInteger, unique=True)

    join_sound_id = db.Column( db.Integer, db.ForeignKey('sounds.id', ondelete='SET NULL'), nullable=True )
    join_sound = db.relationship('Sound', foreign_keys=[join_sound_id] )

    sounds = db.relationship('Sound', backref='user', foreign_keys=[Sound.uploader_id])

    def __repr__(self):
        return '<User {}>'.format(self.id)
