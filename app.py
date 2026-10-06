
from flask import Flask, render_template, render_template_string
from flask import request, jsonify, session, redirect, url_for
import requests

app = Flask(__name__)
app.secret_key = "ridehub_secret_key_123"

HEADERS = {
    "User-Agent": "RideHub-College-Project/1.0"
}

PHOTON_URL = "https://photon.komoot.io/api"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

users = {}


# =========================================================
# LOGIN PAGE
# =========================================================

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Ride Hub - Login</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #e8f1ff, #f8fbff);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .box {
            width: 90%;
            max-width: 420px;
            background: white;
            padding: 35px;
            border-radius: 20px;
            box-shadow: 0 10px 35px rgba(0,0,0,0.12);
        }

        h1 {
            text-align: center;
            color: #1769ff;
            margin-bottom: 8px;
        }

        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 25px;
        }

        input {
            width: 100%;
            padding: 14px;
            margin-bottom: 15px;
            border: 1px solid #ccc;
            border-radius: 10px;
            font-size: 15px;
        }

        button {
            width: 100%;
            padding: 14px;
            border: none;
            border-radius: 10px;
            background: #1769ff;
            color: white;
            font-size: 16px;
            cursor: pointer;
        }

        button:hover {
            background: #0d55d8;
        }

        .create {
            text-align: center;
            margin-top: 18px;
        }

        .create a {
            color: #1769ff;
            text-decoration: none;
            font-weight: bold;
        }

        .error {
            background: #ffe7e7;
            color: #c62828;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 15px;
            text-align: center;
        }
    </style>
</head>

<body>

<div class="box">

    <h1>🚗 Ride Hub</h1>

    <div class="subtitle">
        Compare your rides easily
    </div>

    {% if error %}
        <div class="error">{{ error }}</div>
    {% endif %}

    <form method="POST">

        <input
            type="email"
            name="email"
            placeholder="Enter your email"
            required
        >

        <input
            type="password"
            name="password"
            placeholder="Enter your password"
            required
        >

        <button type="submit">
            Login
        </button>

    </form>

    <div class="create">
        Don't have an account?
        <a href="/create-account">Create Account</a>
    </div>

</div>

</body>
</html>
"""


# =========================================================
# CREATE ACCOUNT PAGE
# =========================================================

CREATE_ACCOUNT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Create Account - Ride Hub</title>

    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <style>

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #e8f1ff, #f8fbff);
            min-height: 100vh;

            display: flex;
            justify-content: center;
            align-items: center;
        }

        .box {
            width: 90%;
            max-width: 420px;
            background: white;
            padding: 35px;
            border-radius: 20px;

            box-shadow:
                0 10px 35px rgba(0,0,0,0.12);
        }

        h1 {
            text-align: center;
            color: #1769ff;
            margin-bottom: 25px;
        }

        input {
            width: 100%;
            padding: 14px;
            margin-bottom: 15px;

            border: 1px solid #ccc;
            border-radius: 10px;

            font-size: 15px;
        }

        button {
            width: 100%;
            padding: 14px;

            border: none;
            border-radius: 10px;

            background: #1769ff;
            color: white;

            font-size: 16px;
            cursor: pointer;
        }

        button:hover {
            background: #0d55d8;
        }

        .back {
            text-align: center;
            margin-top: 18px;
        }

        .back a {
            color: #1769ff;
            text-decoration: none;
            font-weight: bold;
        }

        .error {
            background: #ffe7e7;
            color: #c62828;

            padding: 10px;
            border-radius: 8px;

            margin-bottom: 15px;
            text-align: center;
        }

        .success {
            background: #e5f8e9;
            color: #218838;

            padding: 10px;
            border-radius: 8px;

            margin-bottom: 15px;
            text-align: center;
        }

    </style>
</head>

<body>

<div class="box">

    <h1>🚗 Create Account</h1>

    {% if error %}
        <div class="error">{{ error }}</div>
    {% endif %}

    {% if success %}
        <div class="success">{{ success }}</div>
    {% endif %}

    <form method="POST">

        <input
            type="email"
            name="email"
            placeholder="Enter your email"
            required
        >

        <input
            type="password"
            name="password"
            placeholder="Create password"
            required
        >

        <input
            type="password"
            name="confirm_password"
            placeholder="Confirm password"
            required
        >

        <button type="submit">
            Create Account
        </button>

    </form>

    <div class="back">
        Already have an account?
        <a href="/login">Login</a>
    </div>

</div>

</body>
</html>
"""


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login_page():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if email == "admin@gmail.com" and password == "admin123":
            session["user"] = email
            return redirect(url_for("home"))

        if email in users and users[email] == password:
            session["user"] = email
            return redirect(url_for("home"))

        return render_template_string(
            LOGIN_HTML,
            error="Invalid email or password."
        )

    return render_template_string(
        LOGIN_HTML,
        error=None
    )


# =========================================================
# LOGIN ALIAS
# =========================================================

app.add_url_rule(
    "/login-page",
    endpoint="login",
    view_func=login_page,
    methods=["GET", "POST"]
)


# =========================================================
# CREATE ACCOUNT
# =========================================================

@app.route("/create-account", methods=["GET", "POST"])
def create_account():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not email or not password:
            return render_template_string(
                CREATE_ACCOUNT_HTML,
                error="Please fill all fields.",
                success=None
            )

        if password != confirm_password:
            return render_template_string(
                CREATE_ACCOUNT_HTML,
                error="Passwords do not match.",
                success=None
            )

        if email in users:
            return render_template_string(
                CREATE_ACCOUNT_HTML,
                error="Account already exists.",
                success=None
            )

        users[email] = password

        return redirect(url_for("login_page"))

    return render_template_string(
        CREATE_ACCOUNT_HTML,
        error=None,
        success=None
    )


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    return create_account()


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login_page"))


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    if "user" not in session:
        return redirect(url_for("login_page"))

    return render_template("index.html")


# =========================================================
# LOCATION SEARCH / AUTOCOMPLETE
# =========================================================

@app.route("/location-suggestions")
def location_suggestions():

    query = request.args.get("q", "").strip()

    if len(query) < 2:
        return jsonify([])

    try:

        response = requests.get(
            PHOTON_URL,
            params={
                "q": query,
                "limit": 6
            },
            headers=HEADERS,
            timeout=8
        )

        if response.status_code != 200:
            return jsonify([])

        data = response.json()

        suggestions = []

        for feature in data.get("features", []):

            properties = feature.get(
                "properties",
                {}
            )

            name = properties.get("name", "")

            city = (
                properties.get("city")
                or properties.get("town")
                or properties.get("village")
                or ""
            )

            state = properties.get(
                "state",
                ""
            )

            country = properties.get(
                "country",
                ""
            )

            parts = []

            for part in [name, city, state, country]:

                if part and part not in parts:
                    parts.append(str(part))

            address = ", ".join(parts)

            if address and address not in suggestions:
                suggestions.append(address)

        return jsonify(suggestions[:6])

    except Exception:
        return jsonify([])


# =========================================================
# GEOCODING
# =========================================================

def get_coordinates(location):

    try:

        response = requests.get(
            PHOTON_URL,
            params={
                "q": location,
                "limit": 1
            },
            headers=HEADERS,
            timeout=10
        )

        if response.status_code != 200:
            return None

        data = response.json()

        features = data.get(
            "features",
            []
        )

        if not features:
            return None

        coordinates = features[0].get(
            "geometry",
            {}
        ).get(
            "coordinates",
            []
        )

        if len(coordinates) < 2:
            return None

        longitude = coordinates[0]
        latitude = coordinates[1]

        return latitude, longitude

    except Exception:
        return None


# =========================================================
# ROUTE
# =========================================================

def get_route(
    source_lat,
    source_lon,
    destination_lat,
    destination_lon
):

    try:

        url = (
            f"{OSRM_URL}/"
            f"{source_lon},{source_lat};"
            f"{destination_lon},{destination_lat}"
        )

        response = requests.get(
            url,
            params={
                "overview": "false"
            },
            headers=HEADERS,
            timeout=15
        )

        if response.status_code != 200:
            return None

        data = response.json()

        routes = data.get(
            "routes",
            []
        )

        if not routes:
            return None

        distance_km = (
            routes[0]["distance"] / 1000
        )

        duration_min = (
            routes[0]["duration"] / 60
        )

        return (
            round(distance_km, 2),
            round(duration_min)
        )

    except Exception:
        return None


# =========================================================
# VEHICLE DATA
# =========================================================

VEHICLE_DATA = {

    "Bike": {

        "Rapido": {
            "base": 25,
            "per_km": 8.0
        },

        "Uber": {
            "base": 30,
            "per_km": 8.5
        },

        "Ola": {
            "base": 28,
            "per_km": 8.2
        }
    },

    "Auto": {

        "Rapido": {
            "base": 35,
            "per_km": 14.0
        },

        "Uber": {
            "base": 40,
            "per_km": 15.0
        },

        "Ola": {
            "base": 38,
            "per_km": 14.5
        }
    },

    "Car": {

        "Rapido": {
            "base": 60,
            "per_km": 22.0
        },

        "Uber": {
            "base": 70,
            "per_km": 24.0
        },

        "Ola": {
            "base": 65,
            "per_km": 23.0
        }
    }
}


RATINGS = {

    "Rapido": {
        "Bike": 4.5,
        "Auto": 4.4,
        "Car": 4.3
    },

    "Uber": {
        "Bike": 4.6,
        "Auto": 4.5,
        "Car": 4.6
    },

    "Ola": {
        "Bike": 4.3,
        "Auto": 4.4,
        "Car": 4.4
    }
}


# =========================================================
# FARE CALCULATION
# =========================================================

def calculate_fare(
    company,
    vehicle,
    distance,
    route_factor
):

    data = VEHICLE_DATA[
        vehicle
    ][company]

    base = data["base"]
    per_km = data["per_km"]

    if company == "Rapido":

        variation = (
            (route_factor * 7 + 3)
            % 41
        ) - 20

    elif company == "Uber":

        variation = (
            (route_factor * 13 + 9)
            % 41
        ) - 20

    else:

        variation = (
            (route_factor * 19 + 15)
            % 41
        ) - 20

    fare = (
        base
        + (distance * per_km)
        + variation
    )

    minimum_fare = {

        "Bike": 50,
        "Auto": 70,
        "Car": 120
    }

    fare = max(
        minimum_fare[vehicle],
        fare
    )

    return round(fare)


# =========================================================
# TIME CALCULATION
# =========================================================

TIME_MULTIPLIERS = {

    "Bike": {
        "Rapido": 0.80,
        "Uber": 1.10,
        "Ola": 0.95
    },

    "Auto": {
        "Rapido": 0.95,
        "Uber": 1.25,
        "Ola": 1.10
    },

    "Car": {
        "Rapido": 0.90,
        "Uber": 1.20,
        "Ola": 1.05
    }
}


TIME_OFFSETS = {

    "Bike": {
        "Rapido": 1,
        "Uber": 5,
        "Ola": 3
    },

    "Auto": {
        "Rapido": 3,
        "Uber": 7,
        "Ola": 5
    },

    "Car": {
        "Rapido": 2,
        "Uber": 6,
        "Ola": 4
    }
}


def calculate_time(
    company,
    vehicle,
    route_time,
    route_factor
):

    multiplier = TIME_MULTIPLIERS[
        vehicle
    ][company]

    offset = TIME_OFFSETS[
        vehicle
    ][company]

    route_time_variation = (
        (
            route_factor
            + len(company)
            + len(vehicle)
        )
        % 3
    ) - 1

    estimated_time = (
        route_time * multiplier
        + offset
        + route_time_variation
    )

    return max(
        5,
        round(estimated_time)
    )

    # =========================================================
# COMPARE RIDES
# =========================================================

@app.route("/compare", methods=["POST"])
def compare():

    if "user" not in session:
        return redirect(url_for("login_page"))

    source = request.form.get(
        "source",
        ""
    ).strip()

    destination = request.form.get(
        "destination",
        ""
    ).strip()

    vehicle = request.form.get(
        "vehicleType",
        ""
    ).strip()

    if not vehicle:
        vehicle = request.form.get(
            "vehicle",
            ""
        ).strip()

    if not source or not destination:

        return render_template(
            "result.html",
            rides=[],
            source=source,
            destination=destination,
            vehicle=vehicle,
            distance=0,
            duration=0,
            overall=None,
            overall_suggestion=None,
            cheapest=None,
            fastest=None,
            highest_rated=None,
            error="Please enter pickup and destination."
        )

    # -----------------------------------------------------
    # GET PICKUP COORDINATES
    # -----------------------------------------------------

    source_coordinates = get_coordinates(source)

    if not source_coordinates:

        return render_template(
            "result.html",
            rides=[],
            source=source,
            destination=destination,
            vehicle=vehicle,
            distance=0,
            duration=0,
            overall=None,
            overall_suggestion=None,
            cheapest=None,
            fastest=None,
            highest_rated=None,
            error="Pickup location could not be found."
        )

    # -----------------------------------------------------
    # GET DESTINATION COORDINATES
    # -----------------------------------------------------

    destination_coordinates = get_coordinates(destination)

    if not destination_coordinates:

        return render_template(
            "result.html",
            rides=[],
            source=source,
            destination=destination,
            vehicle=vehicle,
            distance=0,
            duration=0,
            overall=None,
            overall_suggestion=None,
            cheapest=None,
            fastest=None,
            highest_rated=None,
            error="Destination location could not be found."
        )

    # -----------------------------------------------------
    # GET ROUTE
    # -----------------------------------------------------

    route = get_route(
        source_coordinates[0],
        source_coordinates[1],
        destination_coordinates[0],
        destination_coordinates[1]
    )

    if not route:

        return render_template(
            "result.html",
            rides=[],
            source=source,
            destination=destination,
            vehicle=vehicle,
            distance=0,
            duration=0,
            overall=None,
            overall_suggestion=None,
            cheapest=None,
            fastest=None,
            highest_rated=None,
            error="Could not calculate the route."
        )

    distance, duration = route

    # -----------------------------------------------------
    # VEHICLES
    # -----------------------------------------------------

    if vehicle.lower() in [
        "all",
        "all vehicles"
    ]:

        vehicles = [
            "Bike",
            "Auto",
            "Car"
        ]

    elif vehicle in [
        "Bike",
        "Auto",
        "Car"
    ]:

        vehicles = [vehicle]

    else:

        vehicles = [
            "Bike",
            "Auto",
            "Car"
        ]

    # -----------------------------------------------------
    # COMPANIES
    # -----------------------------------------------------

    companies = [
        "Rapido",
        "Uber",
        "Ola"
    ]

    rides = []

    # -----------------------------------------------------
    # ROUTE FACTOR
    # -----------------------------------------------------

    route_text = (
        source.lower()
        + "|"
        + destination.lower()
    )

    route_factor = sum(
        ord(character)
        for character in route_text
    )

    # =====================================================
    # CREATE ALL RIDES
    # =====================================================

    for current_vehicle in vehicles:

        for company in companies:

            # -------------------------------------------------
            # DIFFERENT TIME FOR APP + VEHICLE
            # -------------------------------------------------

            ride_time = calculate_time(
                company,
                current_vehicle,
                duration,
                route_factor
            )

            # -------------------------------------------------
            # PRICE
            # -------------------------------------------------

            fare = calculate_fare(
                company,
                current_vehicle,
                distance,
                route_factor
            )

            # -------------------------------------------------
            # RATING
            # -------------------------------------------------

            if company == "Rapido":

                rating_change = (
                    (
                        (route_factor * 5 + 1)
                        % 9
                    ) - 4
                ) * 0.03

            elif company == "Uber":

                rating_change = (
                    (
                        (route_factor * 7 + 3)
                        % 9
                    ) - 4
                ) * 0.03

            else:

                rating_change = (
                    (
                        (route_factor * 11 + 5)
                        % 9
                    ) - 4
                ) * 0.03

            rating = round(
                max(
                    4.0,
                    min(
                        4.9,
                        RATINGS[
                            company
                        ][
                            current_vehicle
                        ] + rating_change
                    )
                ),
                2
            )

            # -------------------------------------------------
            # REVIEW
            # -------------------------------------------------

            if rating >= 4.6:

                review = "Excellent"

            elif rating >= 4.4:

                review = "Very Good"

            elif rating >= 4.2:

                review = "Good"

            else:

                review = "Average"

            # -------------------------------------------------
            # ADD RIDE
            # -------------------------------------------------

            rides.append({

                "company": company,

                "vehicle": current_vehicle,

                "price": fare,

                "fare": fare,

                "time": ride_time,

                "duration": ride_time,

                "distance": distance,

                "rating": rating,

                "review": review,

                "score": 0

            })

    # =====================================================
    # FIND OVERALL BEST RIDE
    # =====================================================

    overall = None
    cheapest = None
    fastest = None
    highest_rated = None

    if rides:

        # -------------------------------------------------
        # PRICE RANGE
        # -------------------------------------------------

        prices = [
            ride["price"]
            for ride in rides
        ]

        min_price = min(prices)
        max_price = max(prices)

        # -------------------------------------------------
        # TIME RANGE
        # -------------------------------------------------

        times = [
            ride["time"]
            for ride in rides
        ]

        min_time = min(times)
        max_time = max(times)

        # -------------------------------------------------
        # RATING RANGE
        # -------------------------------------------------

        ratings = [
            ride["rating"]
            for ride in rides
        ]

        min_rating = min(ratings)
        max_rating = max(ratings)

        # -------------------------------------------------
        # BALANCED SCORE
        # -------------------------------------------------

        for ride in rides:

            # PRICE SCORE

            if max_price == min_price:

                price_score = 100

            else:

                price_score = (
                    (
                        max_price
                        - ride["price"]
                    )
                    /
                    (
                        max_price
                        - min_price
                    )
                ) * 100

            # TIME SCORE

            if max_time == min_time:

                time_score = 100

            else:

                time_score = (
                    (
                        max_time
                        - ride["time"]
                    )
                    /
                    (
                        max_time
                        - min_time
                    )
                ) * 100

            # RATING SCORE

            if max_rating == min_rating:

                rating_score = 100

            else:

                rating_score = (
                    (
                        ride["rating"]
                        - min_rating
                    )
                    /
                    (
                        max_rating
                        - min_rating
                    )
                ) * 100

            # -------------------------------------------------
            # FINAL SCORE
            # -------------------------------------------------

            final_score = (
                price_score * 0.35
                +
                time_score * 0.30
                +
                rating_score * 0.35
            )

            ride["score"] = round(
                final_score,
                2
            )

        # -------------------------------------------------
        # ONE OVERALL WINNER
        # -------------------------------------------------

        overall = max(
            rides,
            key=lambda ride: ride["score"]
        )

        # -------------------------------------------------
        # OTHER HIGHLIGHTS
        # -------------------------------------------------

        cheapest = min(
            rides,
            key=lambda ride: ride["price"]
        )

        fastest = min(
            rides,
            key=lambda ride: ride["time"]
        )

        highest_rated = max(
            rides,
            key=lambda ride: ride["rating"]
        )

    # =====================================================
    # SEND DATA TO RESULT PAGE
    # =====================================================

    return render_template(

        "result.html",

        rides=rides,

        source=source,

        destination=destination,

        vehicle=vehicle,

        distance=distance,

        duration=duration,

        overall=overall,

        overall_suggestion=overall,

        cheapest=cheapest,

        fastest=fastest,

        highest_rated=highest_rated,

        error=None
    )


# =========================================================
# CURRENT LOCATION → ADDRESS
# =========================================================

@app.route("/reverse-location")
def reverse_location():

    latitude = request.args.get("lat")
    longitude = request.args.get("lon")

    if not latitude or not longitude:

        return jsonify({

            "success": False,

            "message":
                "Could not get your current location."

        }), 400

    try:

        response = requests.get(

            "https://nominatim.openstreetmap.org/reverse",

            params={

                "lat": latitude,

                "lon": longitude,

                "format": "json",

                "zoom": 18,

                "addressdetails": 1

            },

            headers={

                "User-Agent":
                    "RideHub-College-Project/1.0"

            },

            timeout=15

        )

        if response.status_code != 200:

            return jsonify({

                "success": False,

                "message":
                    "Could not find your address."

            })

        data = response.json()

        address_data = data.get(
            "address",
            {}
        )

        parts = [

            address_data.get(
                "house_number"
            ),

            address_data.get(
                "road"
            ),

            address_data.get(
                "neighbourhood"
            ),

            address_data.get(
                "suburb"
            ),

            address_data.get(
                "village"
            ),

            address_data.get(
                "town"
            ),

            address_data.get(
                "city"
            ),

            address_data.get(
                "district"
            ),

            address_data.get(
                "state"
            )

        ]

        clean_parts = []

        for part in parts:

            if (
                part
                and part not in clean_parts
            ):

                clean_parts.append(
                    str(part)
                )

        readable_address = ", ".join(
            clean_parts
        )

        if not readable_address:

            readable_address = data.get(
                "display_name",
                "Current Location"
            )

        return jsonify({

            "success": True,

            "address": readable_address

        })

    except Exception:

        return jsonify({

            "success": False,

            "message":
                "Unable to find your current address."

        })


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    return jsonify({

        "status":
            "Ride Hub backend is running",

        "login": True,

        "comparison": True,

        "location": True,

        "suggestions": True

    })


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    print()
    print("======================================")
    print("          RIDE HUB BACKEND")
    print("======================================")
    print("Server running...")
    print("Open: http://127.0.0.1:5000")
    print("======================================")
    print()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )