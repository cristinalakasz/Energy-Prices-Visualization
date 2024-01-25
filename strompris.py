#!/usr/bin/env python3
"""
Fetch data from https://www.hvakosterstrommen.no/strompris-api
and visualize it.

Assignment 5
"""
from __future__ import annotations

import datetime
import warnings

import altair as alt
import pandas as pd
import requests
import requests_cache

# install an HTTP request cache
# to avoid unnecessary repeat requests for the same data
# this will create the file http_cache.sqlite
requests_cache.install_cache()

# suppress a warning with altair 4 and latest pandas
warnings.filterwarnings("ignore", ".*convert_dtype.*", FutureWarning)


# task 5.1:


def fetch_day_prices(date: datetime.date = None, location: str = "NO1") -> pd.DataFrame:
    """Fetch one day of data for one location from hvakosterstrommen.no API

    Args:
        date (datetime.date): The date for which to fetch prices.
            Defaults to the current date.
        location (str): The location for which to fetch prices.
            Defaults to "NO1" (Oslo).

    Returns:
        df (DataFrame): A DataFrame containing the electricity prices
            for the specified date and location.
    """

    # Check date
    if date is None:
        date = datetime.date.today()

    # Check if date is on or after 1st October 2023
    # If not raise AssertionError and ValueError
    invalid_date = datetime.date(2023,10,1)

    assert (date >= invalid_date)
    if not (date >= invalid_date):
        raise ValueError("Date is before 1st October 2023")


    # Format date and location for URL
    year = date.year
    month = date.month
    day = date.day

    formatted_date = f"{year:04d}/{month:02d}-{day:02d}_{location}"
    url = 'https://www.hvakosterstrommen.no/api/v1/prices/'
    url_ = f"{url}/{formatted_date}.json"

    # Fetch data from API
    response = requests.get(url_).text

    # Convert data to DataFrame and handle Daylight Savings Time
    df = pd.DataFrame(eval(response))[['NOK_per_kWh', 'time_start']]
    df['time_start'] = pd.to_datetime(df['time_start'], utc=True).dt.tz_convert("Europe/Oslo")

    return df

# LOCATION_CODES maps codes ("NO1") to names ("Oslo")
LOCATION_CODES = {
    "NO1": "Oslo",
    "NO2": "Kristiansand",
    "NO3": "Trondheim",
    "NO4": "Tromsø",
    "NO5": "Bergen",
}

# task 1:


def fetch_prices(
    end_date: datetime.date = None,
    days: int = 7,
    locations: list[str] = tuple(LOCATION_CODES.keys()),
) -> pd.DataFrame:
    """Fetch prices for multiple days and locations into a single DataFrame

    Args:
        end_date (datetime.date): The end date of the time period.
            If not specified, defaults to today's date.
        days (int): The number of days of data to fetch, up to and
            including the end date. Defaults to 7 days.
        locations (list[str]): A list of location codes (NO1, NO2, etc.)
            for which to fetch data. Defaults to all locations.

    Returns:
        df (DataFrame): A DataFrame containing the electricity prices
            for the specified time period and locations.
    """

    # Initialize an empty DataFrame
    df = pd.DataFrame()

    if end_date is None:
        end_date = datetime.date.today()

    # Iterate through each location
    for location_code in locations:

        # Iterate through the days in the time period
        for day in range(days):
            # Calculate the date for the current day
            current_date = end_date - datetime.timedelta(days=day)

            # Fetch prices for the current date and location
            daily_prices_df = fetch_day_prices(date=current_date, location=location_code)

            # Add columns for location code and location name
            daily_prices_df["location_code"] = location_code
            daily_prices_df["location"] = LOCATION_CODES[location_code]

            # Append the daily prices to the location DataFrame
            df = pd.concat([df, daily_prices_df])

    return df

# task 5.1:


def plot_prices(df: pd.DataFrame) -> alt.Chart:
    """
    Plots electricity prices over time for each location.
    
    x-axis represents the time_start
    y-axis represents the price in NOK
    each location has its own line

    Args:
        df (DataFrame): The DataFrame containing the electricity prices data.

    Returns:
        chart (Altair.Chart): The chart representing the line plot of the data.
    """
    
    # Define the chart
    chart = alt.Chart(df).mark_line().encode(
        x="time_start:T",
        y="NOK_per_kWh",
        color="location",
        tooltip=["time_start", "location", "NOK_per_kWh"],
    )
    
    return chart


# Task 5.4


def plot_daily_prices(df: pd.DataFrame) -> alt.Chart:
    """Plot the daily average price

    x-axis should be time_start (day resolution)
    y-axis should be price in NOK

    You may use any mark.

    Make sure to document arguments and return value...
    """
    raise NotImplementedError("Remove me when you implement this task (in4110 only)")
    ...


# Task 5.6

ACTIVITIES = {
    # activity name: energy cost in kW
    "shower": {"energy_usage": 30},
    "baking": {"energy_usage": 2.5},
    "heat": {"energy_usage": 1},
}

def plot_activity_prices(
    df: pd.DataFrame,
    activity: str = "shower",
    minutes: float = 10,
) -> alt.Chart:
    """
    Plot price for one activity by name,
    given a data frame of prices, and its duration in minutes.
    
    Args:
        df (DataFrame): A DataFrame containing electricity prices.
        activity (str, optional): The name of the activity to plot the price for.
            Defaults to "shower".
        minutes (float): The duration of the activity in minutes.
            Defaults to 10 minutes.

    Returns:
        alt.Chart: An Altair chart showing the price for the specified activity.
    """

    # Calculate the activity price based on the activity duration and the energy usage
    df['activity_price'] = (
        ACTIVITIES[activity]["energy_usage"] / 60 * minutes * df["NOK_per_kWh"]
    )

    # Create a line chart for the activity price
    activity_chart = alt.Chart(df)
    activity_chart = activity_chart.mark_line().encode(
        x="time_start",
        y='activity_price',
        tooltip=["time_start", 'activity_price'],
    )

    return activity_chart



def main():
    """Allow running this module as a script for testing."""
    # Fetch electricity prices data
    df = fetch_prices()
    # Create the line chart
    chart = plot_prices(df)
    # showing the chart without requiring jupyter notebook or vs code for example
    # requires altair viewer: `pip install altair_viewer`
    # Display the chart
    chart.show()


if __name__ == "__main__":
    main()
