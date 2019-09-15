from flask import Flask, render_template, request
from flask_cors import CORS
from forms import GroupForm
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import pyrebase 

import json

# Use the application default credentials
cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
  'projectId': u"td-groups",
})

db = firestore.client()

config = {
  "apiKey": "AIzaSyBST-3U14ztUoOfIADZ00hfl3vFlW-TN8Q",
  "authDomain": "td-groups.firebaseapp.com",
  "databaseURL": "https://td-groups.firebaseio.com/",
  "storageBucket": "td-groups.appspot.com"
}

firebase = pyrebase.initialize_app(config)
app = Flask(__name__)
# app.config['SECRET_KEY'] = '3a4j3ii6u5h4nn59'
CORS(app)


@app.route('/')
def index():
  return 'Hello world'

@app.route('/home')
def home():

  return render_template("home.html")

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
  # Call the firebase database and get all the user info

  user = "test-user"

  users_ref = db.collection(u'users')
  docs = users_ref.stream()

  for doc in docs:
    print(u'{} => {}'.format(doc.id, doc.to_dict()))

  return render_template("dashboard.html", user=user)

# For registering a user
@app.route('/user', methods=['POST'])
def create_user():
  print(request.get_json())
  return "got user"

# Assigning a user to a new group
@app.route('/user/group', methods=['POST'])
def assign_user_to_group():
  print(request.get_json())
  return "Assigning user to group"

# Registering a new group
@app.route('/group', methods=['POST'])
def create_group():
  print(request.get_json())
  return "Creating group"

# Creating group categories
@app.route('/group/category', methods=['POST'])
def group_category():
  pass


if __name__ == '__main__':
  app.run(debug=True)
