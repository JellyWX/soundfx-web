from flask import redirect, render_template, request, url_for, session, abort, flash
from app import app, discord, db
import os
import requests
import json


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
    guild = session.get('guild')
    user = session.get('user')
    requests.get('http://localhost:7765/play?id={}&guild={}&user={}'.format(id, guild, user))

@app.route('/dashboard/')
def dashboard():
    if not discord.authorized:
        return redirect(url_for('oauth'))

    return render_template('dashboard.html')
