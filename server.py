#!/usr/bin/env python2.7

"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver

To run locally:

    python server.py

Go to http://localhost:8111 in your browser.

A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
import time
import datetime
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, redirect, escape, flash, url_for

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@104.196.135.151/proj1part2
#
# For example, if you had username gravano and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://gravano:foobar@104.196.135.151/proj1part2"
#
DATABASEURI = "postgresql://gc2676:2317@104.196.135.151/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
# engine.execute("""CREATE TABLE IF NOT EXISTS test (
#   id serial,
#   name text
# );""")
# engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")

app.secret_key = 'boba'


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/', methods=['GET', 'POST'])
def index():
  cursor = g.conn.execute("SELECT C.name FROM cafe C")

  data = []
  for result in cursor:
    entry_dict = {"name": result[0]}
    data.append(entry_dict)
  cursor.close()

  username = None
  if session['logged_in']:
    username = session['username']

  context = dict(data = data)

  return render_template("index.html", **context)

@app.route('/profile')
def view_profile():
  if not session['logged_in']:
    return redirect('/login')

  cursor_user = g.conn.execute('SELECT U.first_name, U.last_name, U.username, U.status, U.uid FROM Users U WHERE U.username = (%s)', session['username'])
  user_data = {}
  for result in cursor_user:
    user_data = {"first_name" : result[0], "last_name" : result[1], "username" : result[2], "status" : result[3], "uid" : result[4]}
  cursor_user.close()

  cafes = []
  cursor_cafe = g.conn.execute('SELECT DISTINCT C.name FROM Checked_In Ci, Users U, Cafe C WHERE Ci.uid = (%s) AND Ci.cid = C.cid', user_data['uid'])
  for result in cursor_cafe:
    cafes.append(result[0])
  cursor_cafe.close()

  context = dict(user_data = user_data, cafes = cafes)

  return render_template("profile.html", **context)


"""
@app.route('/nearby')
def view_nearby():
    return render_template('nearby.html')


@app.route('/uptown')
def view_uptown():
  if not session['logged_in']:
    return redirect('/login')

  cafes = []
  cafes = g.conn.execute('SELECT DISTINCT C.name FROM Cafe C WHERE C.neighborhood = 'Morningside Heights'')

  context = dict(user_data = user_data, cafes = cafes)
  return render_template("uptown.html", **context)
"""



@app.route('/search', methods=['POST'])
def search():
  category = ""
  name = ""
  if request.method == 'POST':
    query = request.form['search_query']
    category = request.form['category']

  cafes = []
  if category == 'cafe':
    cursor = g.conn.execute('SELECT C.name FROM Cafe C WHERE C.name = (%s)', query)
    for result in cursor:
      entry_dict = {"cname" : result[0]}
      cafes.append(entry_dict)
    cursor.close()
  elif category == 'neighborhood':
    cursor = g.conn.execute('SELECT C.name FROM Cafe C, Located_At La, Location L WHERE C.cid = La.cid AND La.cid = L.lid AND L.neighborhood = (%s)', query)
    for result in cursor:
      entry_dict = {"cname" : result[0]}
      cafes.append(entry_dict)
    cursor.close()
  elif category == 'time':
    cursor = g.conn.execute('SELECT C.name, C.hours FROM Cafe C')
    for result in cursor:
      closing_time = datetime.datetime.strptime(result[1].split("-")[1].strip(), '%I:%M%p')
      current_time = datetime.datetime.strptime(datetime.datetime.strftime(datetime.datetime.now(), '%I:%M%p'), '%I:%M%p')
      time_diff = closing_time - current_time
      if time_diff.total_seconds() / 60.0 > int(query):
        entry_dict = {"cname" : result[0]}
        cafes.append(entry_dict)
    cursor.close()
  context = dict(cafes = cafes)

  return render_template("search.html", search_query = name, **context)

@app.route('/details', methods=['GET', 'POST'])
def details():
  name = request.args.get('cname')

  search_entry_dict = {}
  cursor_name = g.conn.execute('SELECT C.cid, C.name, C.price_range, C.phone_number, C.payment_option, C.hours, C.best_seller FROM Cafe C WHERE C.name  = (%s)', name)
 
  for result in cursor_name:
    cid = result[0]
    locs = []
    cursor_loc = g.conn.execute("SELECT L.building_number, L.street, L.neighborhood FROM located_at La, location L WHERE La.cid = (%s) AND L.lid = La.lid", cid)
    for loc in cursor_loc:
      locs.append((loc[0], loc[1], loc[2]))

    ratings = []
    cursor_rating = g.conn.execute("SELECT R.category, R.stars, U.username, R.date FROM rating_given R, users U WHERE R.cid = (%s) AND R.uid = U.uid", cid)
    for rating in cursor_rating:
      ratings.append((rating[0], rating[1], rating[2], rating[3]))

    reviews = []
    cursor_review = g.conn.execute("SELECT R.description, U.username, R.date FROM review_written R, users U WHERE R.cid = (%s) AND R.uid = U.uid", cid)
    for review in cursor_review:
      reviews.append((review[0], review[1], review[2]))

    checked_in = False

    if session['logged_in']:
      cursor_uid = g.conn.execute('SELECT U.uid FROM users U WHERE U.username = (%s)', session['username'])
      uid = -1
      for uid_result in cursor_uid:
        uid = uid_result[0]
      cursor_uid.close()

      cursor_ci = g.conn.execute('SELECT C.cid FROM users U, cafe C, checked_in CI WHERE CI.cid = (%s) AND CI.uid = (%s)', cid, uid)
      ci_list = []
      for ci_result in cursor_ci:
        ci_list.append(ci_result[0])

      if len(ci_list) > 0:
        checked_in = True

    search_entry_dict = {"name": name, "price" : result[2], "phone" : result[3], "payment" : result[4], "hours" : result[5], "best_seller" : result[6], "location": locs, "rating": ratings, "review": reviews, "checked_in" : checked_in}

  cursor_name.close()

  return render_template("details.html", cafe = search_entry_dict)

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
  first_name = ""
  last_name = ""
  username = ""
  password = ""
  error = None
  if request.method == 'POST':
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    username = request.form['username']
    password = request.form['password']

    valid_account = True
    cursor_username = g.conn.execute('SELECT COUNT(U.username) FROM users U WHERE U.username = (%s)', username)
    for result in cursor_username:
      if result[0] > 0:
        valid_account = False

    if valid_account:
      cursor_id = g.conn.execute('SELECT MAX(U.uid) FROM users U')
      default_status = 'Novice'
      max_id = -1
      for result in cursor_id:
        max_id = int(result[0])
      max_id = max_id + 1
      g.conn.execute('INSERT INTO users(uid, status, first_name, last_name, username, password) VALUES ((%s), (%s), (%s), (%s), (%s), (%s))', max_id, default_status, first_name, last_name, username, password)
      flash("Your account was created!")
      return redirect('/')
    else:
      error = "Invalid username, please pick a different username"
  return render_template('create_account.html', error=error)

@app.route('/write_review', methods=['GET', 'POST'])
def write_review():
  cname = request.args.get('cname')
  review = request.form['review']

  cursor_cid = g.conn.execute('SELECT C.cid FROM cafe C WHERE C.name = (%s)', cname)
  cid = -1
  for result in cursor_cid:
    cid = result[0]
  cursor_cid.close()

  cursor_uid = g.conn.execute('SELECT U.uid FROM users U WHERE U.username = (%s)', session['username'])
  uid = -1
  for result in cursor_uid:
    uid = result[0]
  cursor_uid.close()

  cursor_revid = g.conn.execute('SELECT MAX(R.revid) FROM review_written R')
  max_id = -1
  for result in cursor_revid:
    max_id = int(result[0])
  max_id = max_id + 1
  cursor_revid.close()

  ts = time.time()
  time_stamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

  g.conn.execute('INSERT INTO review_written(revid, description, cid, uid, date) VALUES ((%s), (%s), (%s), (%s), (%s))', max_id, review, cid, uid, time_stamp)
  return redirect(url_for('details', cname = cname))

@app.route('/give_rating', methods=['GET', 'POST'])
def give_rating():
  cname = request.args.get('cname')
  rating_category = request.form['rating_category']
  rating_stars = request.form['stars']

  cursor_cid = g.conn.execute('SELECT C.cid FROM cafe C WHERE C.name = (%s)', cname)
  cid = -1
  for result in cursor_cid:
    cid = result[0]
  cursor_cid.close()

  cursor_uid = g.conn.execute('SELECT U.uid FROM users U WHERE U.username = (%s)', session['username'])
  uid = -1
  for result in cursor_uid:
    uid = result[0]
  cursor_uid.close()

  cursor_ratid = g.conn.execute('SELECT MAX(R.ratid) FROM rating_given R')
  max_id = -1
  for result in cursor_ratid:
    max_id = int(result[0])
  max_id = max_id + 1
  cursor_ratid.close()

  ts = time.time()
  time_stamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

  g.conn.execute('INSERT INTO rating_given(ratid, stars, category, cid, uid, date) VALUES ((%s), (%s), (%s), (%s), (%s), (%s))', max_id, rating_stars, rating_category, cid, uid, time_stamp)

  return redirect(url_for('details', cname = cname))

@app.route('/add_cafe', methods=['GET', 'POST'])
def add():
  cafe_name = ""
  price_range = ""
  phone_number = ""
  payment_option = ""
  hours = ""
  best_seller = ""
  building_number = ""
  street_name = ""
  neighborhood = ""
  error = None
  if request.method == 'POST':
    cafe_name = request.form['cafe_name']
    price_range = request.form['price_range']
    phone_number = request.form['phone_number']
    payment_option = request.form['payment_option']
    hours = request.form['hours']
    best_seller = request.form['best_seller']
    building_number = request.form['building_number']
    street_name = request.form['street_name']
    neighborhood = request.form['neighborhood']

    valid_cafe = True
    cursor_cname = g.conn.execute('SELECT COUNT(C.name) FROM cafe C WHERE C.name = (%s)', cafe_name)
    for result in cursor_cname:
      if result[0] > 0:
        valid_cafe = False

    if valid_cafe:
      cursor_cid = g.conn.execute('SELECT MAX(C.cid) FROM cafe C')
      max_cid = -1
      for result in cursor_cid:
        max_cid = int(result[0])
      max_cid = max_cid + 1

      cursor_lid = g.conn.execute('SELECT MAX(L.lid) FROM location L')
      max_lid = -1
      for result in cursor_lid:
        max_lid = int(result[0])
      max_lid = max_lid + 1
      g.conn.execute('INSERT INTO cafe(cid, name, price_range, phone_number, payment_option, hours, best_seller) VALUES ((%s), (%s), (%s), (%s), (%s), (%s), (%s))', max_cid, cafe_name, price_range, phone_number, payment_option, hours, best_seller)
      g.conn.execute('INSERT INTO location(lid, street, building_number, neighborhood) VALUES((%s), (%s), (%s), (%s))', max_lid, street_name, building_number, neighborhood)
      g.conn.execute('INSERT INTO located_at(cid, lid) VALUES((%s), (%s))', max_cid, max_lid)
      return redirect('/')
    else:
      error = "You have alrady registered this cafe!"
  return render_template('add_cafe.html', error=error)

@app.route('/check_in', methods=['GET', 'POST'])
def check_in():
  cname = request.args.get('cname')
  cursor_cid = g.conn.execute('SELECT C.cid FROM cafe C WHERE C.name = (%s)', cname)
  cid = -1
  for result in cursor_cid:
    cid = result[0]
  cursor_cid.close()

  cursor_uid = g.conn.execute('SELECT U.uid FROM users U WHERE U.username = (%s)', session['username'])
  uid = -1
  for result in cursor_uid:
    uid = result[0]
  cursor_uid.close()

  try:
    g.conn.execute('INSERT INTO checked_in(uid, cid) VALUES ((%s), (%s))', uid, cid)
  except:
    print("You've already checked in!")
  return redirect(url_for('details', cname = cname))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        session['username'] = request.form['username']
        cursor_password = g.conn.execute("SELECT U.password FROM users U WHERE U.username = (%s)", session['username'])
        password = []
        # there really should only be one password
        for result in cursor_password:
          password.append(result[0])

        if len(password) > 0 and request.form['password'] != password[0]:
            error = 'Invalid password'
        else:
            session['password'] = request.form['password']
            session['logged_in'] = True
            flash('You were logged in')
            return redirect('/')
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    session.pop('password', None)
    session['logged_in'] = False
    return redirect('/')

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
