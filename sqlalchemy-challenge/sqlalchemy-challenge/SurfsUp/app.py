# Import the dependencies.
from flask import Flask, jsonify
import numpy as np
import pandas as pd
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
#################################################
# Database Setup
#################################################

engine = create_engine("sqlite:///Resources/hawaii.sqlite")
# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)


#################################################
# Flask Setup
#################################################

app = Flask(__name__)



#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    """List all available API routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end><br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the precipitation data for the last 12 months as JSON."""
    # Calculate the date one year ago from the last data point in the database
    most_recent_date = session.query(func.max(Measurement.date)).first()[0]
    one_year_ago = dt.datetime.strptime(most_recent_date, '%Y-%m-%d') - dt.timedelta(days=365)

    # Query for the last 12 months of precipitation data
    precipitation_data = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= one_year_ago).all()

    # Convert the query results to a dictionary
    precipitation_dict = {date: prcp for date, prcp in precipitation_data}

    return jsonify(precipitation_dict)

@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of stations from the dataset."""
    # Query all stations
    results = session.query(Station.station).all()

    # Convert list of tuples into a normal list
    stations_list = list(np.ravel(results))

    return jsonify(stations_list)

@app.route("/api/v1.0/tobs")
def tobs():
    """Return a JSON list of temperature observations (TOBS) for the previous year."""
    # Find the most active station ID
    most_active_station_id = session.query(Measurement.station).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first()[0]

    # Calculate the date one year ago from the most recent date
    most_recent_date = session.query(func.max(Measurement.date)).filter(Measurement.station == most_active_station_id).first()[0]
    one_year_ago = dt.datetime.strptime(most_recent_date, '%Y-%m-%d') - dt.timedelta(days=365)

    # Query the last 12 months of temperature observation data for the most active station
    temperature_data = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station_id).\
        filter(Measurement.date >= one_year_ago).all()

    # Convert list of tuples into a normal list
    temps_list = list(np.ravel(temperature_data))

    return jsonify(temps_list)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_range(start=None, end=None):
    """Return a JSON list of TMIN, TAVG, and TMAX for a specified start or start-end range."""
    # Query to select min, max, avg temps
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
    
    if not end:
        # When no end date is provided
        results = session.query(*sel).filter(Measurement.date >= start).all()
    else:
        # When both start and end date are provided
        results = session.query(*sel).filter(Measurement.date >= start).filter(Measurement.date <= end).all()
    
    # Convert list of tuples into a normal list
    temps = list(np.ravel(results))

    return jsonify(temps)

if __name__ == '__main__':
    app.run(debug=True)