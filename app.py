from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask import flash
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'
# 💌 Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'betisasg@gmail.com'
app.config['MAIL_PASSWORD'] = 'mpwoltdyxfmghemb'  # Use your generated app password
app.config['MAIL_DEFAULT_SENDER'] = 'betisasg@gmail.com'

mail = Mail(app)


# Hashed version of 'admin123' generated once beforehand
hashed_password = 'pbkdf2:sha256:1000000$d222IyRYnUcVwZPu$15b2588740c2efa31a04e677ec103cf4e2198264cdf00db4dc7662aea9b7a0f8'
# ✅ Context processor goes here
@app.context_processor
def inject_session():
    return dict(session=session)



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
    __tablename__ = 'dog_walker'  # 💥 THIS is the missing line

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    city = db.Column(db.String(100))
    experience = db.Column(db.String(100))
    availability = db.Column(db.String(100))
    dog_size = db.Column(db.String(100))
    photo = db.Column(db.String(200))
    about_me = db.Column(db.Text)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    price_morning = db.Column(db.Integer)
    price_afternoon = db.Column(db.Integer)
    price_evening = db.Column(db.Integer)
    password_hash = db.Column(db.String(256))
class Booking(db.Model):
    __tablename__ = 'booking'

    id = db.Column(db.Integer, primary_key=True)
    walker_id = db.Column(db.Integer, db.ForeignKey('dog_walker.id'), nullable=False)
    date = db.Column(db.String(20))
    time_of_day = db.Column(db.String(20))
    message = db.Column(db.Text)
    owner_email = db.Column(db.String(100))
    owner_phone = db.Column(db.String(20))
    status = db.Column(db.String(20), default='Pending')


    


# Allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home
@app.route('/')
def home():
    walkers = DogWalker.query.limit(3).all()  # Show only 3 for homepage
    return render_template('index.html', walkers=walkers)

# Register walker
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        password = request.form['password']
        hashed_pw = generate_password_hash(password)

        name = request.form['name']
        city = request.form['city']
        experience = request.form['experience']
        availability = request.form.getlist('availability')
        dog_size = request.form['dog_size']
        about_me = request.form['about_me']
        email = request.form['email']
        phone = request.form['phone']
        price_morning = request.form.get('price_morning')
        price_afternoon = request.form.get('price_afternoon')
        price_evening = request.form.get('price_evening')




        # Check required fields manually
        if not name or not email or not city or not experience:
            return render_template("register.html", error="Please fill in all required fields.")

        # Handle file upload
        profile_pic = request.files['profile_pic']
        filename = ''
        if profile_pic and allowed_file(profile_pic.filename):
            filename = secure_filename(profile_pic.filename)
            profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Save to database
        new_walker = DogWalker(
            name=name,
            city=city,
            experience=experience,
            availability=', '.join(availability),
            dog_size=dog_size,
            photo=filename,
            about_me=about_me,
            email=email,
            phone=phone,
            price_morning=price_morning,
            price_afternoon=price_afternoon,
            price_evening=price_evening,
            password_hash=hashed_pw

        )

        db.session.add(new_walker)
        db.session.commit()

        return render_template("register.html", success="Registration successful!")
        

    # GET request
    return render_template('register.html')
    # View walkers
@app.route('/walkers')
def walkers():
    all_walkers = DogWalker.query.all()
    flash("No walkers found yet. 🐾", "info")
    return render_template('walkers.html', walkers=all_walkers)

# Remove walker
@app.route('/remove_walker/<int:id>', methods=['POST'])
def remove_walker_by_id(id):
    if not session.get('admin'):
        return redirect(url_for('login'))

    walker = DogWalker.query.get(id)
    if walker:
        db.session.delete(walker)
        db.session.commit()
    
    flash('Walker removed successfully!')
    return redirect(url_for('walkers'))

#Book a walker 
@app.route('/book/<int:id>', methods=['GET', 'POST'])
def book_walker(id):
    walker = DogWalker.query.get_or_404(id)

    prices = {
        "Morning": walker.price_morning,
        "Afternoon": walker.price_afternoon,
        "Evening": walker.price_evening
    }

    if request.method == 'POST':
        date = request.form['date']
        time_of_day = request.form['time_of_day']
        message = request.form.get('message')
        owner_email = request.form['owner_email']
        owner_phone = request.form['owner_phone']

        # 💾 Save the booking to the database
        new_booking = Booking(
            walker_id=walker.id,
            date=date,
            time_of_day=time_of_day,
            message=message,
            owner_email=owner_email,
            owner_phone=owner_phone,
            status='Pending'
        )

        db.session.add(new_booking)
        db.session.commit()

        # 📧 Send email to the walker
        email_body = f"""
        Hello {walker.name},

        Someone has booked a dog walk with you! 🐾

        📅 Date: {date}
        🕒 Time: {time_of_day}
        ✉️ Message: {message or 'No message provided'}

        Please log in to confirm the booking.

        — Team Woff
        """

        try:
            msg = Message("📅 New Dog Walk Booking!", recipients=[walker.email])
            msg.body = email_body
            mail.send(msg)
            flash("Booking submitted and confirmation email sent!", "success")
        except Exception as e:
            flash(f"Booking submitted but email failed: {e}", "error")

        return redirect(url_for('walkers'))

    # GET request
    return render_template('book_walker.html', walker=walker, prices=prices)

# Booking Response
@app.route('/respond_booking/<int:booking_id>', methods=['POST'])
def respond_booking(booking_id):
    if 'walker_id' not in session:
        return redirect(url_for('walker_login'))

    booking = Booking.query.get_or_404(booking_id)
    action = request.form['action']

    if action == 'confirm':
        booking.status = 'Confirmed'
        message = "🎉 Your booking has been confirmed!"
    else:
        booking.status = 'Rejected'
        message = "😢 Your booking was rejected. Feel free to try another walker!"

    db.session.commit()

    # Send email to owner
    try:
        msg = Message("🐾 Booking Update from Team Woff", recipients=[booking.owner_email])
        msg.body = f"""
Hello from Team Woff!

Status update on your booking request:
📅 Date: {booking.date}
🕒 Time: {booking.time_of_day}

{message}

Thanks for using Team Woff!
        """
        mail.send(msg)
        flash("Response sent and email delivered!", "success")
    except Exception as e:
        flash(f"Response saved, but email failed: {e}", "error")

    return redirect(url_for('walker_dashboard'))

# walker login
@app.route('/walker_login', methods=['GET', 'POST'])
def walker_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        walker = DogWalker.query.filter_by(email=email).first()

        if walker and walker.password_hash and check_password_hash(walker.password_hash, password):
            session['walker_id'] = walker.id
            flash("Login successful! 🐶", "success")
            return redirect(url_for('walker_dashboard'))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for('walker_login'))

    # Only hit this part on GET
    return render_template('walker_login.html')

# Walkers dashboard login
@app.route('/walker_dashboard')
def walker_dashboard():
    if 'walker_id' not in session:
        return redirect(url_for('walker_login'))

    walker = DogWalker.query.get(session['walker_id'])
    bookings = Booking.query.filter_by(walker_id=walker.id).all()
    return render_template('walker_dashboard.html', walker=walker, bookings=bookings)
# Walkers update
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'walker_id' not in session:
        return redirect(url_for('walker_login'))

    walker = DogWalker.query.get(session['walker_id'])

    if request.method == 'POST':
        walker.name = request.form['name']
        walker.city = request.form['city']
        walker.experience = request.form['experience']
        walker.availability = ', '.join(request.form.getlist('availability'))
        walker.dog_size = request.form['dog_size']
        walker.about_me = request.form['about_me']
        walker.phone = request.form['phone']
        walker.price_morning = request.form.get('price_morning')
        walker.price_afternoon = request.form.get('price_afternoon')
        walker.price_evening = request.form.get('price_evening')

        db.session.commit()
        flash("Your profile has been updated!", "success")
        return redirect(url_for('walker_dashboard'))

    return render_template('edit_profile.html', walker=walker)


# Admin Login Route
# ----------------------------
@app.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form['password']

        # TEMPORARY: skip password check
        if password == 'letmein':
            session['admin'] = True
            return redirect(url_for('walkers'))

        # Real check (leave this here)
        if check_password_hash(hashed_password, password):
            session['admin'] = True
            return redirect(url_for('walkers'))
        else:
            return render_template('login.html', error='Incorrect password')

    return render_template('login.html')

# ----------------------------
# Walker Logout
@app.route('/walker_logout', methods=['POST'])
def walker_logout():
    if 'walker_id' in session:
        session.pop('walker_id')
        flash("Walker logged out.", "success")
    return redirect(url_for('home'))

# Admin Logout
@app.route('/admin_logout', methods=['POST'])
def admin_logout():
    if 'admin' in session:
        session.pop('admin')
        flash("Admin logged out.", "success")
    return redirect(url_for('home'))



# About us
@app.route('/about')
def about():
    return render_template('about.html')
# Meet our CEO 
@app.route('/ceo')
def ceo():
    return render_template('ceo.html')
# ----------------------------
# Run App
# ----------------------------
if __name__ == '__main__':
    app.run(debug=True)


