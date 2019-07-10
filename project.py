#!/usr/bin/env python3
from flask import Flask, render_template, request
from flask import redirect, url_for, jsonify, flash

from sqlalchemy import create_engine, asc, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from database_setup import Base, AnimalClasses, ClassFamilies, User
from flask import session as login_session
import random
import string
from apiclient import discovery
from oauth2client import client
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import os


app = Flask(__name__)

# CLIENT_ID = json.loads(
#     open('client_Secrets.json', 'r').read())['web']['client_id']
# APPLICATION_NAME = "udacity-animal-catalog"
PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(PROJECT_ROOT, 'client_secrets.json')
CLIENT_ID = json.load(open(json_url))['web']['client_id']


# Establish connection to database and create a session
engine = create_engine('sqlite:///animalcatalog.db',
                       connect_args={'check_same_thread': False},
                       poolclass=StaticPool, echo=True)
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create a random anti forgery state token and login user
@app.route('/login/')
def loginPage():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, CLIENT_ID=CLIENT_ID)


# Authenticate user with Googles OAUTH2 API
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('User is already connected'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    print("LOGIN SESSION %s" % login_session['username'])

    # Check if user exists
    user_id = getUserID(login_session['email'])
    print("User id is %s" % user_id)
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    print("User id from login_session is %s" % login_session['user_id'])

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += """ ' " style = "width: 300px; height: 300px;
                border-radius: 150px;-webkit-border-radius: 150px;
                -moz-border-radius: 150px;"> ' """
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output


# User Management Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()

    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one_or_none()

    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except BaseException:
        print("User ID not found")
        return None


# Reset login_session after logging out
@app.route('/logout/')
def logoutPage():
    gdisconnect()
    del login_session['access_token']
    del login_session['gplus_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    flash('Successfully logged out')
    return redirect(url_for('showAnimalClasses'))


# For Google OAUTH users reset token and login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Check for current connection
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/classes/<int:animal_class_id>/family/JSON')
def classFamilyJSON(animal_class_id):
    animal_class = (session.query(AnimalClasses).
                    filter_by(id=animal_class_id).one())
    class_family = (session.query(ClassFamilies).
                    filter_by(animal_class_id=animal_class_id).all())
    return jsonify(ClassFamilies=[i.serialize for i in class_family])


@app.route('/classes/JSON')
def animalClassJSON():
    animal_class = (session.query(AnimalClasses).all())
    return jsonify(AnimalClasses=[i.serialize for i in animal_class])


@app.route('/classes/<int:animal_class_id>/family/<int:animal_family_id>/JSON')
def singleAnimalFamilyJSON(animal_class_id, animal_family_id):
    class_family = (session.query(ClassFamilies).
                    filter_by(animal_class_id=animal_class_id).
                    filter_by(id=animal_family_id).
                    all())
    return jsonify(AnimalClasses=[i.serialize for i in class_family])

# Summary of all animal classes added to the DB


@app.route('/')
@app.route('/classes/')
def showAnimalClasses():
    """Load main page which has an overview of all animal classes"""
    animal_classes = session.query(AnimalClasses)
    animal_families = session.query(ClassFamilies).join(AnimalClasses).all()
    try:
        return (render_template('animalClasses.html',
                animal_classes=animal_classes,
                user_name=login_session['username'],
                user_id=login_session['user_id'],
                animal_families=animal_families))
    except KeyError:
        return (render_template('animalClasses.html',
                animal_classes=animal_classes,
                animal_families=animal_families))


# Create a new animal class
@app.route('/classes/new/', methods=['GET', 'POST'])
def newAnimalClass():
    """Create a new class"""
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == "POST":
        newClass = (AnimalClasses(name=request.form['name'],
                                  link=request.form['link'],
                                  user_id=login_session['user_id'],
                                  ))
        session.add(newClass)
        flash('Class %s successfully added to the Ark' % newClass.name)
        session.commit()
        return redirect(url_for('showAnimalClasses'))
    else:
        return render_template('newAnimalClass.html',
                               user_name=login_session['username'])


# Edit an existing animal class
@app.route('/classes/<int:animal_class_id>/edit/', methods=['GET', 'POST'])
def editAnimalClass(animal_class_id):
    if 'username' not in login_session:
        return redirect('/login')
    animalClassToEdit = (session.query(AnimalClasses).
                         filter_by(id=animal_class_id).one())
    creator = getUserInfo(animalClassToEdit.user_id)
    if creator.id != login_session['user_id']:
        flash('You did not create this class and thus cannot edit it')
        return redirect(url_for('showAnimalClasses'))
    else:
        if request.method == "POST":
            if request.form['name']:
                animalClassToEdit.name = request.form['name']
            if request.form['link']:
                animalClassToEdit.link = request.form['link']
            session.add(animalClassToEdit)
            flash('Class %s successfully edited' % animalClassToEdit.name)
            session.commit()
            return redirect(url_for('showAnimalClasses'))
        else:
            try:
                return (render_template('editAnimalClass.html',
                                        animal_class=animalClassToEdit,
                                        animal_class_id=animal_class_id,
                                        user_name=login_session['username']))
            except KeyError:
                return (render_template('editAnimalClass.html',
                                        animal_class=animalClassToEdit,
                                        animal_class_id=animal_class_id))


# Delete an existing animal class
@app.route('/classes/<int:animal_class_id>/delete/', methods=['GET', 'POST'])
def deleteAnimalClass(animal_class_id):
    if 'username' not in login_session:
        return redirect('/login')
    animalClassToDelete = (session.query(AnimalClasses).
                           filter_by(id=animal_class_id).one())
    creator = getUserInfo(animalClassToDelete.user_id)
    if creator.id != login_session['user_id']:
        flash('You did not create this class and thus cannot delete it')
        return redirect(url_for('showAnimalClasses'))
    else:
        if request.method == "POST":
            session.delete(animalClassToDelete)
            flash('Class %s successfully deleted' % animalClassToDelete.name)
            session.commit()
            return redirect(url_for('showAnimalClasses'))
        else:
            return (render_template('deleteAnimalClass.html',
                    animal_class=animalClassToDelete,
                    animal_class_id=animal_class_id,
                    user_name=login_session['username']))


@app.route('/classes/<int:animal_class_id>/')
@app.route('/classes/<int:animal_class_id>/family/')
def showClassFamilies(animal_class_id):
    animal_classes = session.query(AnimalClasses)
    animal_class = (session.query(AnimalClasses).
                    filter_by(id=animal_class_id).one())
    class_family = (session.query(ClassFamilies).
                    filter_by(animal_class_id=animal_class_id).all())
    creator = getUserInfo(animal_class.user_id)
    try:
        if ('username' not in login_session or
                creator.id != login_session['user_id']):
            return (render_template('animalFamilyPublic.html',
                                    animal_classes=animal_classes,
                                    animal_class_id=animal_class_id,
                                    class_family=class_family,
                                    animal_class=animal_class,
                                    creator=creator,
                                    user_id=login_session['user_id'],
                                    user_name=login_session['username']))
        else:
            return (render_template('animalFamily.html',
                                    animal_classes=animal_classes,
                                    animal_class_id=animal_class_id,
                                    class_family=class_family,
                                    animal_class=animal_class,
                                    creator=creator,
                                    user_name=login_session['username']))
    except KeyError:
            return (render_template('animalFamily.html',
                                    animal_classes=animal_classes,
                                    animal_class_id=animal_class_id,
                                    class_family=class_family,
                                    animal_class=animal_class,
                                    creator=creator))
    except AttributeError:
            return (render_template('animalFamily.html',
                                    animal_classes=animal_classes,
                                    animal_class_id=animal_class_id,
                                    class_family=class_family,
                                    animal_class=animal_class,
                                    creator=creator,
                                    user_name=login_session['username']))


@app.route('/classes/<int:animal_class_id>/family/new/',
           methods=['GET', 'POST'])
def newAnimalFamily(animal_class_id):
    if 'username' not in login_session:
        return redirect('/login')
    animal_class = (session.query(AnimalClasses).
                    filter_by(id=animal_class_id).one())
    creator = getUserInfo(animal_class.user_id)
    if creator.id != login_session['user_id']:
        flash('You did not create this class and cannot add a family to it')
        return redirect(url_for('showClassFamilies',
                                animal_class_id=animal_class_id))
    else:
        if request.method == "POST":
            newFamily = ClassFamilies(name=request.form['name'],
                                      description=request.form['description'],
                                      animal_class_id=animal_class_id,
                                      distinctive_feature=(request.form
                                                           ['distinctive_'
                                                            'feature']
                                                           ),
                                      quantity_on_board=(request.form
                                                         ['quantity_on'
                                                          '_board']),
                                      male_female=request.form['male_female'],
                                      user_id=login_session['user_id'])
            session.add(newFamily)
            flash('Animal family %s successfully added' % newFamily.name)
            session.commit()
            return (redirect(url_for('showClassFamilies',
                                     animal_class_id=animal_class_id)))
        else:
            return (render_template('newAnimalFamily.html',
                                    animal_class_id=animal_class_id,
                                    animal_class=animal_class))


@app.route('/classes/<int:animal_class_id>/family/'
           '<int:animal_family_id>/edit/',
           methods=['GET', 'POST'])
def editAnimalFamily(animal_class_id, animal_family_id):
    if 'username' not in login_session:
        return redirect('/login')
    animalFamilyToEdit = (session.query(ClassFamilies).
                          filter_by(id=animal_family_id).one())
    creator = getUserInfo(animalFamilyToEdit.user_id)
    if creator.id != login_session['user_id']:
        flash('You did not create this family and thus cannot edit it')
        return redirect(url_for('showClassFamilies',
                                animal_class_id=animal_class_id))
    else:
        if request.method == "POST":
            if request.form['name']:
                animalFamilyToEdit.name = request.form['name']
            if request.form['description']:
                animalFamilyToEdit.description = request.form['description']
            if request.form['quantity_on_board']:
                animalFamilyToEdit.quantity_on_board = (request.
                                                        form['quantity_on_'
                                                             'board'])
            if request.form['male_female']:
                animalFamilyToEdit.male_female = request.form['male_female']
            if request.form['distinctive_feature']:
                animalFamilyToEdit.distinctive_feature = (request.form
                                                          ['distinctive_'
                                                           'feature'])
            session.add(animalFamilyToEdit)
            flash('Animal family %s successfully edited'
                  % animalFamilyToEdit.name)
            session.commit()
            return (redirect(url_for('showClassFamilies',
                                     animal_class_id=animal_class_id)))
        else:
            return (render_template('editAnimalFamily.html',
                                    animal_family=animalFamilyToEdit,
                                    animal_class_id=animal_class_id,
                                    animal_family_id=animal_family_id))


@app.route('/classes/<int:animal_class_id>'
           '/family/<int:animal_family_id>/delete/',
           methods=['GET', 'POST'])
def deleteAnimalFamily(animal_class_id, animal_family_id):
    if 'username' not in login_session:
        return redirect('/login')
    animalFamilyToDelete = (session.query(ClassFamilies).
                            filter_by(id=animal_family_id).one())
    creator = getUserInfo(animalFamilyToDelete.user_id)
    if creator.id != login_session['user_id']:
        flash('You did not create this family and thus cannot delete it')
        return redirect(url_for('showAnimalFamilies',
                                animal_class_id=animal_class_id,
                                animal_family_id=animal_family_id))
    else:
        if request.method == "POST":
            session.delete(animalFamilyToDelete)
            flash('Family %s successfully deleted' % animalFamilyToDelete.name)
            session.commit()
            return (redirect(url_for('showClassFamilies',
                                     animal_class_id=animal_class_id)))
        else:
            return (render_template('deleteAnimalFamily.html',
                                    animal_family=animalFamilyToDelete,
                                    animal_class_id=animal_class_id,
                                    animal_family_id=animal_family_id))


@property
def serialize(self):
    return {'name': self.name, 'image URL': self.link, 'id': self.id}

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
