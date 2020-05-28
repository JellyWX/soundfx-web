from flask import redirect, render_template, request, url_for, session, send_file
from sqlalchemy.sql.expression import func
from app import app, discord, db
from app.models import Sound, Favorites
import io
import subprocess


def int_or_none(o):
    try:
        return int(o)
    except:
        return None


@app.errorhandler(500)
def internal_error(error):
    session.clear()
    return "An error has occured! We've made a report, and cleared your cache on this website. " \
           "If you encounter this error again, please send us a message on Discord!"


@app.route('/')
def index():
    return redirect(url_for('help'))


@app.route('/help/')
def help():
    return render_template('help.html', title='Help')


@app.route('/oauth/')
def oauth():
    session.clear()

    return redirect(url_for('discord.login'))


@app.route('/fav/', methods=['POST'])
def fav():
    id = int_or_none(request.args.get('id'))
    user = session.get('user') or discord.get('api/users/@me').json().get('user')

    f = db.session.query(Favorites).filter(Favorites.c.user_id == user).filter(Favorites.c.sound_id == id)

    if f.first() is None:
        f.delete(synchronize_session='fetch')
        db.session.commit()

        return ('removed', 200)

    else:
        f = Favorites(user_id=user, sound_id=id)
        db.session.add(f)
        db.session.commit()

        return ('added', 200)


@app.route('/delete/')
def delete():
    id = int_or_none(request.args.get('id'))
    user = session.get('user') or discord.get('api/users/@me').json().get('user')

    s = Sound.query.filter(Sound.uploader_id == user).filter(Sound.id == id).delete(synchronize_session='fetch')
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

    if random:
        s = Sound.query.filter(
            (Sound.public == True) & (Sound.name.ilike('%{}%'.format(query)))).order_by(
            func.rand())
    else:
        s = Sound.query.filter(
            (Sound.public == True) & (Sound.name.ilike('%{}%'.format(query)))).order_by(
            Sound.name)

    max_pages = s.count() // app.config['RESULTS_PER_PAGE']

    s = s.slice(page * app.config['RESULTS_PER_PAGE'], (page + 1) * app.config['RESULTS_PER_PAGE'])

    f = [x.sound_id for x in db.session.query(Favorites).filter(Favorites.c.user_id == user['id']).all()]
    f_s = Sound.query.filter(Sound.id.in_(f))
    user_sounds = Sound.query.filter(Sound.uploader_id == user['id'])

    return render_template('dashboard.html', favorites=f_s, public=s, q=query, p=page, max_pages=max_pages,
                           sounds=user_sounds, title='Dashboard', random=random)


@app.route('/audio/')
def audio():
    id = request.args.get('id')
    user = session.get('user') or discord.get('api/users/@me').json().get('user')
    s = Sound.query.filter((Sound.public == True) | (Sound.uploader_id == user)).filter(Sound.id == id).first()

    if s is not None:
        sub = subprocess.Popen(('ffmpeg', '-i', '-', '-loglevel', 'error', '-f', 'mp3', 'pipe:1'),
                               stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        stdout = sub.communicate(input=s.src)[0]

        return send_file(io.BytesIO(stdout), mimetype='audio/mp3', attachment_filename='{}.mp3'.format(s.name))

    else:
        return ('Forbidden', 403)
