import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from matplotlib import pyplot as plt

def firebase_setup():
    """
    TODO: Docstring
    """
    import firebase_admin
    from firebase_admin import credentials
    from firebase_admin import db
    
    # authenticate using json key location and url
    cred = credentials.Certificate('/home/pi/SmartBin/data/guiwithkivy-48023-firebase-adminsdk-i41qf-c08ecb8507.json')
    firebase_admin.initialize_app(cred, {'databaseURL': 'https://guiwithkivy-48023.firebaseio.com/',})
    firebase = db.reference('/')
    
    return firebase

def firebase_reset(firebase):
    """
    TODO: Docstring
    """
    users = ['ken', 'tim', 'grace', 'shelly', 'frank']
    categories = ['bottles', 'cans', 'others']
    
    for user in users:
        for category in categories:
            firebase.child(user).child(category).set(0)
            
    return firebase.get()


def firebase_update(firebase, user, category, increment):
    """
    TODO: Docstring
    """
    current = firebase.child(user).child(category).get()
    firebase.child(user).child(category).set(current + increment)
    
    return firebase.get()


def firebase_stats(firebase):
    """
    TODO: Docstring
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
    TODO: Docstring
    """
    users = ['ken', 'tim', 'grace', 'shelly', 'frank']
    categories = ['bottles', 'cans', 'others']
    
    from random import randint
    for user in users:
        for category in categories:
            firebase.child(user).child(category).set(randint(1,100))
            
    return firebase.get()


def firebase_plot(firebase):
    """
    TODO: Docstring
    """
    by_user_count, by_category_count = firebase_stats(firebase)
    
    plt.bar(range(len(by_user_count)), by_user_count.values())
    plt.xticks(range(len(by_user_count)), by_user_count.keys())
    plt.title('Statistics by user')
    plt.show()
    
    plt.bar(range(len(by_category_count)), by_category_count.values())
    plt.xticks(range(len(by_category_count)), by_category_count.keys())
    plt.title('Statistics by category')
    plt.show()
