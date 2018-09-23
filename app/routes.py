from flask import redirect, render_template, url_for
from app import app

@app.route('/')
def index():
    return redirect(url_for('help'))

@app.route('/help/')
def help():
    return render_template('index.html', title='Help')
