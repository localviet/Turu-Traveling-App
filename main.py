from flask import Flask, redirect, render_template, url_for, request, session, flash, jsonify
import requests
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, func, desc
import pytz

app = Flask(__name__)
app.secret_key = "khul"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
#app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.permanent_session_lifetime = timedelta(minutes=5)

db = SQLAlchemy(app)
cityFile = open('static/cities.txt', "r")
cities = eval(cityFile.read())

countryFile = open('static/countries.txt', "r")
countries = eval(countryFile.read())

class users(db.Model):
	_id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String(100))
	email = db.Column(db.String(100))
	password = db.Column(db.String(50))


	def __init__(self, name, email, password):
		self.name = name
		self.email = email
		self.password = password
class posts(db.Model):
	_id = db.Column(db.Integer, primary_key=True)
	easeOfTravel = db.Column(db.Integer)
	costOfLiving = db.Column(db.Integer)
	hospitality = db.Column(db.Integer)
	activities = db.Column(db.Integer)
	overall = db.Column(db.Integer)
	writtenReview = db.Column(db.String(350))
	user = db.Column(db.String(100))
	likes = db.Column(db.Integer)
	utc_now = datetime.utcnow()
	created_at = db.Column(db.DateTime, default = utc_now.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern')))
	country = db.Column(db.String(60))
	city = db.Column(db.String(60))
	inUS = db.Column(db.Boolean)

	def __init__(self, eot, col, h, ae, overall, user, writtenReview, cs, citi, ifUS):
		self.easeOfTravel = eot
		self.costOfLiving = col
		self.hospitality = h
		self.activities = ae
		self.overall = overall
		self.writtenReview = writtenReview
		self.user = user
		self.likes = 0
		self.country = cs
		self.city = citi
		self.inUS = ifUS
	

@app.route("/yomama")
@app.route("/", methods=["POST", "GET"])
def home():
	if request.method == "POST":
		session.permanent = True;
		user = request.form["nm"]
		userpw = request.form["pass"]
		foundUser = users.query.filter_by(name=user).first();
		if foundUser:
			if foundUser.password == userpw:
				session["user"] = user
				session["email"] = foundUser.email
				flash("Logged in!", "info")
				return redirect(url_for("user"))
			else:
				flash("Password doesn't match! / Name already taken", "info")
				return render_template('home.html')
		else:
			session["user"] = user
			session["email"] = "";
			newUser = users(user, session["email"], userpw)
			db.session.add(newUser)
			db.session.commit()
			flash("Account created!", "info")
			return redirect(url_for("user"))
	else:
		return render_template('home.html')

@app.route("/signup", methods=['GET', 'POST'])
def signup():
	if request.method == "POST":
		session.permanent = True;
		user = request.form['usrnm']
		email = request.form['email']
		pw = request.form['pass']
		confpw = request.form['confirm']
		#DATABASE IS DROPPED HELP
		if inspect(db.engine).has_table('users'):
			foundUser = users.query.filter_by(name=user).first()
		else:
		    # Handle the case where the table does not exist
			foundUser = None
			print("The users table does not exist. Skipping query.")
		#foundUser = users.query.filter_by(name=user).first();
		if foundUser:
			flash("Username is taken", "info")
			return redirect(url_for("signup"))
		elif pw != confpw:
			flash("Passwords don't match!", "info")
			return redirect(url_for("signup"))
		elif (email.find("@") == -1 and email.find(".") == -1) or ((email.find("@") == -1) != (email.find(".") == -1)):
			flash("Invalid email", "info")
			return redirect(url_for("signup"))
		else:
			session["user"] = user
			session["email"] = email;
			newUser = users(user, email, pw)
			db.session.add(newUser)
			db.session.commit()
			flash("Account created!", "info")
			return redirect(url_for("user"))

	else:
		return render_template('signup.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
	if request.method == "POST":
		session.permanent = True;
		useremail = request.form['usr']
		pw = request.form['pass']
		foundUser = users.query.filter_by(name=useremail).first();
		foundEmail = users.query.filter_by(email=useremail).first();
		if foundUser:
			if pw == foundUser.password:
				session["user"] = foundUser.name
				session["email"] = foundUser.email
				return redirect(url_for("user"))
			else:
				flash("Wrong password/username", "info")
				return redirect(url_for("login"))
		elif foundEmail:
			if pw == foundEmail.password:
				session["user"] = foundEmail.name
				session["email"] = foundEmail.email
				return redirect(url_for("user"))
			else:
				flash("Wrong password/username", "info")
				return redirect(url_for("login"))
		else:
			flash("There's no account with that user/email", "info")
			return redirect(url_for("login"))
	else:
		return render_template('login.html')


#ACTUAL PAGE

@app.route("/user")
def user():
	if "user" in session and users.query.filter_by(name=session["user"]).first():
		user = session["user"]
		return render_template('userPage.html', usrNm = user, posts = posts.query.order_by(posts.created_at.desc()).limit(8).all(),
						top = db.session.query(
						posts.city,
						posts.country,
						func.avg(posts.overall).label('avg_overall')
						).group_by(posts.city, posts.country).order_by(desc('avg_overall')).limit(5).all())
	else:
		return redirect(url_for("home"))

#get more posts
@app.route('/load_more_posts', methods=['GET'])
def load_more_posts():
    offset = int(request.args.get('offset'))
    more_posts = posts.query.order_by(posts.created_at.desc()).offset(offset).limit(5).all()
    posts_data = [{'created_at': post.created_at.strftime('%B %d %Y'), 'user': post.user, 'overall': post.overall,
                   'writtenReview': post.writtenReview, 'city': post.city, 'country': post.country} for post in more_posts]
    return jsonify(posts_data)


@app.route('/get_city_suggestions', methods=['GET'])
def get_city_suggestions():
    query = request.args.get('citySearch', '').lower()
    matching_cities = [city for city in cities if query in city.lower()]
    return jsonify(matching_cities)

@app.route('/get_country_suggestions', methods=['GET'])
def get_country_suggestions():
    query = request.args.get('countrySearch', '').lower()
    matching_countries = [country for country in countries if query in country.lower()]
    return jsonify(matching_countries)

@app.route("/logout")
def logout():
	if "user" in session:
		flash("You've been logged out", "info")
		session.pop("user", None)
		session.pop("email", None)
	return redirect(url_for("login"))
@app.route("/about")
def about():
	return "about";

@app.route("/settings", methods=["POST", "GET"])
def settings():

	if 'user' in session:
		return render_template('settings.html')
	else:
		return redirect(url_for("home"))

@app.route("/nameChange", methods=["POST"])
def nameChange():
	nN = request.form["newName"]
	if (len(nN) > 0) and not(users.query.filter_by(name=nN).first()):
		
		old = users.query.filter_by(name=session["user"])
		oldPass = old.first().password
		old.delete()
		db.session.add(users(nN, session["email"], oldPass))
		db.session.commit()
		session["user"] = nN
		flash("Name changed!", "info")
	elif len(request.form["newName"]) > 0:
		flash("Name is already taken", "info")
	else:
		flash("New name is too short!", "info")
	return redirect(url_for("settings"))

@app.route("/emailChange", methods=["POST"])
def emailChange():
	if len(request.form["newEmail"]) > 0:
		nE = request.form["newEmail"]
		old = users.query.filter_by(name=session["user"])
		oldPass = old.first().password
		old.delete()
		db.session.add(users(session["user"], session["email"], oldPass))
		db.session.commit()
		session["email"] = nE
		flash("Email changed!", "info")
	else:
		flash("New Email is too short!", "info")

	return redirect(url_for("settings"))


@app.route("/post", methods=["POST", "GET"])
def post():

	if request.method == "POST":
		ease = request.form["eot"]
		cost = request.form["col"]
		hosp = request.form["h"]
		excite = request.form["ae"]
		overall = request.form["overall"]
		written = request.form["review"]

		#auto caps the names of places to be able to store
		locCountry = autoCap(request.form["country"])
		locCity = autoCap(request.form["city"])
		in_US = False
		#add to DB
		if (len(locCity) > 0 and len(locCountry) > 0):
			db.session.add(posts(ease, cost, hosp, excite, overall, session['user'], written, locCountry, locCity, in_US))
			db.session.commit()
		else:
			flash("Post not uploaded: No location was given!")
		return redirect(url_for('user'))
	else:
		if "user" in session and users.query.filter_by(name=session["user"]).first():
			user = session["user"]
			return render_template('poster.html')
			#return f"<h1>Welcome {user}!</h1> "
		else:
			return redirect(url_for("home"))
		

#VIEWING PLACES
@app.route("/place", methods=["GET", "POST"])
def place():
	avgOverall = 0
	avgEase = 0
	avgCost = 0
	avgHosp = 0
	avgAct = 0
	postNum = 0
	if request.method == "POST":
		city = autoCap(request.form["citySearch"])
		country = autoCap(request.form["countrySearch"])
		collection = posts.query.filter_by(city = city, country = country).all()

		if (len(collection) > 0):
			for post in collection:
				avgOverall += post.overall
				avgEase += post.easeOfTravel
				avgCost += post.costOfLiving
				avgHosp += post.hospitality
				avgAct += post.activities
				postNum += 1

			return render_template("placePage.html", city = city, country = country, posts = collection, ovrall=(avgOverall/postNum), ease=(avgEase/postNum), cost=(avgCost/postNum), hosp=(avgHosp/postNum), act=(avgAct/postNum), empty=False)
		else:
			return render_template("placePage.html", city = city, country = country, posts = collection, ovrall="N/A", ease="N/A", cost="N/A", hosp="N/A", act="N/A", empty=True)
	else:
		city = request.args.get("city")
		country = request.args.get("country")
		collection = posts.query.filter_by(city = city, country = country).all()

		city = autoCap(city)
		country = autoCap(country)

		if (len(collection) > 0):
			for post in collection:
				avgOverall += post.overall
				avgEase += post.easeOfTravel
				avgCost += post.costOfLiving
				avgHosp += post.hospitality
				avgAct += post.activities
				postNum += 1

			return render_template("placePage.html", city = city, country = country, posts = collection, ovrall=(avgOverall/postNum), ease=(avgEase/postNum), cost=(avgCost/postNum), hosp=(avgHosp/postNum), act=(avgAct/postNum), empty=False)
		else:
			return render_template("placePage.html", city = city, country = country, posts = collection, ovrall="N/A", ease="N/A", cost="N/A", hosp="N/A", act="N/A", empty=True)




@app.route("/admin")
def admin():
	return render_template('dbView.html', accounts = users.query.all());
@app.route("/postsview")
def postsview():
	return render_template('postview.html', posts = posts.query.all());
@app.route("/dbclear")
def dbclear():
	db.session.query(users).delete()
	db.session.query(posts).delete()
	db.session.commit()
	return redirect(url_for('home'))
@app.route("/postsclear")
def postsclear():
	db.session.query(posts).delete()
	db.session.commit()
	return redirect(url_for('user'))
@app.route("/dbreset")
def dbreset():
	db.drop_all()
	return redirect(url_for('home'))

#auto caps function
def autoCap(name):
	name = name.lower()
	space = False
	ans = ""
	ind = 0
	if (len(name) > 0):
		if (name.find("city") >= 0):
			name = name[:name.find("city")]
		if (name[-1] == " "):
			name = name[:-1]
		for i in name:
			if (i == " "):
				space = True
				ans += i
			elif ((name.index(i) == 0 and ind == 0) or space == True):
				ind +=1
				ans += i.upper()
				space = False;
			else:
				ans += i
	return ans

if __name__ == '__main__':
	with app.app_context():
		db.create_all()
	app.run(debug=True);
	