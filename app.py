from flask import Flask, render_template, url_for, session, redirect, jsonify, request, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, DateField, BooleanField, TextAreaField, FileField, RadioField
from wtforms.fields.html5 import DateField
from wtforms.validators import InputRequired, Email, length
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

from werkzeug.utils import secure_filename
app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)


# database models


class users(db.Model):
    id = db.Column(db.Integer, nullable=False,
                   primary_key=True, autoincrement=True)
    username = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(20), nullable=False, unique=True)
    clearance = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    bookings = db.relationship('bookings', backref='users',
                               lazy=True, primaryjoin="users.id == bookings.user_id")
    profiles = db.relationship(
        'profiles', backref='users', lazy=True, primaryjoin="users.id == profiles.user")
    contacts = db.relationship(
        'contacts', backref='users', lazy=True, primaryjoin="users.id == contacts.user")
    rentals = db.relationship('rentalowner', backref='users',
                              lazy=True, primaryjoin="users.id == rentalowner.rental_id")


class bookings(db.Model):
    id = db.Column(db.Integer, nullable=False,
                   primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rental_id = db.Column(db.Integer, db.ForeignKey(
        'rentals.id'), nullable=False)


class rentals(db.Model):
    id = db.Column(db.Integer, nullable=False,
                   primary_key=True, autoincrement=True)
    location = db.Column(db.String(100), nullable=False)
    features = db.Column(db.String(300), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    bookings = db.relationship('bookings', backref='rentals',
                               lazy=True, primaryjoin="rentals.id == bookings.rental_id")
    rentals = db.relationship('rentalowner', backref='rentals',
                              lazy=True, primaryjoin="rentals.id == rentalowner.rental_id")
    images = db.relationship('images', backref='rentals',
                             lazy=True, primaryjoin='rentals.id == images.rental')


class rentalowner (db.Model):
    id = db.Column(db.Integer, nullable=False,
                   autoincrement=True, primary_key=True)
    owner = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rental = db.Column(db.Integer, db.ForeignKey('rentals.id'), nullable=False)


class images(db.Model):
    id = db.Column(db.Integer, nullable=False,
                   primary_key=True, autoincrement=True)
    rental = db.Column(db.Integer, db.ForeignKey(
        'rentals.id'), nullable=False)
    image_url = db.Column(db.LargeBinary)


class profiles(db.Model):
    id = db.Column(db.Integer, nullable=False,
                   primary_key=True, autoincrement=True)
    user = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    profile = db.Column(db.LargeBinary)


class contacts(db.Model):
    id = db.Column(db.Integer, nullable=False,
                   autoincrement=True, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    phone = db.Column(db.Integer, nullable=False)
    pAdress = db.Column(db.Integer)

# form models


class reg(FlaskForm):
    username = StringField('username', validators=[
        InputRequired(), length(min=6, max=20)])
    email = StringField('email', validators=[
                        InputRequired(), length(min=10, max=20)])
    password = PasswordField('password', validators=[
                             InputRequired(), length(min=8, max=80)])
    password2 = PasswordField('password2', validators=[
        InputRequired(), length(min=8, max=80)])


class Login(FlaskForm):
    email = StringField('email', validators=[
        InputRequired(), length(min=10, max=20)])
    password = PasswordField('password', validators=[
                             InputRequired(), length(min=8, max=80)])


class reservehouse(FlaskForm):
    name = StringField('name', validators=[
                       InputRequired(), length(min=6, max=30)])
    occupants = IntegerField('occupants')
    phone = IntegerField('phone', validators=[
        InputRequired(), length(min=10, max=20)])
    email = StringField('email')
    passport = IntegerField('passport')
    date = DateField('date')


class spaceupload(FlaskForm):
    location = StringField('location', validators=[InputRequired()])
    price = IntegerField('price', validators=[InputRequired()])
    description = TextAreaField('description', validators=[
        InputRequired(), length(min=200, max=2000)])
    type = RadioField('housetype', choices=[(
        '1', 'bungallow'), ('2', 'mansionete'), ('3', 'appartment')])
    bedrooms = IntegerField('bedrooms')
    bathrooms = IntegerField('bathrooms')
    squarefeet = IntegerField('squarefeet')
    images = FileField('images')
# image checker


def allowed_image(filename):
    if not '.' in filename:
        return False
    ext = filename.rsplit('.', 1)[1]
    if ext.upper() in app.config['ALLOWED_IMAGE_EXTENSIONS']:
        return True
    else:
        return False

 # start page loader


@app.route('/')
def main():
    return render_template('dash.html')

# house ownner page loader
@app.route('/admin', methods=['POST', 'GET'])
def admin():
    if "user" in session:
        myform = spaceupload()
        return render_template('landlord.html', form=myform)
    else:
        return render_template('index.html')

# property page expounder route. pulls property from database and displays
@app.route('/property', methods=['GET', 'POST'])
def property():
    if "user" in session:
        return render_template('property.html')
    else:
        return render_template('index.html')

# landlord views status of their available rentals
@app.route('/rentalstatus', methods=['GET', 'POST'])
def rentalstatus():
    if "user" in session:
        return render_template('rentalstatus.html')
    else:
        return render_template('index.html')

# customer booking page is displayed
@app.route('/bookspace', methods=['GET', 'POST'])
def book():
    if "user" in session:
        form = reservehouse()
        user = session['user']
        return render_template('book.html', user=user, form=form)
    else:
        return render_template('index.html')

# booking by customer is processed and either approved or denied
@app.route('/reserve', methods=['POST', 'GET'])
def reserve():
    if "user" in session:
        form = book()
        userID = session['id']
        rentalID = session['rentalID']
        booking = booking(user_id=userID, rental_id=rentalID)
        db.session.add(booking)
        db.session.commit()
        return render_template('checkout.html')
    else:
        return render_template('index.html')


# log in page is initiated here
@app.route('/start', methods=['GET', 'POST'])
def start():
    form = Login()
    return render_template('index.html', form=form)

#login is processed
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = Login()
    account = users.query.filter_by(email=form.email.data).first()
    if account:
        checkpass = check_password_hash(account.password, form.password.data)
        if checkpass:
            clearance = account.clearance
            session['user'] = account.username
            session['id'] = account.id
            name = session['user']
            if clearance == "admin":
                return render_template(url_for('admin'))
            elif clearance == 'user':
                return redirect(url_for('homepage'))

            return redirect(url_for('systemadmin'))
        else:
            return '<h1>Invalid user or password</h1>'
    else:
        return render_template('index.html', form=form)

    return redirect(url_for('login'))

# register new user page is initiated
@app.route('/registration', methods=['POST', 'GET'])
def registration():
    form = reg()
    return render_template('register.html', form=form)

# register new user is processed
@app.route('/register', methods=['POST', 'GET'])
def register():
    form = reg()
    if form.password.data == form.password2.data:
        hashed_password = generate_password_hash(
            form.password.data, method='sha256')
        new_user = users(username=form.username.data,
                         email=form.email.data, clearance="user", password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return render_template('index.html', form=form)
    else:
        return render_template('register.html', errors='passwords dont match', form=form)

    return redirect('/registration')


# landlord upload page is loaded here
@app.route('/newrental', methods=['POST', 'GET'])
def newrental():
    if "user" in session:
        form = spaceupload()
        return render_template('uploadspace.html', form=form)
    else:
        return render_template('index.html')


# landlord upload new rental is processed here
@app.route('/upload', methods=['POST', 'GET'])
def upload():
    form = spaceupload()
    if "user" in session:
        if request.method == 'POST':
            if form.images:
                image = request.files['images']
                if allowed_image(image.filename):
                    filename = secure_filename(image.filename)
                    new_image = images(
                        rental=form.email.data, image_url=filename)
                    db.session.add(new_image)
                    db.session.commit()
                    image.save(os.path.join(
                        app.config['UPLOAD_IMAGE'], filename))
                    new_rental = rentals(
                        rental=form.email.data, image_url=filename)
                    db.session.add(new_rental)
                    db.session.commit()
                    return redirect(url_for('admin'))
                else:
                    print('Image isnt really apealing')
                    return redirect(request.url)
        else:
            error = "The details were not correct.Please try again"
            return render_template('uploadspace.html', errormessage=error, form=spaceupload())
    else:
        return render_template('index.html')


# debug mode
if __name__ == "__main__":
    app.run()
