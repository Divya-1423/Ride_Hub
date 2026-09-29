
from flask import Flask, render_template, request, jsonify
import hashlib

app = Flask(__name__)


# ---------------------------------------------------------
# LOCATION / ROUTE BASE DATA
# ---------------------------------------------------------

base_data = {
    "Uber": {
        "Car": {"price": 316, "duration": 23, "rating": 4.6, "reviews": 1500},
        "Bike": {"price": 140, "duration": 20, "rating": 4.6, "reviews": 3500}
    },

    "Rapido": {
        "Car": {"price": 299, "duration": 22, "rating": 4.4, "reviews": 1200},
        "Bike": {"price": 115, "duration": 16, "rating": 4.4, "reviews": 3530}
    },

    "Ola": {
        "Car": {"price": 308, "duration": 24, "rating": 4.5, "reviews": 1400},
        "Bike": {"price": 193, "duration": 19, "rating": 4.3, "reviews": 3600}
    }
}


# ---------------------------------------------------------
# DIFFERENT LOCATIONS GET DIFFERENT PLATFORM ADVANTAGES
# ---------------------------------------------------------

location_rules = {

    "visakhapatnam": {
        "Uber": 1,
        "Rapido": 0,
        "Ola": 0
    },

    "vijayawada": {
        "Uber": 0,
        "Rapido": 2,
        "Ola": 1
    },

    "hyderabad": {
        "Uber": 1,
        "Rapido": 2,
        "Ola": 0
    },

    "bangalore": {
        "Uber": 0,
        "Rapido": 2,
        "Ola": 1
    },

    "bengaluru": {
        "Uber": 0,
        "Rapido": 2,
        "Ola": 1
    },

    "chennai": {
        "Uber": 1,
        "Rapido": 0,
        "Ola": 2
    },

    "tirupati": {
        "Uber": 0,
        "Rapido": 2,
        "Ola": 1
    },

    "guntur": {
        "Uber": 0,
        "Rapido": 2,
        "Ola": 1
    }
}


# ---------------------------------------------------------
# GET LOCATION ADVANTAGE
# ---------------------------------------------------------

def get_location_bonus(source, destination, platform):

    route = f"{source} {destination}".lower()

    # Check whether any known location is present
    for location, rules in location_rules.items():
        if location in route:
            return rules.get(platform, 0)

    # For unknown locations, create a stable result
    # based on source + destination.
    # It will NOT change randomly every refresh.
    key = f"{source.lower()}-{destination.lower()}"

    number = int(hashlib.md5(key.encode()).hexdigest(), 16)

    platform_order = ["Uber", "Rapido", "Ola"]

    selected = platform_order[number % 3]

    if platform == selected:
        return 2

    return 0


# ---------------------------------------------------------
# CALCULATE SCORE
# ---------------------------------------------------------

def calculate_score(data, location_bonus):

    price_score = max(0, 100 - (data["price"] / 5))

    duration_score = max(0, 100 - (data["duration"] * 2))

    rating_score = data["rating"] * 20

    review_score = min(100, data["reviews"] / 40)

    # Location has an effect, but price/time/rating still matter
    final_score = (
        price_score * 0.30
        + duration_score * 0.25
        + rating_score * 0.25
        + review_score * 0.10
        + location_bonus * 5
    )

    return round(final_score, 2)


# ---------------------------------------------------------
# HOME PAGE
# ---------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------------------------------------------------
# COMPARISON API
# ---------------------------------------------------------

@app.route("/compare", methods=["POST"])
@app.route("/api/compare", methods=["POST"])
def compare():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "No data received"
        }), 400

    source = data.get("source", "").strip()
    destination = data.get("destination", "").strip()
    vehicle = data.get("vehicleType", data.get("vehicle", "Car"))

    if not source or not destination:
        return jsonify({
            "error": "Please enter source and destination"
        }), 400

    if vehicle not in ["Car", "Bike"]:
        vehicle = "Car"

    results = []

    # -----------------------------------------------------
    # CREATE RESULT FOR EACH PLATFORM
    # -----------------------------------------------------

    for platform in ["Uber", "Rapido", "Ola"]:

        original = base_data[platform][vehicle].copy()

        location_bonus = get_location_bonus(
            source,
            destination,
            platform
        )

        score = calculate_score(
            original,
            location_bonus
        )

        result = {
            "platform": platform,
            "price": original["price"],
            "duration": original["duration"],
            "rating": original["rating"],
            "reviews": original["reviews"],
            "score": score
        }

        results.append(result)

    # -----------------------------------------------------
    # FIND BEST OVERALL PLATFORM
    # -----------------------------------------------------

    best = max(
        results,
        key=lambda x: x["score"]
    )

    cheapest = min(
        results,
        key=lambda x: x["price"]
    )

    fastest = min(
        results,
        key=lambda x: x["duration"]
    )

    highest_rated = max(
        results,
        key=lambda x: x["rating"]
    )

    # -----------------------------------------------------
    # OVERALL SUGGESTION
    # -----------------------------------------------------

    suggestion = {
        "platform": best["platform"],
        "reason": (
            f"{best['platform']} has the highest overall ride score "
            f"for this location based on price, duration, rating, "
            f"reviews and location."
        ),
        "cheapest": (
            f"{cheapest['platform']} {vehicle} at ₹{cheapest['price']}"
        ),
        "fastest": (
            f"{fastest['platform']} {vehicle} in "
            f"{fastest['duration']} minutes"
        ),
        "highestRated": (
            f"{highest_rated['platform']} {vehicle} with "
            f"⭐ {highest_rated['rating']}"
        )
    }

    return jsonify({
        "source": source,
        "destination": destination,
        "vehicle": vehicle,
        "results": results,
        "overallSuggestion": suggestion
    })


# ---------------------------------------------------------
# RUN SERVER
# ---------------------------------------------------------

if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )