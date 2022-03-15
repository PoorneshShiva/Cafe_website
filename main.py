import os

from flask import Flask, jsonify, render_template, request, \
    get_flashed_messages, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import *
import random
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import *
from wtforms.validators import DataRequired, URL


class AddCafe(FlaskForm):
    name = StringField("Name", validators=[DataRequired()],  render_kw={"placeholder": "eg: Wonder Cafe"} )
    map_url = URLField("Map URL", validators=[DataRequired()], render_kw={"placeholder": "eg: https://www.google.com/maps/place/Mini+Coffee+Day/@12.9416893,77.5522817,15z/data=!4m9!1m2!2m1!1scafe+near+me!3m5!1s0x3bae3ff7a9753c55:0xdb5ed2c4c05f5e6e!8m2!3d12.9416893!4d77.5610364!15sCgxjYWZlIG5lYXIgbWUiA5ABAVoOIgxjYWZlIG5lYXIgbWWSAQRjYWZl"})
    img_url = URLField("Img URL", validators=[DataRequired()], render_kw={"placeholder":"eg: https://lh5.googleusercontent.com/p/AF1QipM4XfafWGvsN1-r3xrq1X8PLmzDLLRyXDlZ_DN1=w408-h544-k-no"})
    location = StringField("Location", validators=[DataRequired()], render_kw={"placeholder": "eg: Church Street"})
    seats = StringField("Number of Seats", validators=[DataRequired()], render_kw={"placeholder": "eg: 20-40"})
    has_toilet = RadioField(label="Toilets", choices=["Great", "Good"], validators=[DataRequired()])
    has_wifi = RadioField("Wifi", choices=["Strong", "Weak"], validators=[DataRequired()])
    has_sockets = RadioField("Sockets", choices=["Few", "None"], validators=[DataRequired()])
    can_take_calls = RadioField("Calls", choices=["Noisy", "Less Noisy"], validators=[DataRequired()])
    coffee_price = StringField("Coffee Price", validators=[DataRequired()], render_kw={"placeholder": "eg: £1.50"})
    city = StringField("City", validators=[DataRequired()])
    submit = SubmitField("Add")


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY')
Bootstrap(app)
# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///cafes.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

print(db.Model)


# Cafe TABLE Configuration
class Cafe(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(250), unique=True, nullable=False)
    map_url = Column(String(500), nullable=False)
    img_url = Column(String(500), nullable=False)
    location = Column(String(250), nullable=False)
    seats = Column(String(250), nullable=False)
    has_toilet = Column(Boolean, nullable=False)
    has_wifi = Column(Boolean, nullable=False)
    has_sockets = Column(Boolean, nullable=False)
    can_take_calls = Column(Boolean, nullable=False)
    coffee_price = Column(String(250), nullable=True)
    city = Column(String(250), nullable=False)


@app.route("/")
def home():
    return render_template("index.html")


@app.route('/random', methods=["GET"])
def get_random_cafe():
    all_cafes = db.session.query(Cafe).all()
    random_cafe = random.choice(all_cafes).__dict__

    first = dict(list(random_cafe.items())[1:])
    print(first)
    new = {
        "cafe": first
    }
    return jsonify(new)


@app.route('/all', methods=["GET"])
def all_cafes():
    cafes_from_db = db.session.query(Cafe).all()
    print(cafes_from_db)
    cafes = []
    for each in cafes_from_db:
        cafe = each.__dict__
        cafes.append(dict(list(cafe.items())[1:]))
    cafes_dict = {"cafes": cafes}
    return jsonify(cafes_dict)


@app.route('/search')
def search():
    location = request.args.get('loc').title()
    cafes_at_location = Cafe.query.filter_by(location=location).all()

    cafe = [dict(list(each.__dict__.items())[1:]) for each in cafes_at_location]

    if len(cafe) > 0:
        cafe_dict = {
            "cafes": cafe
        }
    else:
        cafe_dict = {
            "error": {"Not Found": "Sorry, we don't have a cafe at that location."}
        }
    return jsonify(cafe_dict)


@app.route('/add', methods=['POST', 'GET'])
def add():
    name = request.args.get("name")
    map_url = request.args.get("map_url")
    img_url = request.args.get("img_url")
    location = request.args.get("location")
    has_sockets = int(request.args.get("has_sockets"))
    has_toilet = int(request.args.get("has_toilet"))
    has_wifi = int(request.args.get("has_wifi"))
    can_take_calls = int(request.args.get("can_take_calls"))
    seats = request.args.get("seats")
    coffee_price = request.args.get("coffee_price")
    city = request.args.get('city')

    try:
        new_cafe = Cafe(name=name, map_url=map_url, img_url=img_url, location=location, has_sockets=has_sockets,
                        has_toilet=has_toilet,
                        has_wifi=has_wifi, can_take_calls=can_take_calls, seats=seats, coffee_price=coffee_price,
                        city=city)
        db.session.add(new_cafe)
        db.session.commit()
    except:
        parameters = {
            "response": {
                "response": {
                    "Failed": "Cafe is Already Stored"
                }
            }
        }
    else:
        parameters = {
            "response": {
                "success": "Successfully added the new cafe"
            }
        }

    return jsonify(parameters)


@app.route('/update-price/<cafe_id>', methods=["PATCH"])
def update(cafe_id):
    cafe_price_to_change = Cafe.query.get(cafe_id)
    new_price = request.args.get('new_price')

    try:
        cafe_price_to_change.coffee_price = new_price
        db.session.commit()
        parameter = {
            "success": "Successfully changed the price"
        }
    except:
        parameter = {
            "error": {
                "Not Found": "Sorry, a cafe with that id was not found in the database"
            }
        }

    return jsonify(parameter)


@app.route('/report-closed/<int:number>', methods=["Delete"])
def delete(number):
    api_key = request.args.get("api-key")
    if api_key == "TopSecretAPIKey":
        try:
            cafe_to_delete = Cafe.query.get(number)
            db.session.delete(cafe_to_delete)
            db.session.commit()
            param = {
                "Success": "Successfully deleted the cafe."
            }
        except:
            param = {
                "error": {
                    "Not Found": "Sorry, a cafe with that id was not found in the database"
                }
            }

    else:
        param = {
            "error": "Sorry, that's not allowed. Make sure you have the correct api_key"
        }

    return jsonify(param)


@app.route('/location')
def location():
    return render_template('location.html')


@app.route('/location/<place>')
def cafes_at_location(place):
    print(place)
    cafes = Cafe.query.filter_by(city=place).all()
    cafe = [each for each in cafes]
    print(cafe)
    # cafe = [dict(list(each.__dict__.items())[1:]) for each in cafes]
    # print(cafe)
    return render_template('city.html', city=place, cafes=cafe)


@app.route('/location/<place>/add-new-cafe', methods=["GET", "POST"])
def add_new_cafe(place):
    form = AddCafe()
    if request.method == "POST":
            name = form.name.data
            map_url = form.map_url.data
            img_url = form.img_url.data
            location = form.location.data
            seats = form.seats.data
            has_toilet = form.has_toilet.data
            has_wifi = form.has_wifi.data
            has_sockets = form.has_sockets.data
            calls = form.can_take_calls.data
            city = form.city.data
            coffee_price = form.coffee_price.data

            print('yes')
            if has_sockets == "Few":
                has_sockets = 1
            else:
                has_sockets = 0
            if has_toilet == "Great":
                has_toilet = 1
            else:
                has_toilet = 0
            if has_wifi == "Strong":
                has_wifi = 1
            else:
                has_wifi = 0
            if calls == "Noisy":
                calls = 1
            else:
                calls = 0
            print(name, map_url, img_url, location, seats, has_sockets, has_toilet, has_wifi, calls, coffee_price)
            try:
                new_cafe = Cafe(name=name, map_url=map_url, img_url=img_url,
                                location=location, seats=seats,
                                has_sockets=has_sockets, has_toilet=has_toilet,
                                has_wifi=has_wifi, city=place,
                                coffee_price=coffee_price, can_take_calls=calls)
                db.session.add(new_cafe)
                db.session.commit()
            except:
                flash(f"The {name} is already in the location")
                return render_template("add_new_cafe.html", form=form)
            else:
                flash(f"The {name} saved successfully!")
                return render_template("add_new_cafe.html", form=form)



    else:

        return render_template("add_new_cafe.html", form=form)

@app.route("/location/<place>/check", methods=["POST", "GET"])
def check(place):
    form = AddCafe()
    print(form.validate_on_submit())
    print('yes')
    name = form.name.data
    map_url = form.map_url.data
    img_url = form.img_url.data
    location = form.location.data
    seats = form.seats.data
    has_toilet = form.has_toilet.data
    has_wifi = form.has_wifi.data
    has_sockets = form.has_sockets.data

    coffee_price = form.coffee_price.data
    print('yes')
    print(name, map_url, img_url, location, seats, has_sockets, has_toilet, has_wifi, city, coffee_price)
    return place


@app.route('/delete_cafe', methods=["POST", "GET", "DELETE"])
def delete_cafe():
    if request.method == "POST":
        secret_key = request.form.get("secret_key")
        pl = request.args.get("location")
        if secret_key == "TOPSECRETKEY":
            name = request.args.get("name")

            print(name)
            print(pl)

            print(secret_key)

            cafe_to_delete = Cafe.query.filter_by(name=name).first()
            db.session.delete(cafe_to_delete)
            db.session.commit()
            flash(f"The {name} Successfully Deleted")
            return redirect(url_for('cafes_at_location', place=pl))
        else:
            flash(f"Invalid Secret Key")
            return redirect(url_for('cafes_at_location', place=pl))


if __name__ == '__main__':
    app.run(host="0.0.0.0")
