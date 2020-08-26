import requests
from requests import RequestException

base_api_path = "https://game.considition.com/api/game/"
sess = None


def new_game(api_key, game_options=""):
    try:
        global sess
        if not sess:
            sess = requests.Session()
        response = sess.post(base_api_path + "new", json=game_options, headers={"x-api-key": api_key})
        if response.status_code == 200:
            return response.json()

        print("Fatal Error: could not create new game")
        print(str(response.status_code) + " " + response.reason + ": " + response.text)
    except RequestException as e:
        print("Fatal Error: could not create new game")
        print("Something went wrong with the request: " + str(e))


def start_game(api_key, game_id=None):
    if game_id:
        game_id = "?GameId=" + game_id
    else:
        game_id = ""
    try:
        global sess
        if not sess:
            sess = requests.Session()
        response = sess.get(base_api_path + "start" + game_id, headers={"x-api-key": api_key})
        if response.status_code == 200:
            return response.json()

        print("Fatal Error: could not start game")
        print(str(response.status_code) + " " + response.reason + ": " + response.text)
    except RequestException as e:
        print("Fatal Error: could not start game")
        print("Something went wrong with the request: " + str(e))


def end_game(api_key, game_id=None):
    if game_id:
        game_id = "?GameId=" + game_id
    else:
        game_id = ""
    try:
        global sess
        if not sess:
            sess = requests.Session()
        response = sess.get(base_api_path + "end" + game_id, headers={"x-api-key": api_key})
        if response.status_code == 200:
            return

        print("Fatal Error: could not end game")
        print(str(response.status_code) + " " + response.reason + ": " + response.text)
    except RequestException as e:
        print("Fatal Error: could not end game")
        print("Something went wrong with the request: " + str(e))


def get_score(api_key, game_id=None):
    if game_id:
        game_id = "?GameId=" + game_id
    else:
        game_id = ""
    try:
        global sess
        if not sess:
            sess = requests.Session()
        response = sess.get(base_api_path + "score" + game_id, headers={"x-api-key": api_key})
        if response.status_code == 200:
            return response.json()

        print("Fatal Error: could not get score")
        print(str(response.status_code) + " " + response.reason + ": " + response.text)
    except RequestException as e:
        print("Fatal Error: could not get score")
        print("Something went wrong with the request: " + str(e))


def get_game_info(api_key, game_id=None):
    if game_id:
        game_id = "?GameId=" + game_id
    else:
        game_id = ""
    try:
        global sess
        if not sess:
            sess = requests.Session()
        response = sess.get(base_api_path + "gameInfo" + game_id, headers={"x-api-key": api_key})
        if response.status_code == 200:
            return response.json()

        print("Fatal Error: could not get game info")
        print(str(response.status_code) + " " + response.reason + ": " + response.text)
    except RequestException as e:
        print("Fatal Error: could not get game info")
        print("Something went wrong with the request: " + str(e))        


def place_foundation(api_key, foundation, game_id=None):
    if game_id:
        game_id = "?GameId=" + game_id
    else:
        game_id = ""
    try:
        global sess
        if not sess:
            sess = requests.Session()
        response = sess.post(base_api_path + "action/startBuild" + game_id, json=foundation, headers={"x-api-key": api_key})
        if response.status_code == 200:
            return response.json()

        print("Fatal Error: could not do action place foundation")
        print(str(response.status_code) + " " + response.reason + ": " + response.text)
    except RequestException as e:
        print("Fatal Error: could not do action place foundation")
        print("Something went wrong with the request: " + str(e))


def build(api_key, pos, game_id=None):
    if game_id:
        game_id = "?GameId=" + game_id
    else:
        game_id = ""
    try:
        global sess
        if not sess:
            sess = requests.Session()
        response = sess.post(base_api_path + "action/Build" + game_id, json=pos, headers={"x-api-key": api_key})
        if response.status_code == 200:
            return response.json()

        print("Fatal Error: could not do action build")
        print(str(response.status_code) + " " + response.reason + ": " + response.text)
    except RequestException as e:
        print("Fatal Error: could not do action build")
        print("Something went wrong with the request: " + str(e))


def maintenance(api_key, pos, game_id=None):
    if game_id:
        game_id = "?GameId=" + game_id
    else:
        game_id = ""
    try:
        global sess
        if not sess:
            sess = requests.Session()
        response = sess.post(base_api_path + "action/maintenance" + game_id, json=pos, headers={"x-api-key": api_key})
        if response.status_code == 200:
            return response.json()

        print("Fatal Error: could not do action maintenance")
        print(str(response.status_code) + " " + response.reason + ": " + response.text)
    except RequestException as e:
        print("Fatal Error: could not do action maintenance")
        print("Something went wrong with the request: " + str(e))


def demolish(api_key, pos, game_id=None):
    if game_id:
        game_id = "?GameId=" + game_id
    else:
        game_id = ""
    try:
        global sess
        if not sess:
            sess = requests.Session()
        response = sess.post(base_api_path + "action/demolish" + game_id, json=pos, headers={"x-api-key": api_key})
        if response.status_code == 200:
            return response.json()

        print("Fatal Error: could not do action demolish")
        print(str(response.status_code) + " " + response.reason + ": " + response.text)
    except RequestException as e:
        print("Fatal Error: could not do action demolish")
        print("Something went wrong with the request: " + str(e))


def wait(api_key, game_id=None):
    if game_id:
        game_id = "?GameId=" + game_id
    else:
        game_id = ""
    try:
        global sess
        if not sess:
            sess = requests.Session()
        response = sess.post(base_api_path + "action/wait" + game_id, headers={"x-api-key": api_key})
        if response.status_code == 200:
            return response.json()

        print("Fatal Error: could not do action wait")
        print(str(response.status_code) + " " + response.reason + ": " + response.text)
    except RequestException as e:
        print("Fatal Error: could not do action wait")
        print("Something went wrong with the request: " + str(e))


def adjust_energy(api_key, energy_level, game_id=None):
    if game_id:
        game_id = "?GameId=" + game_id
    else:
        game_id = ""
    try:
        global sess
        if not sess:
            sess = requests.Session()
        response = sess.post(base_api_path + "action/adjustEnergy" + game_id, json=energy_level, headers={"x-api-key": api_key})
        if response.status_code == 200:
            return response.json() 
        print("Fatal Error: could not do action adjust energy level")
        print(str(response.status_code) + " " + response.reason + ": " + response.text)
    except RequestException as e:
        print("Fatal Error: could not do action adjust energy level")
        print("Something went wrong with the request: " + str(e))


def buy_upgrades(api_key, upgrade, game_id=None):
    if game_id:
        game_id = "?GameId=" + game_id
    else:
        game_id = ""
    try:
        global sess
        if not sess:
            sess = requests.Session()
        response = sess.post(base_api_path + "action/buyUpgrade" + game_id, json=upgrade, headers={"x-api-key": api_key})
        if response.status_code == 200:
            return response.json()

        print("Fatal Error: could not do action buy upgrades")
        print(str(response.status_code) + " " + response.reason + ": " + response.text)
    except RequestException as e:
        print("Fatal Error: could not do action buy upgrades")
        print("Something went wrong with the request: " + str(e))


def get_game_state(api_key, game_id=None):
    if game_id:
        game_id = "?GameId=" + game_id
    else:
        game_id = ""
    try:
        global sess
        if not sess:
            sess = requests.Session()
        response = sess.get(base_api_path + "gameState" + game_id, headers={"x-api-key": api_key})
        if response.status_code == 200:
            return response.json()

        print("Fatal Error: could not get game state")
        print(str(response.status_code) + " " + response.reason + ": " + response.text)
    except RequestException as e:
        print("Fatal Error: could not do get game state")
        print("Something went wrong with the request: " + str(e))


def get_games(api_key):
    try:
        global sess
        if not sess:
            sess = requests.Session()
        response = sess.get(base_api_path + "games", headers={"x-api-key": api_key})
        if response.status_code == 200:
            return response.json()

        print("Fatal Error: could not get games")
        print(str(response.status_code) + " " + response.reason + ": " + response.text)
    except RequestException as e:
        print("Fatal Error: could not get games")
        print("Something went wrong with the request: " + str(e))
