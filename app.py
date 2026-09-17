from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

df = pd.read_excel("Ride_Hub_Dataset.xlsx")

# Clean columns
df["App"] = df["App"].astype(str).str.strip().str.lower()
df["Review"] = df["Review"].astype(str).str.lower()

df["Price (₹)"] = pd.to_numeric(df["Price (₹)"], errors="coerce")
df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/compare", methods=["POST"])
def compare():

    source = request.form["source"]
    destination = request.form["destination"]
    vehicle = request.form["vehicle"].strip().lower()

    # Identify vehicle type from Review
    if vehicle == "bike":
        vehicle_data = df[df["Review"].str.contains("bike", na=False)]
    elif vehicle == "auto":
        vehicle_data = df[df["Review"].str.contains("auto", na=False)]
    elif vehicle == "car":
        vehicle_data = df[df["Review"].str.contains("car", na=False)]
    else:
        vehicle_data = df

    # Separate companies
    rapido = vehicle_data[vehicle_data["App"] == "rapido"]
    uber = vehicle_data[vehicle_data["App"] == "uber"]
    ola = vehicle_data[vehicle_data["App"] == "ola"]

    # Prices
    rapido_price = rapido["Price (₹)"].mean()
    uber_price = uber["Price (₹)"].mean()
    ola_price = ola["Price (₹)"].mean()

    # Ratings
    rapido_rating = rapido["Rating"].mean()
    uber_rating = uber["Rating"].mean()
    ola_rating = ola["Rating"].mean()

    # Find lowest price
    prices = {
        "Rapido": rapido_price,
        "Uber": uber_price,
        "Ola": ola_price
    }

    valid_prices = {
        name: price
        for name, price in prices.items()
        if pd.notna(price)
    }

    if valid_prices:
        best_ride = min(valid_prices, key=valid_prices.get)
    else:
        best_ride = "No ride data available"

    return render_template(
        "result.html",
        source=source,
        destination=destination,
        vehicle=vehicle.title(),

        rapido_price=round(rapido_price, 2) if pd.notna(rapido_price) else "N/A",
        uber_price=round(uber_price, 2) if pd.notna(uber_price) else "N/A",
        ola_price=round(ola_price, 2) if pd.notna(ola_price) else "N/A",

        rapido_rating=round(rapido_rating, 2) if pd.notna(rapido_rating) else "N/A",
        uber_rating=round(uber_rating, 2) if pd.notna(uber_rating) else "N/A",
        ola_rating=round(ola_rating, 2) if pd.notna(ola_rating) else "N/A",

        best_ride=best_ride
    )


if __name__ == "__main__":
    app.run(debug=True)