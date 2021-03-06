from flask import Flask, render_template, request, flash, redirect, url_for
from flask_jsglue import JSGlue
from flask_cors import CORS
from forms import GroupForm, TransForm
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import pyrebase
import requests
import ast

import json
from groups import *

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
jsglue = JSGlue(app)
app.config['SECRET_KEY'] = '23d6332424c296c2bb6d2f1c4454fae2'
CORS(app)


@app.route('/')
def index():
  return render_template("home.html")

@app.route('/home')
def home():

  return render_template("home.html")

@app.route('/dashboard/<string:uid>/', methods=['GET', 'POST'])
def dashboard(uid):
  # Call the firebase database and get all the user info
  user_doc = db.collection(u'users').document(uid).get().to_dict()
  url = "https://api.td-davinci.com/api/customers/" + user_doc["td-customer-id"] + "/transactions"
  headers = {"accept": 'application/json', "Authorization": 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJDQlAiLCJ0ZWFtX2lkIjoiM2IyZDVhMTYtYTMwMC0zY2U2LTgzZTYtOTE2OWU4OTEzYzQ1IiwiZXhwIjo5MjIzMzcyMDM2ODU0Nzc1LCJhcHBfaWQiOiI5MjVhZjU4Yi1kMmQzLTQ0MjctOGE2Zi1kM2Y1MGZjOGJlOTMifQ.RRdnWTXL8jMdlgKKQ_zAtazf78cF45FchafL4TlEA0g'}

  print(requests.get(url, headers=headers).json())

  transactions = (requests.get(url, headers=headers).json())["result"]
  groups = []

  for doc in db.collection("groups").get():

    if (doc.id in [x.strip() for x in user_doc["groups"]]):
      group_dict = doc.to_dict()
      group_dict["id"] = doc.id
      groups.append(group_dict)

  result = {"user": user_doc, "transactions": transactions[:10], "groups" : groups}


  form = GroupForm()
  if form.validate_on_submit():
    # form is an object with its fields
    flash("GOOD!")
    form = GroupForm()

    name = form.name.data
    members = form.members.data.split(',')
    desc = form.description.data

    data = {"name": name,
            "members": members,
            "desc": desc,
            }

    db.collection(u'groups').add(data)

    return redirect(url_for('dashboard', uid=uid))

  # print(result)
  # result = ""

  print(result["groups"])

  return render_template("dashboard.html", user=result, form=form)

@app.route('/group/<string:group_id>/transaction', methods=['POST'])
def make_transaction(group_id):
  transaction_json = request.get_json()
  data = parse_transaction(transaction_json)

  db.collection(u'groups').document(group_id).collection('transactions').add(data)
  return redirect(url_for('group', group_id=group_id))

# For registering a user
@app.route('/user', methods=['POST'])
def create_user():
  print(request.get_json())
  return "got user"

# Assigning a user to a new group
@app.route('/user/group', methods=['POST'])
def assign_user_to_group():
  print(request.get_json())

  user = request.get_json()
  userId = user["userId"]
  groupId = user["groupId"]
  assign_to_group(userId, groupId)
  return "Assigning user to group"

# Registering a new group
@app.route('/group', methods=['GET', 'POST'])
def create_group():
  form = TransForm()
  if form.validate_on_submit():
    return redirect(url_for('group', uid=uid))
  # print(request.get_json())
  # group_json = request.get_json()
  # group_name = group_json["groupName"]
  # group_members = group_json["groupMembers"]

  # data = create_new_group(group_name, group_members)
  # db.collection(u'groups').document(u'').set(data)
  return render_template("group.html", user='user', form=form)

# Creating group categories
@app.route('/group/category', methods=['POST'])
def group_category():
  category_json = request.get_json()
  group_name = category_json["groupName"]
  category_name = category_json["groupName"]

  create_category(group_name, category_name)
  return "Hey"


@app.route('/transaction')
def get_transactions():
  user_id = request.args.get('userId')
  get_all_user_transactions(user_id)

def group_transaction():
  groupId = request.args.get('name')
  docs = db.collection(u'groups').where(u'name', u'==', groupId).stream()

  transactions = []
  for doc in docs:
    transactions.append(doc.to_dict())

  return render_template("group.html", transactions=transactions)

@app.route('/group/<string:group_id>/calculate/')
def group_calculate(group_id):
  group = db.collection(u'groups').document(group_id).get().to_dict()
  name = group["name"]
  desc = group["desc"]
  groupMembers = group["members"]

  trans = db.collection(u'groups').document(group_id).collection(u'transactions').stream()

  transactions = []
  balance = {}
  for doc in trans:
    transaction = doc.to_dict()
    owner = transaction["owner"]
    for person in transaction["owings"]:
      try:
        balance[owner] += transaction["owings"][person]
      except KeyError:
        balance[owner] = transaction["owings"][person]
      try:
        balance[person] -= transaction["owings"][person]
      except KeyError:
        balance[person] = -transaction["owings"][person]
    transactions.append(transaction)

  form = TransForm()

  return balance

#flag
@app.route('/group/<string:group_id>', methods=['GET', 'POST'])
def group_route(group_id):
  group = db.collection(u'groups').document(group_id).get().to_dict()
  name = group["name"]
  desc = group["desc"]
  groupMembers = group["members"]
  form = TransForm()

  trans = db.collection(u'groups').document(group_id).collection(u'transactions').stream()

  transactions = []
  for doc in trans:
    transactions.append(doc.to_dict())

  for transaction in transactions:
    stri = ""
    for key in transaction['owings']:
      stri += "%s: $%s, " % (key, transaction['owings'][key])
    transaction['owings'] = stri

  if form.validate_on_submit():
    owner = form.owner.data
    cost = form.cost.data
    owings = ast.literal_eval(form.owings.data)
    desc = form.description.data

    data = {"cost": cost,
            "owner": owner,
            "owings": owings,
            "description": desc}

    db.collection(u'groups').document(group_id).collection('transactions').add(data)
     
    return redirect(url_for('group_route', group_id=group_id))

  return render_template("group.html", group_id = group_id, desc=desc, name=name, members=groupMembers, transactions=transactions, form=form)

# Creating category transactions
@app.route('/group/category/transaction', methods=['POST', 'GET'])
def create_transaction():
  if request.method == 'POST':
    print(request.get_json())
    transaction_json = request.get_json()
    group_name = transaction_json["groupName"]
    category_name = transaction_json["category_name"]
    create_category_transaction(group_name, category_name)

    return "Create transaction"
  elif request.method == 'GET':
    group_id = request.args.get('groupId')
    get_group_transactions(group_id)
    return "Return all transactions in a group category"
  else:
    return "err"

@app.route('/group/category/<string:category_id>/transaction/<string:transaction_id>')
def get_transaction(category_id, transaction_id):
  get_single_transaction(category_id, transaction_id)
  return "get specific transaction"


if __name__ == '__main__':
  app.run(debug=True)
