'''
This script contains functions for integrating internet of things in the form of firebase into our system.
To summarise, the functions set up, update, reset, randomise values, consolidate and plot statistics.
They do this by manipulating the data streams to and from the authenticated firebase instance.
The functions will be imported from this script to perform iot tasks within the SmartBinApp.py main script.
'''

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from matplotlib import pyplot as plt


def firebase_setup():
    """
    Required imports and authentication using json service key. 
    Instantiate firebase object for future manipulation.
    """
    import firebase_admin
    from firebase_admin import credentials
    from firebase_admin import db

    cred = credentials.Certificate(
        '/home/pi/SmartBin/data/guiwithkivy-48023-firebase-adminsdk-i41qf-c08ecb8507.json')
    firebase_admin.initialize_app(
        cred, {'databaseURL': 'https://guiwithkivy-48023.firebaseio.com/', })
    firebase = db.reference('/')
    return firebase


def firebase_reset(firebase):
    """
    Reset all users and their recycling category counts to 0. 
    Returns a dictionary of the data in the updated firebase.
    Dictionary will look like this:
    {
    'frank': {'bottles': 0, 'cans': 0, 'others': 0},
    'grace': {'bottles': 0, 'cans': 0, 'others': 0},
    'ken': {'bottles': 0, 'cans': 0, 'others': 0},
    'shelly': {'bottles': 0, 'cans': 0, 'others': 0},
    'tim': {'bottles': 0, 'cans': 0, 'others': 0}
    }
    """
    users = ['ken', 'tim', 'grace', 'shelly', 'frank']
    categories = ['bottles', 'cans', 'others']

    for user in users:
        for category in categories:
            firebase.child(user).child(category).set(0)

    return firebase.get()


def firebase_update(firebase, user, category, increment):
    """
    Updates the specified user's recycling count in the specified category by the specified amount. 
    Returns a dictionary of the data in the updated firebase.
    """
    current = firebase.child(user).child(category).get()
    firebase.child(user).child(category).set(current + increment)

    return firebase.get()


def firebase_stats(firebase):
    """
    Returns two dictionaries.
    The first with the user names as keys and the respective user recycling count as values.
    It will look like this:
    {'frank': 91, 'grace': 169, 'ken': 145, 'shelly': 103, 'tim': 112}
    The second dictionary has the recycling categories as keys and the respective category count as values.
    It will look like this:
    {'bottles': 229, 'cans': 205, 'others': 186}
    """
    data = firebase.get()
    by_user_count = {user: sum(data[user].values()) for user in data.keys()}
    by_category_count = {}

    for user in data:
        for category in data[user]:
            if category not in by_category_count:
                by_category_count[category] = data[user][category]
            else:
                by_category_count[category] += data[user][category]

    return by_user_count, by_category_count


def firebase_random(firebase):
    """
    For testing purposes, this function will set random values to all counts in the firebase.
    Returns a dictionary of the data in the updated firebase.
    """
    users = ['ken', 'tim', 'grace', 'shelly', 'frank']
    categories = ['bottles', 'cans', 'others']

    from random import randint
    for user in users:
        for category in categories:
            firebase.child(user).child(category).set(randint(1, 100))

    return firebase.get()


def firebase_plot(firebase):
    """
    This plotting function takes in two dictionaries by calling the firebase_stats function.
    The first the the statistics by user, and the second the statistics by category.
    It then uses matplotlib to plot 2 bar charts based on the data in the respective dictionaries.
    """
    by_user_count, by_category_count = firebase_stats(firebase)

    plt.bar(range(len(by_user_count)), by_user_count.values())
    plt.xticks(range(len(by_user_count)), by_user_count.keys())
    plt.title('Statistics by user')
    plt.xlabel('User name')
    plt.ylabel('Number of items recycled')
    plt.show()

    plt.bar(range(len(by_category_count)), by_category_count.values())
    plt.xticks(range(len(by_category_count)), by_category_count.keys())
    plt.title('Statistics by category')
    plt.xlabel('Recyclable item category')
    plt.ylabel('Number of items recycled')
    plt.show()
