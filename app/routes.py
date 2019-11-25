from flask import redirect, render_template, request, url_for, session, abort, flash, send_file
from sqlalchemy.sql.expression import func
from app import app, discord, db, limiter
from app.models import Sound, User, Collection
import os
import requests
import json
import io
import subprocess
import pika

def int_or_none(o):
    try:
        return int(o)
    except:
        return None


@app.errorhandler(500)
def internal_error(error):
    session.clear()
    return "An error has occured! We've made a report, and cleared your cache on this website. If you encounter this error again, please send us a message on Discord!"

@app.route('/')
def index():
    return redirect( url_for('help') )


@app.route('/help/')
def help():
    return render_template('help.html', title='Help')


@app.route('/oauth/')
def oauth():
    session.clear()

    return redirect(url_for('discord.login'))


@app.route('/play/', methods=['POST'])
@limiter.limit('1 per {} seconds'.format(app.config['PLAY_LIMIT']))
def play():
    id = request.args.get('id')
    user = session.get('user') or discord.get('api/users/@me').json().get('user')
    s = Sound.query.filter((Sound.public == True) | (Sound.uploader_id == user)).filter(Sound.id == id).first()

    if all(x is not None for x in (s, user, id)):
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='soundfx')

        channel.basic_publish(exchange='', routing_key='soundfx', body='{},{}'.format(id, user))

        connection.close()

    return ('OK', 200)


@app.route('/fav/', methods=['POST'])
def fav():
    id = int_or_none(request.args.get('id'))
    user = session.get('user') or discord.get('api/users/@me').json().get('user')

    u = User.query.filter(User.id == user).first()
    s = Sound.query.get(id)

    if s in u.favorites:
        u.favorites.remove(s)
        db.session.commit()

        return ('removed', 200)

    else:
        u.favorites.append(s)
        db.session.commit()

        return ('added', 200)


@app.route('/delete/')
def delete():
    id = int_or_none(request.args.get('id'))
    user = session.get('user') or discord.get('api/users/@me').json().get('user')

    u = User.query.filter(User.id == user).first()
    s = Sound.query.get(id)

    if s in u.sounds:
        Sound.query.filter(Sound.id == id).delete(synchronize_session='fetch')
        db.session.commit()

    return redirect(url_for('dashboard'))


@app.route('/dashboard/')
def dashboard():
    if not discord.authorized:
        return redirect(url_for('oauth'))

    user = discord.get('api/users/@me').json()

    session['user'] = user['id']
    query = request.args.get('query') or ''
    page = int_or_none(request.args.get('page')) or 0
    random = int_or_none(request.args.get('random')) or 0

    u = User.query.filter(User.id == user['id']).first()

    if u is None:
        u = User(id=user['id'])
        db.session.add(u)
        db.session.commit()

    if random:
        s = Sound.query.filter((Sound.public == True) & (Sound.src != None) & (Sound.name.ilike('%{}%'.format(query)))).order_by( func.rand() )
    else:
        s = Sound.query.filter((Sound.public == True) & (Sound.src != None) & (Sound.name.ilike('%{}%'.format(query)))).order_by( Sound.name )

    max_pages = s.count() // app.config['RESULTS_PER_PAGE']

    s = s.slice(page*app.config['RESULTS_PER_PAGE'], (page+1)*app.config['RESULTS_PER_PAGE'])

    return render_template('dashboard.html', user=u, public=s, q=query, p=page, max_pages=max_pages, title='Dashboard', random=random)


@app.route('/collections/')
def all_collections():
    collections = Collection.query.all()

    return render_template('all_collections.html', collections=collections)


@app.route('/audio/')
def audio():
    id = request.args.get('id')
    user = session.get('user') or discord.get('api/users/@me').json().get('user')
    s = Sound.query.filter((Sound.public == True) | (Sound.uploader_id == user)).filter(Sound.id == id).first()

    if s is not None:
        sub = subprocess.Popen(('ffmpeg', '-i', '-', '-loglevel', 'error', '-f', 'mp3', 'pipe:1'), stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        stdout = sub.communicate(input=s.src)[0]

        return send_file(io.BytesIO(stdout), mimetype='audio/mp3', attachment_filename='{}.mp3'.format(s.name))

    else:
        return ('Forbidden', 403)


@app.route('/collection/<int:id>')
def view_collection(id: int):
    if not discord.authorized:
        return redirect(url_for('oauth'))

    user = session.get('user') or discord.get('api/users/@me').json().get('user')

    u = User.query.filter(User.id == user).first()

    collection = Collection.query.filter(Collection.id == id).first_or_404()

    return render_template('collections.html', user=u, collection=collection, sounds=collection.sounds)