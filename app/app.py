from flask import Flask, request, jsonify, g
from src.index import run, setup
from flask_cors import CORS
from memory import create_or_update_db, get_history_from_db, update_history_in_db
from logs import update_logs_in_db, get_logs_from_db, create_or_update_logs_db
import sqlite3
import threading
import requests
import logging

app = Flask(__name__)
CORS(app)

""" 
    Logger to log messages to the console.
"""
LOG_DATABASE = "log.db"

""" 
    Database to save chat history.
"""
DATABASE = "chat_history.db"


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

        # Create a log message dictionary
        log_message = {
            'type': '/setup',
            'ip': request.remote_addr,
            'session_id': "default",
            'message': "",
            'history': [],
            'response': "",
            'error': "None"
        }

        # Log the message
        update_logs_in_db(get_logs(), log_message)

        return jsonify({"success": True, "message": "Setup successful."})
    except Exception as e:
        # Create a log message dictionary
        log_message = {
            'type': '/setup',
            'ip': request.remote_addr,
            'session_id': "default",
            'message': "",
            'history': [],
            'response': "",
            'error': str(e)
        }

        # Log the message
        update_logs_in_db(get_logs(), log_message)

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

    session_id = None

    try:
        # Get the session ID from the request
        session_id = request.json['session_id']
    except:
        pass

    # Get the history from the database
    history = get_history_from_db(get_db(), session_id)

    try:
        message = request.json['msg']
        response = run(message=message, history=history)

        # Update the history in the database with human message and bot response
        update_history_in_db(get_db(), session_id, message, "human")
        update_history_in_db(get_db(), session_id, response, "ai")

        # Create a log message dictionary
        log_message = {
            'type': '/run',
            'ip': request.remote_addr,
            'session_id': session_id or "default",
            'message': message,
            'history': history,
            'response': response,
            'error': "None"
        }

        # Log the message
        update_logs_in_db(get_logs(), log_message)

        return jsonify(response)
    except Exception as e:
        # Create a log message dictionary
        log_message = {
            'type': '/run',
            'ip': request.remote_addr,
            'session_id': session_id or "default",
            'message': message,
            'history': history,
            'response': "None",
            'error': str(e)
        }

        # Log the message
        update_logs_in_db(get_logs(), log_message)

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


@app.route('/logs')
def get_logs():
    return jsonify(get_logs_from_db(get_logs()))


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


def get_logs():
    db = getattr(g, '_logs', None)
    if db is None:
        db = g._logs = sqlite3.connect(LOG_DATABASE)
    create_or_update_logs_db(db)
    return db


def close_logs(e=None):
    db = getattr(g, '_logs', None)
    if db is not None:
        db.close()


if __name__ == '__main__':
    app.teardown_appcontext(close_db)
    app.run(host="0.0.0.0", port=8080)
