import pandas as pd
from joblib import dump
import sqlalchemy
from google.cloud.sql.connector import Connector

# GETTING THE DATA

import sqlalchemy
from google.cloud.sql.connector import Connector
import pandas as pd

# info about mysql instance
project_id = 'cloudcomputing-398719'
region = 'us-central1'
instance_name = "ayang903"

# initialize db parameters
INSTANCE_CONNECTION_NAME = f"{project_id}:{region}:{instance_name}" # i.e demo-project:us-central1:demo-instance
print(f"Your instance connection name is: {INSTANCE_CONNECTION_NAME}")
DB_USER = "andy"
DB_PASS = "yang"
DB_NAME = "hw5_requests"

# initialize Connector object
connector = Connector()

# function to return the database connection object
def getconn():
    conn = connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pymysql",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME
    )
    return conn

# create connection pool with 'creator' argument to our connection object function
pool = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=getconn,
)

query = "SELECT * FROM successful_requests"
df = pd.read_sql_query(query, pool)
csv_file_path = "data.csv"
df.to_csv(csv_file_path, index=False)
print(f"Data exported to {csv_file_path} and loaded in as df")
print(f"--------------")

#PREDICTING COUNTRY FROM IP

# preprocess IP column
new_columns = df['Client_IP'].str.split('.', expand=True)
df[['client_ip_part1', 'client_ip_part2', 'client_ip_part3', 'client_ip_part4']] = new_columns
df['client_ip_part1'] = df['client_ip_part1'].astype(int)
df['client_ip_part2'] = df['client_ip_part2'].astype(int)
df['client_ip_part3'] = df['client_ip_part3'].astype(int)
df['client_ip_part4'] = df['client_ip_part4'].astype(int)

from sklearn.model_selection import train_test_split
X = df[['client_ip_part1', 'client_ip_part2', 'client_ip_part3', 'client_ip_part4']]
y = df['Country_Name']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)


# KNN
print(f"Training KNN model to predict country from IP...")
from sklearn.neighbors import KNeighborsClassifier
knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(X_train, y_train)

preds = knn.predict(X_test)

from sklearn.metrics import accuracy_score
print("Accuracy of predictions vs y_test: " + str(round(accuracy_score(preds, y_test), 2)))

dump(knn, "knn_country.joblib")
print(f"exported model as knn_country.joblib")

print(f"--------------")
print(f"Training Random Forest to predict country from IP...")

from sklearn.ensemble import RandomForestClassifier

rf = RandomForestClassifier()
rf.fit(X_train, y_train)
preds = rf.predict(X_test)
print("Accuracy of predictions vs y_test: " + str(round(accuracy_score(preds, y_test), 2)))

dump(rf, "rf_country.joblib")
print(f"exported model as rf_country.joblib")
print(f"--------------")
# PREDICTING INCOME, gridsearch a KNN
print(f"Training KNN model to predict income from IP, age, gender ...")
# ordinal encoding for ordered categorical vars, income, age, 
from sklearn.preprocessing import OrdinalEncoder
ordinal_encoder = OrdinalEncoder(categories=[['0-10k', '10k-20k', '20k-40k', '40k-60k', '60k-100k', '100k-150k' ,'150k-250k' ,'250k+']])
df['Income_encoded'] = ordinal_encoder.fit_transform(df[['Income']])

ordinal_encoder = OrdinalEncoder(categories=[['0-16', '17-25', '26-35', '36-45', '46-55', '56-65' ,'66-75' ,'76+']])
df['Age_encoded'] = ordinal_encoder.fit_transform(df[['Age']])

from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()
df['Gender_encoded'] = le.fit_transform(df['Gender'])

X = df[['client_ip_part1', 'client_ip_part2', 'client_ip_part3', 'client_ip_part4', 'Age_encoded', 'Gender_encoded']]
y = df['Income_encoded']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)

print("Using GridSearchCV to find best hyperparameters...")
from sklearn.model_selection import GridSearchCV

knn_params = {
    'n_neighbors': [3, 5, 7, 9, 11],
    'weights': ['uniform', 'distance'],
    'metric': ['euclidean', 'manhattan']
}


knn = KNeighborsClassifier()
grid_search_knn = GridSearchCV(estimator=knn, param_grid=knn_params, cv=5, verbose=1, scoring='accuracy')
grid_search_knn.fit(X_train, y_train)


print("Best parameters for KNN:", grid_search_knn.best_params_)
print("Best score for KNN:", round(grid_search_knn.best_score_, 2))
dump(knn, "knn_income.joblib")
print(f"exported model as knn_income.joblib")
print(f"--------------")

print(f"Training Decision Tree to predict income from IP, age, gender ...")
from sklearn.tree import DecisionTreeClassifier
dt = DecisionTreeClassifier()
dt.fit(X_train, y_train)
preds = dt.predict(X_test)
print("Accuracy of predictions vs y_test: " + str(round(accuracy_score(preds, y_test), 2)))
dump(dt, "dt_income.joblib")
print(f"exported model as dt_income.joblib")