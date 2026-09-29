import pandas as pd

def compare_rides(data):

    cheapest = data.loc[data["Fare"].idxmin()]

    fastest = data.loc[data["Trip Duration"].idxmin()]

    highest_rated = data.loc[data["Rating"].idxmax()]

    best_overall = data.loc[data["Ride Score"].idxmax()]

    return cheapest, fastest, highest_rated, best_overall