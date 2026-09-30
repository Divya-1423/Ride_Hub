
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

HEADERS = {
    "User-Agent": "RideHub-College-Project/1.0"
}

PHOTON_URL = "https://photon.komoot.io/api"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"


@app.route("/")
def home():
    return render_template("index.html")


# --------------------------------------------------
# LOCATION SEARCH
# --------------------------------------------------

@app.route("/search_location")
def search_location():

    q = request.args.get("q", "").strip()

    if len(q) < 3:
        return jsonify([])

    try:

        response = requests.get(
            PHOTON_URL,
            params={
                "q": q,
                "limit": 6,
                "lang": "en"
            },
            headers=HEADERS,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        results = []

        for feature in data.get("features", []):

            coordinates = feature.get(
                "geometry", {}
            ).get("coordinates", [])

            if len(coordinates) != 2:
                continue

            p = feature.get(
                "properties", {}
            )

            parts = []

            for value in [
                p.get("name"),
                p.get("street"),
                p.get("district"),
                p.get("city"),
                p.get("state"),
                p.get("country")
            ]:

                if value and value not in parts:
                    parts.append(value)

            name = ", ".join(parts)

            if not name:
                continue

            results.append({
                "name": name,
                "lat": coordinates[1],
                "lng": coordinates[0]
            })

        return jsonify(results)

    except Exception:
        return jsonify([])


# --------------------------------------------------
# EXACT CURRENT GPS LOCATION -> PLACE NAME
# --------------------------------------------------

@app.route("/reverse_location")
def reverse_location():

    lat = request.args.get("lat")
    lng = request.args.get("lng")

    if not lat or not lng:
        return jsonify({
            "error": "Coordinates missing"
        }), 400

    try:

        response = requests.get(
            f"{PHOTON_URL}/reverse",
            params={
                "lat": lat,
                "lon": lng,
                "lang": "en"
            },
            headers=HEADERS,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        features = data.get("features", [])

        if not features:

            return jsonify({
                "name": "Current Location",
                "lat": float(lat),
                "lng": float(lng)
            })

        p = features[0].get(
            "properties", {}
        )

        parts = []

        for value in [
            p.get("name"),
            p.get("street"),
            p.get("district"),
            p.get("city"),
            p.get("state")
        ]:

            if value and value not in parts:
                parts.append(value)

        address = ", ".join(parts)

        if not address:
            address = "Current Location"

        return jsonify({
            "name": address,
            "lat": float(lat),
            "lng": float(lng)
        })

    except Exception:

        return jsonify({
            "name": "Current Location",
            "lat": float(lat),
            "lng": float(lng)
        })


# --------------------------------------------------
# ROAD DISTANCE + TIME
# --------------------------------------------------

def get_route(
    source_lat,
    source_lng,
    destination_lat,
    destination_lng
):

    coordinates = (
        f"{source_lng},{source_lat};"
        f"{destination_lng},{destination_lat}"
    )

    response = requests.get(
        f"{OSRM_URL}/{coordinates}",
        params={
            "overview": "false"
        },
        headers=HEADERS,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    if data.get("code") != "Ok":
        raise Exception("Route not found.")

    route = data["routes"][0]

    distance = round(
        route["distance"] / 1000,
        1
    )

    minutes = max(
        1,
        round(route["duration"] / 60)
    )

    return distance, minutes


# --------------------------------------------------
# FARE
# --------------------------------------------------

def calculate_fare(
    company,
    vehicle,
    distance,
    minutes
):

    rates = {

        "Rapido": {
            "Bike": (25, 8.0, 0.35),
            "Auto": (35, 11.0, 0.65),
            "Car":  (60, 14.0, 0.90)
        },

        "Uber": {
            "Bike": (30, 8.5, 0.40),
            "Auto": (40, 11.5, 0.70),
            "Car":  (70, 15.0, 1.00)
        },

        "Ola": {
            "Bike": (28, 8.2, 0.38),
            "Auto": (38, 11.2, 0.68),
            "Car":  (65, 14.5, 0.95)
        }
    }

    base, per_km, per_min = rates[company][vehicle]

    fare = (
        base
        + distance * per_km
        + minutes * per_min
    )

    minimum = {
        "Bike": 35,
        "Auto": 50,
        "Car": 80
    }

    return max(
        minimum[vehicle],
        round(fare)
    )


# --------------------------------------------------
# RIDE TIME
# --------------------------------------------------

def ride_time(base_time, vehicle):

    factors = {
        "Bike": 0.92,
        "Auto": 1.00,
        "Car": 0.96
    }

    return max(
        1,
        round(base_time * factors[vehicle])
    )


# --------------------------------------------------
# RATINGS
# --------------------------------------------------

def rating(company, vehicle):

    ratings = {

        "Rapido": {
            "Bike": 4.5,
            "Auto": 4.3,
            "Car": 4.2
        },

        "Uber": {
            "Bike": 4.4,
            "Auto": 4.5,
            "Car": 4.4
        },

        "Ola": {
            "Bike": 4.3,
            "Auto": 4.4,
            "Car": 4.3
        }
    }

    return ratings[company][vehicle]


def review(value):

    if value >= 4.5:
        return "Very Good"

    if value >= 4.3:
        return "Good"

    return "Average"


# --------------------------------------------------
# CREATE RIDES
# --------------------------------------------------

def create_rides(distance, base_time):

    rides = []

    for company in [
        "Rapido",
        "Uber",
        "Ola"
    ]:

        for vehicle in [
            "Bike",
            "Auto",
            "Car"
        ]:

            time = ride_time(
                base_time,
                vehicle
            )

            r = rating(
                company,
                vehicle
            )

            rides.append({

                "Company": company,
                "Vehicle": vehicle,
                "Price": calculate_fare(
                    company,
                    vehicle,
                    distance,
                    time
                ),
                "Distance": distance,
                "Time": time,
                "Rating": r,
                "Review": review(r),
                "Overall Score": 0
            })

    return rides


# --------------------------------------------------
# OVERALL BEST
# Equal importance:
# Price 33.33%
# Time 33.33%
# Rating 33.34%
# --------------------------------------------------

def calculate_overall(rides):

    prices = [r["Price"] for r in rides]
    times = [r["Time"] for r in rides]
    ratings = [r["Rating"] for r in rides]

    min_price = min(prices)
    max_price = max(prices)

    min_time = min(times)
    max_time = max(times)

    min_rating = min(ratings)
    max_rating = max(ratings)

    for r in rides:

        if max_price == min_price:
            price_score = 100
        else:
            price_score = (
                (max_price - r["Price"])
                / (max_price - min_price)
            ) * 100

        if max_time == min_time:
            time_score = 100
        else:
            time_score = (
                (max_time - r["Time"])
                / (max_time - min_time)
            ) * 100

        if max_rating == min_rating:
            rating_score = 100
        else:
            rating_score = (
                (r["Rating"] - min_rating)
                / (max_rating - min_rating)
            ) * 100

        r["Overall Score"] = round(
            price_score * 0.3333
            + time_score * 0.3333
            + rating_score * 0.3334,
            2
        )

    return max(
        rides,
        key=lambda r: r["Overall Score"]
    )


# --------------------------------------------------
# COMPARE
# --------------------------------------------------

@app.route(
    "/compare",
    methods=["POST"]
)
def compare():

    try:

        source = request.form.get(
            "source",
            ""
        ).strip()

        destination = request.form.get(
            "destination",
            ""
        ).strip()

        vehicle = request.form.get(
            "vehicle",
            "All"
        )

        source_lat = request.form.get(
            "source_lat"
        )

        source_lng = request.form.get(
            "source_lng"
        )

        destination_lat = request.form.get(
            "destination_lat"
        )

        destination_lng = request.form.get(
            "destination_lng"
        )


        if not source_lat or not source_lng:
            raise Exception(
                "Please select a pickup location or use Current Location."
            )

        if not destination_lat or not destination_lng:
            raise Exception(
                "Please select the destination from the suggestions."
            )


        distance, base_time = get_route(

            float(source_lat),
            float(source_lng),

            float(destination_lat),
            float(destination_lng)
        )


        rides = create_rides(
            distance,
            base_time
        )


        if vehicle != "All":

            rides = [
                r for r in rides
                if r["Vehicle"] == vehicle
            ]


        best = calculate_overall(rides)

        lowest = min(
            rides,
            key=lambda r: r["Price"]
        )

        fastest = min(
            rides,
            key=lambda r: r["Time"]
        )

        highest = max(
            rides,
            key=lambda r: r["Rating"]
        )


        return render_template(
            "result.html",
            results=rides,
            best_overall=best,
            lowest_price=lowest,
            fastest=fastest,
            highest_rated=highest,
            source=source,
            destination=destination,
            distance=distance,
            base_minutes=base_time,
            selected_vehicle=vehicle,
            error=None
        )


    except Exception as e:

        return render_template(
            "result.html",
            results=[],
            best_overall=None,
            lowest_price=None,
            fastest=None,
            highest_rated=None,
            source=request.form.get(
                "source",
                ""
            ),
            destination=request.form.get(
                "destination",
                ""
            ),
            distance=None,
            base_minutes=None,
            selected_vehicle="All",
            error=str(e)
        )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )