from flask import Flask, request, jsonify
from src.index import run, setup
from flask_cors import CORS
from memory import create_or_update_db, get_history_from_db, update_history_in_db
import sqlite3
import threading
import requests

app = Flask(__name__)
CORS(app)


@app.route('/')
def hello_world():
    return 'Hello, World!'


""" 
    This is the setup endpoint. It is called when the user first creates a new
    instance of your app. It is passed a config object that contains the
    user's input from the setup form. You can use this to initialize your app
    with the user's input.
            
    The setup function should return a dictionary with the following keys:
    - success: a boolean indicating whether the setup was successful
    - message: a string containing a message to display to the user
                   
    The setup function should raise an exception if the setup was not successful.
    The exception message will be displayed to the user.
"""


@app.route('/setup', methods=['POST'])
def handle_setup():
    try:
        config = request.json['config']
        response = setup(config)
        return jsonify({"success": True, "message": "Setup successful."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


""" 
    This is the run endpoint. It is called when the user sends a message to
    your app. It is passed a message object that contains the user's input.
    You can use this to process the user's input and return a response.

    The run function should return a dictionary with the following keys:
    - success: a boolean indicating whether the run was successful
    - message: a string containing a message to display to the user
    - data: a dictionary containing any data you want to pass to the frontend
    - context: a dictionary containing any context you want to pass to the next
                run call

    The run function should raise an exception if the run was not successful.
    The exception message will be displayed to the user.
 """


@app.route('/run', methods=['POST'])
def handle_run():
    try:
        message = request.json['msg']
        response = run(message)
        return jsonify(response)
    except Exception as e:
        return jsonify(str(e))


def process_request(response_url, text):
    # hit the external API endpoint with a GET request
    try:
        # return the result to the response_url
        requests.post(response_url, json={"text": run(text)})
    except requests.exceptions.Timeout:
        # handle timeout error
        requests.post(response_url, json={'text': 'Request timed out'})


@app.route('/slack', methods=['POST'])
def handle_slack():
    token = request.form['token']
    command = request.form['command']
    text = request.form['text']
    user_id = request.form['user_id']
    response_url = request.form['response_url']

    threading.Thread(target=process_request,
                     args=(response_url, text, )).start()

    # Return a 200 OK response to acknowledge receipt of the command
    return "", 200


@app.route('/messenger', methods=['GET', 'POST'])
def handle_messenger():
    print(request.args)
    # Return a 200 OK response to acknowledge receipt of the command
    return request.args['hub.challenge'], 200


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    create_or_update_db(db)
    return db


def close_db(e=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


if __name__ == '__main__':
    app.teardown_appcontext(close_db)
    app.run(host="localhost", port=8080)
