from flask import redirect, render_template, request, url_for, session, jsonify, abort
from app import app, discord, db
from app.models import Sound, Favorites


def int_or_none(o):
    try:
        return int(o)

    except:
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


@app.route('/terms/')
def terms_page():
    return render_template('terms.html', title='Terms of Service')


@app.route('/privacy/')
def privacy_page():
    return render_template('privacy.html', title='Privacy Policy')


@app.route('/oauth/')
def oauth():
    session.clear()

    return redirect(url_for('discord.login'))


@app.route('/api/search/', methods=['GET'])
def search_sounds():
    query = request.args.get('query') or ''
    page = int_or_none(request.args.get('page')) or 0

    sounds = Sound.query.filter((Sound.public == True) & (Sound.name.like('%{}%'.format(query)))) \
        .order_by(Sound.name)

    max_pages = sounds.count() // app.config['RESULTS_PER_PAGE']

    sounds_slice = sounds.slice(page * app.config['RESULTS_PER_PAGE'], (page + 1) * app.config['RESULTS_PER_PAGE'])

    return jsonify({'sounds': [sound.to_dict() for sound in sounds_slice], 'first_page': 0, 'last_page': max_pages})


@app.route('/api/favorites/', methods=['POST', 'DELETE', 'GET'])
def favorites():
    user_id = session.get('user') or discord.get('api/users/@me').json().get('user')

    if user_id is None:
        abort(401)

    else:
        if request.method == 'GET':
            user_favorites = db.session.query(Favorites).join(Sound).filter(Favorites.user_id == user_id)

            return jsonify({'sounds': [Sound.query.get(fav.sound_id).to_dict() for fav in user_favorites]})

        elif (sound_id := request.json.get('sound_id')) is not None:
            if request.method == 'DELETE':
                q = db.session.query(Favorites) \
                    .filter_by(user_id=int(user_id), sound_id=sound_id) \
                    .delete(synchronize_session='fetch')

                db.session.commit()

                return '', 201

            else:  # method is POST
                f = db.session.query(Favorites) \
                    .filter(Favorites.user_id == user_id) \
                    .filter(Favorites.sound_id == sound_id)

                if f.first() is None:
                    f = Favorites(user_id=user_id, sound_id=sound_id)
                    db.session.add(f)

                    db.session.commit()

                return '', 201

        else:
            abort(400)


@app.route('/api/user_sounds/', methods=['GET', 'DELETE'])
def user_sounds():
    user_id = session.get('user') or discord.get('api/users/@me').json().get('user')

    if user_id is None:
        abort(401)

    else:
        if request.method == 'DELETE':
            if (sound_id := request.args.get('sound_id')) is not None:
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
def get_sound():
    if (sound_id := request.args.get('sound_id')) is not None:
        try:
            user_id = session.get('user') or discord.get('api/users/@me').json().get('user')
        except:
            user_id = None

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
