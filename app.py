"""
strompris fastapi app entrypoint
"""
from __future__ import annotations

import datetime
import os
from typing import List, Optional

import altair as alt
from fastapi import FastAPI, Query, Request
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from strompris import (
    ACTIVITIES,
    LOCATION_CODES,
    fetch_day_prices,
    fetch_prices,
    plot_activity_prices,
    plot_daily_prices,
    plot_prices,
)

from pathlib import Path
base_dir = Path(__file__).resolve().parent

app = FastAPI()
templates = Jinja2Templates(directory=Path(base_dir, 'templates'))


# `GET /` should render the `strompris.html` template
# with inputs:
# - request
# - location_codes: location code dict
# - today: current date

@app.get("/")
def strompris_html(
    request: Request,
    location_codes: dict = LOCATION_CODES,
    today: datetime.date = datetime.date.today()
    ):
    """
    Renders the `strompris.html` template with the provided context.

    Args:
        request (Request): The incoming request object.
        location_codes (dict): A dictionary of location codes and names.
        today (datetime.date): The current date.

    Returns:
        templates.TemplateResponse: The rendered HTML template response.
    """

    return templates.TemplateResponse(
        "strompris.html",
        context={
            "request": request,
            "location_codes": location_codes,
            "today": today,
            "data_source": "https://www.nds.no/dataportalen/dataset/strompriser-last-hour",
        },
    )


# GET /plot_prices.json should take inputs:
# - locations (list from Query)
# - end (date)
# - days (int, default=7)
# all inputs should be optional
# return should be a vega-lite JSON chart (alt.Chart.to_dict())
# produced by `plot_prices`
# (task 5.6: return chart stacked with plot_daily_prices)

@app.get("/plot_prices.json")
def plot_prices_json(
    locations: Optional[List[str]] = Query(default=None),
    end: Optional[datetime.date] = None,
    days: Optional[int] = 7,
):
    """
    Generates and returns a JSON chart of electricity prices.

    Args:
        locations (Optional[List[str]]): A list of location codes to fetch data for.
            Defaults to None, indicating all locations.
        end (Optional[datetime.date]): The end date of the time period.
            Defaults to None.
        days (Optional[int]): The number of days of data to fetch, up to and
            including the end date. Defaults to 7 days.

    Returns:
        JSON chart: A JSON chart of electricity prices.
    """
    # If end is empty:
    if end is None:
        end = datetime.date.today()

    # If locations is empty and not a tuple:
    if locations is None:
        if locations != tuple:
            locations = LOCATION_CODES.keys()

    # Fetch and plot daily prices for the specified period and locations
    prices_df = fetch_prices(end_date=end, days=days, locations=tuple(locations))
    chart = plot_prices(prices_df).to_dict()
    return chart

# Task 5.6 (bonus):
# `GET /activity` should render the `activity.html` template
# activity.html template must be adapted from `strompris.html`
# with inputs:
# - request
# - location_codes: location code dict
# - activities: activity energy dict
# - today: current date

@app.get("/activity")
def activity(request: Request, date: datetime.date = datetime.date.today()):
    """
    Renders the `activity.html` template with the provided context.

    Args:
        request (Request): The incoming request object.
        date (datetime.date, optional): The date for which to fetch activity energy costs.
            Defaults to today's date.

    Returns:
        templates.TemplateResponse: The rendered HTML template response.
    """
    # Fetch location codes and activity energy costs
    location_codes = LOCATION_CODES
    activities = ACTIVITIES

    return templates.TemplateResponse(
        "activity.html",
        context={
            "request": request,
            "location_codes": location_codes,
            "activities": activities,
            "date": date,
        },
    )

# Task 5.6:
# `GET /plot_activity.json` should return vega-lite chart JSON (alt.Chart.to_dict())
# from `plot_activity_prices`
# with inputs:
# - location (single, default=NO1)
# - activity (str, default=shower)
# - minutes (int, default=10)
@app.get("/plot_activity.json")
def plot_activity_json(
    activity: str,
    minutes: int,
    location: str = "NO1",
):
    """
    Generates and returns a JSON chart of the estimated cost of an activity based on electricity prices.

    Args:
        activity (str): The name of the activity to calculate the cost for.
        minutes (int): The duration of the activity in minutes.
        location (str): The location for which to fetch electricity prices. Defaults to "NO1" (Oslo).

    Returns:
        JSON chart: A JSON chart showing the estimated cost of the activity.
    """
    # Fetch prices for the current day
    today = datetime.date.today()
    prices_df = fetch_day_prices(date=today, location=location)

    # Calculate the activity price and create the chart
    activity_price = plot_activity_prices(prices_df, activity, minutes)

    return activity_price.to_dict()



# mount your docs directory as static files at `/help`

# Get static files from Sphinx from 'docs' directory
app.mount(
    "/docs",
    StaticFiles(directory="docs", html=True),
    name="docs"
)
@app.get("/help")
def help(request: Request):
    return templates.TemplateResponse(
        "help.html",
        {
            "request": request
        }
    )

if __name__ == "__main__":
    # use uvicorn to launch your application on port 5000
    import uvicorn
    uvicorn.run(app, host='localhost', port=5000)