from flask import redirect, render_template, request, url_for, session, abort, flash, send_file
from app import app, discord, db
from app.models import Sound, User
import os
import requests
import json
import zlib
import io


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
def play():
    id = request.args.get('id')
    user = session.get('user')
    requests.get('http://localhost:7765/play?id={}&user={}'.format(id, user))
    return ('OK', 200)


@app.route('/dashboard/')
def dashboard():
    if not discord.authorized:
        return redirect(url_for('oauth'))

    user = discord.get('api/users/@me').json()

    session['user'] = user['id']
    query = request.args.get('query') or ''
    page = int_or_none(request.args.get('page')) or 0

    u = User.query.filter(User.id == user['id']).first()

    s = Sound.query.filter((Sound.public == True) & (Sound.src != None) & (Sound.name.ilike('%{}%'.format(query))))
    max_pages = s.count() // app.config['RESULTS_PER_PAGE']

    s = s.slice(page*app.config['RESULTS_PER_PAGE'], (page+1)*app.config['RESULTS_PER_PAGE'])

    return render_template('dashboard.html', user_sounds=u.sounds, public=s, q=query, p=page, max_pages=max_pages, title='Dashboard')


@app.route('/audio/')
def audio():
    id = request.args.get('id')
    s = Sound.query.get(id)

    return send_file(io.BytesIO(zlib.decompress(s.src)), mimetype='audio/ogg', attachment_filename='{}.ogg'.format(s.name))
