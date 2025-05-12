from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
import csv
import os

app = Flask(__name__)
app.secret_key = 'qwerty'  # In production, use a strong random key

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('home.html')

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

        fieldnames = ['name', 'city', 'experience', 'availability', 'dog_size', 'photo']
        new_row = {
            'name': name,
            'city': city,
            'experience': experience,
            'availability': ', '.join(availability),
            'dog_size': dog_size,
            'photo': filename
        }

        file_exists = os.path.isfile('registrations.csv')
        with open('registrations.csv', mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            if os.path.getsize('registrations.csv') == 0:
                writer.writeheader()

            writer.writerow(new_row)

        return render_template('thank_you.html', name=name)

    return render_template('register.html')

@app.route('/walkers')
def walkers():
    walkers = []
    with open('registrations.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if any(row.values()):  # Skip empty rows
                walkers.append(row)

    return render_template('walkers.html', walkers=walkers)

@app.route('/remove_walker', methods=['POST'])
def remove_walker():
    if not session.get('admin'):
        return redirect(url_for('login'))

    walker_id = int(request.form['walker_id'])

    walkers = []
    with open('registrations.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if any(row.values()):
                walkers.append(row)

    if 0 <= walker_id < len(walkers):
        del walkers[walker_id]

    fieldnames = ['name', 'city', 'experience', 'availability', 'dog_size', 'photo']
    with open('registrations.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for walker in walkers:
            writer.writerow(walker)

    return redirect(url_for('walkers'))

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

