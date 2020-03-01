from flask import Flask,render_template,url_for,session,redirect
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,DateField,BooleanField
from wtforms.fields.html5 import DateField
from wtforms.validators import InputRequired, Email, length
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)


#database models
class users(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True,autoincrement=True)
    username = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(20), nullable=False, unique=True)
    clearance = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    bookings = db.relationship('bookings', backref='users',lazy = True,primaryjoin="users.id == bookings.user_id")
    rentals = db.relationship('rentals', backref='users',lazy = True,primaryjoin="users.id == rentals.owner_id")
    profiles = db.relationship('profiles', backref = 'users',lazy = True,primaryjoin="users.id == profiles.user")
    contacts = db.relationship('contacts', backref = 'users',lazy = True,primaryjoin="users.id == contacts.user")

class bookings(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True,autoincrement=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.id'),nullable=False)
    rental_id = db.Column(db.Integer, db.ForeignKey('rentals.id'), nullable=False)

class rentals(db.Model):
    id = db.Column(db.Integer, nullable=False, primary_key=True,autoincrement=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    features = db.Column(db.String(300), nullable=False)
    description = db.Column(db.String(1000),nullable = False)    
    bookings = db.relationship('bookings', backref = 'rentals', lazy = True,primaryjoin="rentals.id == bookings.rental_id")
    images = db.relationship('images',backref = 'rentals',lazy = True,primaryjoin="rentals.id == images.owner_id")

class images(db.Model):
    id = db.Column(db.Integer,nullable = False, primary_key = True, autoincrement = True)
    owner_id = db.Column(db.Integer,db.ForeignKey('rentals.id'),nullable = False)
    image = db.Column(db.LargeBinary)

class profiles(db.Model):
    id = db.Column(db.Integer,nullable = False,primary_key = True,autoincrement = True)
    user = db.Column(db.Integer, db.ForeignKey('users.id'),nullable = False)
    profile = db.Column(db.LargeBinary)

class contacts(db.Model):
    id = db.Column(db.Integer, nullable = False,autoincrement = True,primary_key= True)
    user = db.Column(db.Integer,db.ForeignKey('users.id'),nullable = False)
    phone = db.Column(db.Integer,nullable = False)
    pAdress = db.Column(db.Integer)

#form models
class reg(FlaskForm):
    username = StringField('username', validators=[
                       InputRequired(), length(min=6, max=20)])
    email = StringField('email', validators=[
                        InputRequired(), length(min=10, max=20)])
    password = PasswordField('password', validators=[
                             InputRequired(), length(min=8, max=80)])
    password2 = PasswordField('password2',validators=[
        InputRequired(),length(min=8,max=80)])

class Login(FlaskForm):

    email = StringField('email', validators=[
        InputRequired(), length(min=10, max=20)])
    password = PasswordField('password', validators=[
                             InputRequired(), length(min=8, max=80)])

@app.route('/',methods=['POST','GET'])
def main():
    form = Login()
    return render_template('dash.html')

@app.route('/admin',methods=['POST','GET'])
def admin():
    return render_template('landlord.html')

@app.route('/property',methods=['GET','POST'])
def property():
    user = session['user']
    return render_template('property.html',user=user)

@app.route('/bookspace',methods=['GET','POST'])
def book():
    user = session['user']
    return render_template('book.html',user = user)

@app.route('/homepage',methods=['POST','GET'])
def homepage():
    link = "static\img\myAvatar.png"
    user = session['user']
    return render_template('dash.html',image = link,user = user)

@app.route('/profiles',methods=['POST','GET'])
def profiles():
    user = session['user']    
    return render_template('profiles.html',user = user)

@app.route('/update',methods=['POST','GET'])
def update():
    return f"<h3>info update</h3>"

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
        return render_template('index.html',form =form)

    return redirect(url_for('login'))

@app.route('/registration' ,methods=['POST','GET'])
def registration():
    form = reg()
    return render_template('register.html', form=form)

@app.route('/register',methods=['POST','GET'])
def register():
    form = reg()  
    if form.password.data == form.password2.data:
        hashed_password = generate_password_hash(
        form.password.data, method='sha256')
        print(hashed_password)
        new_user = users(username=form.username.data,
                    email=form.email.data,clearance = "user", password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return render_template('index.html',form=form )
    else:
        return render_template('register.html',errors = 'passwords dont match',form = form)


    return redirect('/registration')


#debug mode
if __name__ == "__main__":
    app.run()
