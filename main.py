import os
import sys
from pathlib import Path  # Python 3.6+ only

from dotenv import load_dotenv

import api
from game_layer import GameLayer

load_dotenv()
API_KEY = os.getenv("API_KEY")
# The different map names can be found on considition.com/rules
# Map name taken as command line argument.
# If left empty, the map "training1" will be selected.
map_name = sys.argv[1] if len(sys.argv) > 1 else "training1"

game_layer: GameLayer = GameLayer(API_KEY)


def main():
    try:
        game_layer.new_game(map_name)
        print("Starting game: " + game_layer.game_state.game_id)
        print("Map:", map_name)
        game_layer.start_game()
        while game_layer.game_state.turn < game_layer.game_state.max_turns:
            take_turn()
        print("Done with game: " + game_layer.game_state.game_id)
        print("Final score was: " + str(game_layer.get_score()["finalScore"]))
    except KeyboardInterrupt:  # End game session in case of exceptions
        print(f"\nForce quit game: {game_layer.game_state.game_id}")
        game_layer.end_game()
    except Exception as e:  # Catching generic exceptions
        print(f"Error: {e}")
        game_layer.end_game()


def take_turn():
    state = game_layer.game_state

    # Take one of the following actions in order of priority #
    if residence_maintenance(state):
        pass
    elif regulate_temperature(state):
        pass
    elif build_residence(state):
        pass
    elif place_residence(state):
        pass
    else:
        game_layer.wait()
    # --- #

    for message in game_layer.game_state.messages:
        print(message)
    for error in game_layer.game_state.errors:
        print("Error: " + error)


# Maintain a residence in need of maintenance
def residence_maintenance(state):
    for residence in state.residences:
        if residence.health < 50:
            game_layer.maintenance((residence.X, residence.Y))
            return True


# Regulate the temperature of a residence if it's too low/high
def regulate_temperature(state):
    for residence in state.residences:
        if residence.temperature < 18 or residence.temperature > 24:
            blueprint = game_layer.get_residence_blueprint(residence.building_name)
            energy = (
                blueprint.base_energy_need
                + (21 - residence.temperature)
                + (residence.temperature - state.current_temp)
                * blueprint.emissivity
                / 1
                - residence.current_pop * 0.04
            )
            game_layer.adjust_energy_level((residence.X, residence.Y), energy)
            return True


# Build a residence that is under construction
def build_residence(state):
    for residence in state.residences:
        if residence.build_progress < 100:
            game_layer.build((residence.X, residence.Y))
            return True


# Place a new (cheapest) residence at an available spot
def place_residence(state):
    cheapest_residence = min(state.available_residence_buildings, key=lambda x: x.cost)
    if state.housing_queue >= cheapest_residence.max_pop:
        for i in range(len(state.map)):
            for j in range(len(state.map)):
                if state.map[i][j] == 0:
                    x = i
                    y = j
                    break
        state.map[x][y] = 1
        game_layer.place_foundation((x, y), cheapest_residence.building_name)
        return True


if __name__ == "__main__":
    main()