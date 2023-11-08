import pandas as pd
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn import tree
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from http.server import BaseHTTPRequestHandler, HTTPServer
import argparse
import time
import google.cloud.storage as storage
import google.cloud.pubsub as pubsub

# Sql dependencies
import os
from google.cloud.sql.connector import Connector, IPTypes
import pymysql
import socket, struct
import sqlalchemy


class MySqlServer():
    pool = None
    
    def connect_with_connector(self) -> sqlalchemy.engine.base.Engine:
        """
        Initializes a connection pool for a Cloud SQL instance of MySQL.
        
        Uses the Cloud SQL Python Connector package.
        """
        # Note: Saving credentials in environment variables is convenient, but not
        # secure - consider a more secure solution such as
        # Cloud Secret Manager (https://cloud.google.com/secret-manager) to help
        # keep secrets safe.

        instance_connection_name = os.environ["INSTANCE_CONNECTION_NAME"]  # e.g. 'project:region:instance'
        db_user = os.environ["DB_USER"]  # e.g. 'my-db-user'
        db_pass = os.environ["DB_PASS"]  # e.g. 'my-db-password'
        db_name = os.environ["DB_NAME"]  # e.g. 'my-database'

        ip_type = IPTypes.PRIVATE if os.environ.get("DB_PRIVATE_IP") else IPTypes.PUBLIC

        connector = Connector(ip_type)

        def getconn() -> pymysql.connections.Connection:
            conn: pymysql.connections.Connection = connector.connect(
                instance_connection_name,
                "pymysql",
                user=db_user,
                password=db_pass,
                db=db_name,
            )
            return conn
        
        self.pool = sqlalchemy.create_engine(
            "mysql+pymysql://",
            creator=getconn,
            # ...
        )
        return self.pool

    def retrieve_db(self):
        query_stmt = sqlalchemy.text("SELECT * from accesslogs")
        with self.pool.connect() as db_conn:
            result = db_conn.execute(query_stmt).fetchall()
            return result


# Create database connection
sqlserver= MySqlServer()
sqlserver.pool = sqlserver.connect_with_connector()

# fetch all from db
db = sqlserver.retrieve_db()
X = db[['ip']]
y = db['country']

# split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Build a Linear Regression model
lr_model = LinearRegression()
lr_model.fit(X_train, y_train)

# Build a decision tree model
clf = tree.DecisionTreeClassifier()
clf_model = clf.fit(X_train, y_train)

# Make predictions with both models
lr_predictions = lr_model.predict(X_test)
clf_predictions = clf_model.predict(X_test)

# Evaluate models
mae = mean_absolute_error(y_test, lr_predictions)
mse = mean_squared_error(y_test, lr_predictions)
r2 = r2_score(y_test, lr_predictions)

print("Linear Regression: ")
print(f"Mean Absolute Error (MAE): {mae}")
print(f"Mean Squared Error (MSE): {mse}")
print(f"R-squared (R²) Score: {r2}")
print("\n")

# Evaluate models
mae_2 = mean_absolute_error(y_test, clf_predictions)
mse_2 = mean_squared_error(y_test, clf_predictions)
r2_2 = r2_score(y_test, clf_predictions)

print("Decision Tree: ")
print(f"Mean Absolute Error (MAE): {mae_2}")
print(f"Mean Squared Error (MSE): {mse_2}")
print(f"R-squared (R²) Score: {r2_2}")
print("\n")



