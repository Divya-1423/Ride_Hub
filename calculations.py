
import pandas as pd

data = pd.read_csv("data_new.csv")
print(data)

cheapest = data.loc[data["Fare"].idxmin()]

print("\nCheapest Ride:")
print(cheapest)

fastest = data.loc[data["Trip Duration"].idxmin()]

print("\nFastest Ride:")
print(fastest)

#PART 7 - Find highest-rated ride
print(data.columns)
highest_rated = data.loc[data["Rating"].idxmax()]
print("\nHighest Rated Ride:")
print(highest_rated)

# PART 8 - Calculate Ride Score

data["Fare Score"] = (data["Fare"].max() - data["Fare"]) / (
    data["Fare"].max() - data["Fare"].min()
) * 100

data["Time Score"] = (data["Trip Duration"].max() - data["Trip Duration"]) / (
    data["Trip Duration"].max() - data["Trip Duration"].min()
) * 100

data["Rating Score"] = (data["Rating"] / 5) * 100

data["Ride Score"] = (
    data["Fare Score"] * 0.40
    + data["Time Score"] * 0.30
    + data["Rating Score"] * 0.20
)

print("\nRide Scores:")
print(data[["Ride", "Ride Score"]])

# PART 9 - Find the Best Overall Ride

best_ride = data.loc[data["Ride Score"].idxmax()]

print("\n🏆 Best Overall Ride:")
print(best_ride)

# PART 10 - Save the calculated results

data.to_csv("ride_results.csv", index=False)

print("\nResults saved successfully!")

# ==============================
# OVERALL PLATFORM COMPARISON
# ==============================

print("\n==============================")
print("OVERALL PLATFORM COMPARISON")
print("==============================")

# Change these column names only if your CSV uses different names
platform_col = "Platform"
price_col = "Price"
rating_col = "Rating"
duration_col = "Trip Duration"

# Calculate average values for each platform
comparison = data.groupby(platform_col).agg({
    price_col: "mean",
    rating_col: "mean",
    duration_col: "mean"
}).reset_index()

# Rename columns
comparison.columns = [
    "Platform",
    "Average Price",
    "Average Rating",
    "Average Duration"
]

# Normalize each metric
comparison["Price Score"] = (
    1 - (comparison["Average Price"] - comparison["Average Price"].min()) /
    (comparison["Average Price"].max() - comparison["Average Price"].min())
) * 100

comparison["Rating Score"] = (
    (comparison["Average Rating"] - comparison["Average Rating"].min()) /
    (comparison["Average Rating"].max() - comparison["Average Rating"].min())
) * 100

comparison["Duration Score"] = (
    1 - (comparison["Average Duration"] - comparison["Average Duration"].min()) /
    (comparison["Average Duration"].max() - comparison["Average Duration"].min())
) * 100

# Overall score
comparison["Overall Score"] = (
    comparison["Price Score"] * 0.40 +
    comparison["Rating Score"] * 0.30 +
    comparison["Duration Score"] * 0.30
)

# Display comparison
print(comparison[
    [
        "Platform",
        "Average Price",
        "Average Rating",
        "Average Duration",
        "Overall Score"
    ]
].round(2).to_string(index=False))

# Find best overall platform
best_platform = comparison.loc[
    comparison["Overall Score"].idxmax(),
    "Platform"
]

print("\n🏆 BEST OVERALL PLATFORM:", best_platform)
print("This result is based on price, rating, and trip duration.")




















































