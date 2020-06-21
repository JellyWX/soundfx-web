from flask import redirect, render_template, request, url_for, session, jsonify, abort
from app import app, discord, db, limiter
from app.models import Sound, Favorites


def int_or_none(o):
    try:
        return int(o)

    except ValueError:
        return None


@app.errorhandler(500)
def internal_error(_error):
    session.clear()
    return "An error has occured! We've made a report, and cleared your cache on this website. " \
           "If you encounter this error again, please send us a message on Discord!"


@app.route('/')
def index():
    return redirect(url_for('help_page'))


@app.route('/help/')
def help_page():
    return render_template('help.html', title='Help')


@app.route('/oauth/')
def oauth():
    session.clear()

    return redirect(url_for('discord.login'))


@app.route('/api/search/', methods=['GET'])
@limiter.limit('1 per 2 seconds')
def search_sounds():
    query = request.args.get('query') or ''
    page = int_or_none(request.args.get('page')) or 0

    sounds = Sound.query.filter((Sound.public == True) & (Sound.name.ilike('%{}%'.format(query)))) \
        .order_by(Sound.name) \
        .slice(page * app.config['RESULTS_PER_PAGE'], (page + 1) * app.config['RESULTS_PER_PAGE'])

    max_pages = sounds.count() // app.config['RESULTS_PER_PAGE']

    return jsonify({'sounds': [sound.to_dict() for sound in sounds], 'first_page': 0, 'last_page': max_pages})


@app.route('/api/favorites/', methods=['POST', 'DELETE', 'GET'])
def favorites():
    user_id = session.get('user') or discord.get('api/users/@me').json().get('user')

    if user_id is None:
        abort(401)

    else:
        if request.method == 'GET':
            user_favorites = db.session.query(Favorites).join(Sound).filter(Favorites.c.user_id == user_id)

            return jsonify({'sounds': [sound.to_dict() for sound in user_favorites]})

        elif (sound_id := request.json.get('sound_id')) is not None:
            if request.method == 'DELETE':
                db.session.query(Favorites) \
                    .filter(Favorites.c.user_id == user_id) \
                    .filter(Favorites.c.sound_id == sound_id) \
                    .delete(synchronize_session='fetch')

                db.session.commit()

                return '', 201

            else:  # method is POST
                f = db.session.query(Favorites) \
                    .filter(Favorites.c.user_id == user_id) \
                    .filter(Favorites.c.sound_id == sound_id)

                if f.first() is not None:
                    f = Favorites(user_id=user_id, sound_id=sound_id)
                    db.session.add(f)
                    db.session.commit()

                return '', 201

        else:
            abort(400)


@app.route('/api/user_sounds/', methods=['GET', 'DELETE'])
@limiter.limit('1 per 2 seconds')
def user_sounds():
    user_id = session.get('user') or discord.get('api/users/@me').json().get('user')

    if user_id is None:
        abort(401)

    else:
        if request.method == 'DELETE':
            if (sound_id := request.json.get('sound_id')) is not None:
                Sound.query \
                    .filter(Sound.uploader_id == user_id) \
                    .filter(Sound.id == sound_id) \
                    .delete(synchronize_session='fetch')

                db.session.commit()

                return '', 201

            else:
                abort(400)

        else:
            sounds = Sound.query.filter(Sound.uploader_id == user_id)

            return jsonify({'sounds': [sound.to_dict() for sound in sounds]})


@app.route('/api/sound/', methods=['GET'])
@limiter.limit('1 per 5 seconds')
def get_sound():
    if (sound_id := request.json.get('sound_id')) is not None:
        user_id = session.get('user') or discord.get('api/users/@me').json().get('user')

        sound = Sound.query.get(sound_id)

        if sound is not None:
            if sound.public or sound.uploader_id == user_id:
                return jsonify(sound.to_full_dict())

            else:
                abort(403)

        else:
            abort(404)

    else:
        abort(400)


@app.route('/dashboard/')
def dashboard():
    if not discord.authorized:
        return redirect(url_for('oauth'))

    user = discord.get('api/users/@me').json()
    session['user'] = user['id']

    return render_template('dashboard.html', title='Dashboard')
