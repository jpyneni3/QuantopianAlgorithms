#Use the previous 10 bars' movements to predict the next movement.

# Use a random forest classifier. More here: http://scikit-learn.org/stable/user_guide.html
from sklearn.ensemble import RandomForestClassifier
from collections import deque
import numpy as np

def initialize(context):
    context.security = sid(698) # Boeing
    context.window_length = 10 # Amount of prior bars to study

    context.classifier = RandomForestClassifier() # Use a random forest classifier

    # deques are lists with a maximum length where old entries are shifted out
    context.recent_prices = deque(maxlen=context.window_length+2) # Stores recent prices
    context.X = deque(maxlen=500) # Independent, or input variables
    context.Y = deque(maxlen=500) # Dependent, or output variable

    context.prediction = 0 # Stores most recent prediction

    schedule_function(rebalance, date_rules.every_day(), time_rules.market_close(minutes=5))
    schedule_function(record_vars, date_rules.every_day(), time_rules.market_close())

def rebalance(context, data):
    context.recent_prices.append(data.current(context.security, 'price')) # Update the recent prices
    if len(context.recent_prices) == context.window_length+2: # If there's enough recent price data

        # Make a list of 1's and 0's, 1 when the price increased from the prior bar
        changes = np.diff(context.recent_prices) > 0

        context.X.append(changes[:-1]) # Add independent variables, the prior changes
        context.Y.append(changes[-1]) # Add dependent variable, the final change

        if len(context.Y) >= 100: # There needs to be enough data points to make a good model

            context.classifier.fit(context.X, context.Y) # Generate the model

            context.prediction = context.classifier.predict(changes[1:]) # Predict

            # If prediction = 1, buy all shares affordable, if 0 sell all shares
            order_target_percent(context.security, context.prediction)

def record_vars(context, data):
    record(prediction=int(context.prediction))
