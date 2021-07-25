# app.py
import pyrebase
from getpass import getpass
import os
import dotenv
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from firebase_admin import credentials, firestore, initialize_app

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, validators
# Initialize Flask App
app = Flask(__name__)
app.secret_key=os.environ.get('SECRET_KEY', 'my-secret-key')


dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

class LoginForm(FlaskForm):
    email = StringField('Email')
    password = PasswordField('Password')
    submit = SubmitField('Submit')

    def validate(self):
        initial_validation = super(LoginForm, self).validate()
        if not initial_validation:
            return False

        """querry firestore by email"""
        admins = db.collection(u'admins').get()
        """filter by email"""
        for admin in admins:
            if admin.to_dict()['email'] == self.email.data:
                return True
        
        return False



cred = credentials.Certificate({
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID", ""),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID", ""),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL", ""),
    "client_id": os.getenv("FIREBASE_CLIENT_ID", ""),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
})
default_app = initialize_app(cred)
firebaseConfig = {
    "apiKey": os.getenv("FIREBASE_API_KEY", ""),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""),
    "databaseURL": "",
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", ""),
}
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()


db = firestore.client()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)

    """implement firebase auth login"""
    if form.validate_on_submit():
        try:
            user = auth.sign_in_with_email_and_password(form.email.data, form.password.data)
            session['refreshToken'] = user['refreshToken']
            return redirect(url_for('dashboard'))
        except:
            flash('Invalid email or password')

    return render_template('login.html', form=form)



@app.route('/manage')
def dashboard():
    """list users in db with type equals to ong"""

    """check if user is logged"""
    user = None
    if 'refreshToken' in session:
        user = auth.refresh(session['refreshToken'])
    if user:
        users = db.collection(u'users').get()
        ong_users = []
        for user in users:
            if user.to_dict()['type'] == 'ong':
                user_dict = user.to_dict()
                """replace user data document reference by dict"""
                user_dict['data'] = user_dict['data'].get().to_dict()
                if user_dict['data']['isApproved'] == False:
                    ong_users.append(user_dict)

        print(ong_users)
        return render_template('manage.html', ong_users=ong_users)
    else:
        return redirect(url_for('login'))


@app.route('/approve')
def approve_user():
    """approve user"""

    user = auth.current_user
    if user:
        email = request.args.get('email')
        users = db.collection(u'users').get()

        """filter users by email"""
        for user in users:
            if user.to_dict()['email'] == email:
                """update data.isApproved value to true"""
                data = user.to_dict()['data'].get()
                data.reference.update({'isApproved': True})

        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))


def main():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()
