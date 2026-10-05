
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "ridehub_secret_key_123"

DATABASE = "ridehub.db"

HEADERS = {
    "User-Agent": "RideHub-College-Project/1.0"
}

PHOTON_URL = "https://photon.komoot.io/api"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


init_db()


# =========================================================
# LOGIN
# =========================================================

@app.route("/")
def login_page():

    if "user_id" in session:
        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_user():

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email or not password:
        return """
        <script>
            alert("Please enter email and password.");
            window.location.href="/";
        </script>
        """

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    conn.close()

    if user and check_password_hash(
        user["password"],
        password
    ):

        session["user_id"] = user["id"]
        session["email"] = user["email"]

        return redirect(url_for("home"))

    return """
    <script>
        alert("Invalid email or password.");
        window.location.href="/";
    </script>
    """


# =========================================================
# REGISTER
# =========================================================

@app.route("/register")
def register_page():

    if "user_id" in session:
        return redirect(url_for("home"))

    return render_template("register.html")


@app.route("/create_account", methods=["POST"])
def create_account():

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get(
        "confirm_password",
        ""
    )

    if not email or not password or not confirm_password:
        return """
        <script>
            alert("Please fill all fields.");
            window.location.href="/register";
        </script>
        """

    if password != confirm_password:
        return """
        <script>
            alert("Passwords do not match.");
            window.location.href="/register";
        </script>
        """

    conn = get_db()

    existing = conn.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    if existing:

        conn.close()

        return """
        <script>
            alert("Email already registered. Please login.");
            window.location.href="/";
        </script>
        """

    hashed_password = generate_password_hash(password)

    conn.execute(
        "INSERT INTO users (email, password) VALUES (?, ?)",
        (email, hashed_password)
    )

    conn.commit()
    conn.close()

    return """
    <script>
        alert("Account created successfully!");
        window.location.href="/";
    </script>
    """


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login_page")
    )


# =========================================================
# HOME
# =========================================================

@app.route("/home")
def home():

    if "user_id" not in session:
        return redirect(
            url_for("login_page")
        )

    return render_template(
        "index.html",
        email=session.get("email")
    )


# =========================================================
# LOCATION SEARCH
# =========================================================

@app.route("/search_location")
def search_location():

    query = request.args.get(
        "q",
        ""
    ).strip()

    if not query:
        return jsonify([])

    try:

        response = requests.get(
            PHOTON_URL,
            params={
                "q": query,
                "limit": 6
            },
            headers=HEADERS,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        results = []

        for feature in data.get(
            "features",
            []
        ):

            properties = feature.get(
                "properties",
                {}
            )

            geometry = feature.get(
                "geometry",
                {}
            )

            coordinates = geometry.get(
                "coordinates",
                []
            )

            if len(coordinates) < 2:
                continue

            lng = coordinates[0]
            lat = coordinates[1]

            parts = []

            for key in [
                "name",
                "street",
                "district",
                "city",
                "state",
                "country"
            ]:

                value = properties.get(key)

                if value and str(value) not in parts:
                    parts.append(str(value))

            name = ", ".join(parts)

            if not name:
                name = query

            results.append({
                "name": name,
                "lat": lat,
                "lng": lng
            })

        return jsonify(results)

    except Exception as e:

        print(
            "Location search error:",
            e
        )

        return jsonify([])


# =========================================================
# LIVE LOCATION
# =========================================================

@app.route("/reverse_location")
def reverse_location():

    lat = request.args.get(
        "lat",
        ""
    ).strip()

    lng = request.args.get(
        "lng",
        ""
    ).strip()

    if not lat or not lng:

        return jsonify({
            "success": False,
            "name": "Unable to find current location"
        })

    # Photon reverse geocoding
    try:

        response = requests.get(
            PHOTON_URL,
            params={
                "lat": lat,
                "lon": lng
            },
            headers=HEADERS,
            timeout=10
        )

        if response.ok:

            data = response.json()

            features = data.get(
                "features",
                []
            )

            if features:

                properties = features[0].get(
                    "properties",
                    {}
                )

                parts = []

                for key in [
                    "name",
                    "street",
                    "district",
                    "city",
                    "state",
                    "country"
                ]:

                    value = properties.get(key)

                    if value and str(value) not in parts:
                        parts.append(str(value))

                if parts:

                    return jsonify({
                        "success": True,
                        "name": ", ".join(parts)
                    })

    except Exception as e:

        print(
            "Photon reverse error:",
            e
        )

    # Nominatim fallback
    try:

        response = requests.get(
            NOMINATIM_URL,
            params={
                "lat": lat,
                "lon": lng,
                "format": "json",
                "addressdetails": 1,
                "zoom": 18
            },
            headers=HEADERS,
            timeout=10
        )

        if response.ok:

            data = response.json()

            address = data.get(
                "address",
                {}
            )

            parts = []

            for key in [
                "house_number",
                "road",
                "neighbourhood",
                "suburb",
                "city_district",
                "city",
                "town",
                "village",
                "state",
                "postcode",
                "country"
            ]:

                value = address.get(key)

                if value and str(value) not in parts:
                    parts.append(str(value))

            if parts:

                return jsonify({
                    "success": True,
                    "name": ", ".join(parts)
                })

    except Exception as e:

        print(
            "Nominatim error:",
            e
        )

    return jsonify({
        "success": False,
        "name": "Current location found, but address unavailable"
    })


# =========================================================
# ROUTE
# =========================================================

def get_route(
    source_lat,
    source_lng,
    destination_lat,
    destination_lng
):

    try:

        coordinates = (
            f"{source_lng},{source_lat};"
            f"{destination_lng},{destination_lat}"
        )

        url = f"{OSRM_URL}/{coordinates}"

        response = requests.get(
            url,
            params={
                "overview": "false"
            },
            headers=HEADERS,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        routes = data.get(
            "routes",
            []
        )

        if not routes:
            return None

        route = routes[0]

        distance = route["distance"] / 1000
        time = route["duration"] / 60

        return {
            "distance": round(
                distance,
                2
            ),
            "time": max(
                5,
                round(time)
            )
        }

    except Exception as e:

        print(
            "Route error:",
            e
        )

        return None


# =========================================================
# FARE DATA
# =========================================================

FARE_DATA = {

    "Rapido": {
        "Bike": {
            "base": 30,
            "per_km": 9.0
        },
        "Auto": {
            "base": 40,
            "per_km": 13.0
        },
        "Car": {
            "base": 80,
            "per_km": 18.0
        }
    },

    "Uber": {
        "Bike": {
            "base": 32,
            "per_km": 9.5
        },
        "Auto": {
            "base": 42,
            "per_km": 13.5
        },
        "Car": {
            "base": 85,
            "per_km": 18.5
        }
    },

    "Ola": {
        "Bike": {
            "base": 34,
            "per_km": 9.2
        },
        "Auto": {
            "base": 43,
            "per_km": 13.2
        },
        "Car": {
            "base": 82,
            "per_km": 18.2
        }
    }
}


# =========================================================
# RATING DATA
# =========================================================

RATING_DATA = {

    "Rapido": {
        "Bike": 4.5,
        "Auto": 4.3,
        "Car": 4.4
    },

    "Uber": {
        "Bike": 4.6,
        "Auto": 4.5,
        "Car": 4.6
    },

    "Ola": {
        "Bike": 4.4,
        "Auto": 4.4,
        "Car": 4.5
    }
}


# =========================================================
# FARE CALCULATION
# =========================================================

def calculate_fare(
    company,
    vehicle,
    distance
):

    data = FARE_DATA[
        company
    ][vehicle]

    price = (
        data["base"]
        +
        distance * data["per_km"]
    )

    variation = int(
        distance * 7
    ) % 8

    price += variation

    return max(
        30,
        round(price)
    )


# =========================================================
# TIME CALCULATION
# =========================================================

def calculate_time(
    base_time,
    company,
    vehicle
):

    company_adjustment = {
        "Rapido": 0,
        "Uber": 1,
        "Ola": -1
    }

    vehicle_adjustment = {
        "Bike": 0,
        "Auto": 2,
        "Car": 3
    }

    time = (
        base_time
        + company_adjustment[company]
        + vehicle_adjustment[vehicle]
    )

    return max(
        5,
        round(time)
    )


# =========================================================
# REVIEW
# =========================================================

def get_review(rating):

    if rating >= 4.6:
        return "Excellent"

    if rating >= 4.4:
        return "Very Good"

    if rating >= 4.2:
        return "Good"

    return "Average"


# =========================================================
# CREATE RIDES
# =========================================================

def create_rides(
    distance,
    route_time,
    selected_vehicle
):

    companies = [
        "Rapido",
        "Uber",
        "Ola"
    ]

    all_vehicles = [
        "Bike",
        "Auto",
        "Car"
    ]

    if selected_vehicle == "All Vehicles":

        vehicle_list = [
            "Bike",
            "Auto",
            "Car"
        ]

    elif selected_vehicle in all_vehicles:

        vehicle_list = [
            selected_vehicle
        ]

    else:

        vehicle_list = [
            "Bike",
            "Auto",
            "Car"
        ]

    rides = []

    for company in companies:

        for vehicle in vehicle_list:

            price = calculate_fare(
                company,
                vehicle,
                distance
            )

            time = calculate_time(
                route_time,
                company,
                vehicle
            )

            rating = RATING_DATA[
                company
            ][vehicle]

            review = get_review(
                rating
            )

            rides.append({

                "company": company,

                "vehicle": vehicle,

                "price": price,

                "distance": round(
                    distance,
                    2
                ),

                "time": time,

                "rating": rating,

                "review": review,

                "score": 0

            })

    return rides

# =========================================================
# OVERALL BEST RIDE
# =========================================================

def calculate_overall(rides):

    if not rides:
        return None

    min_price = min(
        ride["price"]
        for ride in rides
    )

    max_price = max(
        ride["price"]
        for ride in rides
    )

    min_time = min(
        ride["time"]
        for ride in rides
    )

    max_time = max(
        ride["time"]
        for ride in rides
    )

    min_rating = min(
        ride["rating"]
        for ride in rides
    )

    max_rating = max(
        ride["rating"]
        for ride in rides
    )

    for ride in rides:

        # PRICE SCORE
        if max_price == min_price:
            price_score = 1
        else:
            price_score = (
                max_price - ride["price"]
            ) / (
                max_price - min_price
            )

        # TIME SCORE
        if max_time == min_time:
            time_score = 1
        else:
            time_score = (
                max_time - ride["time"]
            ) / (
                max_time - min_time
            )

        # RATING SCORE
        if max_rating == min_rating:
            rating_score = 1
        else:
            rating_score = (
                ride["rating"] - min_rating
            ) / (
                max_rating - min_rating
            )

        # OVERALL SCORE
        ride["score"] = round(
            (
                price_score * 0.40
                +
                time_score * 0.30
                +
                rating_score * 0.30
            ) * 100,
            2
        )

    return max(
        rides,
        key=lambda ride: ride["score"]
    )


# =========================================================
# COMPARE RIDES
# =========================================================

@app.route(
    "/compare",
    methods=["POST"]
)
def compare():

    if "user_id" not in session:

        return redirect(
            url_for("login_page")
        )

    try:

        # -------------------------------------------------
        # PICKUP LOCATION
        # -------------------------------------------------

        source = (
            request.form.get("source")
            or request.form.get("pickup")
            or request.form.get("from")
            or ""
        ).strip()

        # -------------------------------------------------
        # DESTINATION
        # -------------------------------------------------

        destination = (
            request.form.get("destination")
            or request.form.get("drop")
            or request.form.get("to")
            or ""
        ).strip()

        # -------------------------------------------------
        # VEHICLE
        # -------------------------------------------------

        vehicle = (
            request.form.get("vehicle")
            or request.form.get("vehicleType")
            or request.form.get("vehicle_type")
            or "All Vehicles"
        ).strip()

        # -------------------------------------------------
        # PICKUP COORDINATES
        # -------------------------------------------------

        source_lat = (
            request.form.get("source_lat")
            or request.form.get("pickup_lat")
            or request.form.get("sourceLat")
        )

        source_lng = (
            request.form.get("source_lng")
            or request.form.get("pickup_lng")
            or request.form.get("sourceLng")
        )

        # -------------------------------------------------
        # DESTINATION COORDINATES
        # -------------------------------------------------

        destination_lat = (
            request.form.get("destination_lat")
            or request.form.get("drop_lat")
            or request.form.get("destinationLat")
        )

        destination_lng = (
            request.form.get("destination_lng")
            or request.form.get("drop_lng")
            or request.form.get("destinationLng")
        )

        # -------------------------------------------------
        # CHECK PICKUP
        # -------------------------------------------------

        if not source:

            return """
            <script>
                alert("Please enter pickup location.");
                window.history.back();
            </script>
            """

        # -------------------------------------------------
        # CHECK DESTINATION
        # -------------------------------------------------

        if not destination:

            return """
            <script>
                alert("Please enter destination.");
                window.history.back();
            </script>
            """

        # -------------------------------------------------
        # CHECK COORDINATES
        # -------------------------------------------------

        if (
            source_lat is None
            or source_lng is None
            or destination_lat is None
            or destination_lng is None
        ):

            return """
            <script>
                alert(
                    "Please select pickup and destination from the suggestions."
                );
                window.history.back();
            </script>
            """

        # -------------------------------------------------
        # CONVERT COORDINATES
        # -------------------------------------------------

        source_lat = float(
            source_lat
        )

        source_lng = float(
            source_lng
        )

        destination_lat = float(
            destination_lat
        )

        destination_lng = float(
            destination_lng
        )

        # -------------------------------------------------
        # GET REAL ROUTE
        # -------------------------------------------------

        route = get_route(
            source_lat,
            source_lng,
            destination_lat,
            destination_lng
        )

        if route is None:

            return """
            <script>
                alert(
                    "Unable to calculate route. Please try again."
                );
                window.history.back();
            </script>
            """

        distance = route["distance"]

        route_time = route["time"]

        # -------------------------------------------------
        # CREATE RIDES
        # -------------------------------------------------

        rides = create_rides(
            distance,
            route_time,
            vehicle
        )

        if not rides:

            return """
            <script>
                alert("No rides found.");
                window.history.back();
            </script>
            """

        # -------------------------------------------------
        # LOWEST PRICE
        # -------------------------------------------------

        lowest_price = min(
            rides,
            key=lambda ride: ride["price"]
        )

        # -------------------------------------------------
        # FASTEST RIDE
        # -------------------------------------------------

        fastest_ride = min(
            rides,
            key=lambda ride: ride["time"]
        )

        # -------------------------------------------------
        # HIGHEST RATED
        # -------------------------------------------------

        highest_rated = max(
            rides,
            key=lambda ride: ride["rating"]
        )

        # -------------------------------------------------
        # OVERALL BEST
        # -------------------------------------------------

        overall = calculate_overall(
            rides
        )

        # -------------------------------------------------
        # SHOW RESULT PAGE
        # -------------------------------------------------

        return render_template(
            "result.html",

            source=source,

            destination=destination,

            vehicle=vehicle,

            distance=distance,

            route_time=route_time,

            rides=rides,

            overall=overall,

            lowest_price=lowest_price,

            fastest_ride=fastest_ride,

            highest_rated=highest_rated
        )

    except Exception as e:

        print()
        print("====================================")
        print("COMPARE ERROR:")
        print(e)
        print("====================================")
        print()

        return """
        <script>
            alert(
                "Unable to compare rides. Please check your pickup and destination."
            );
            window.history.back();
        </script>
        """


# =========================================================
# START FLASK
# =========================================================

if __name__ == "__main__":

    print()
    print("====================================")
    print("          RIDE HUB IS RUNNING")
    print("====================================")
    print()
    print(
        "Open: http://127.0.0.1:5000"
    )
    print()

    app.run(
        debug=True
    )