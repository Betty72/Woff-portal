from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'qwerty'  # Use a strong random key in production

# Upload folder config
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///walkers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Make sure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Model for dog walkers
class DogWalker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    city = db.Column(db.String(100))
    experience = db.Column(db.Integer)
    availability = db.Column(db.String(100))
    dog_size = db.Column(db.String(50))
    photo = db.Column(db.String(200))

# Allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home
@app.route('/')
def home():
    return render_template('home.html')

# Register walker
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        city = request.form['city']
        experience = request.form['experience']
        availability = request.form.getlist('availability')
        dog_size = request.form['dog_size']

        profile_pic = request.files['profile_pic']
        filename = ''
        if profile_pic and allowed_file(profile_pic.filename):
            filename = secure_filename(profile_pic.filename)
            profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_walker = DogWalker(
            name=name,
            city=city,
            experience=experience,
            availability=', '.join(availability),
            dog_size=dog_size,
            photo=filename
        )
        db.session.add(new_walker)
        db.session.commit()

        return render_template('thank_you.html', name=name)

    return render_template('register.html')

# View walkers
@app.route('/walkers')
def walkers():
    all_walkers = DogWalker.query.all()
    return render_template('walkers.html', walkers=all_walkers)

# Remove walker (admin only)
@app.route('/remove_walker', methods=['POST'])
def remove_walker():
    if not session.get('admin'):
        return redirect(url_for('login'))

    walker_id = int(request.form['walker_id'])
    walker = DogWalker.query.get(walker_id)

    if walker:
        db.session.delete(walker)
        db.session.commit()

    return redirect(url_for('walkers'))

# Admin login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == 'admin123':
            session['admin'] = True
            return redirect(url_for('walkers'))
        else:
            return render_template('login.html', error='Incorrect password')
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
    # Deploy trigger

