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

GAME_LAYER: GameLayer = GameLayer(API_KEY)

def main():
    try:
        GAME_LAYER.new_game(map_name)
        print("Starting game: " + GAME_LAYER.game_state.game_id)
        print("Map:", map_name)
        GAME_LAYER.start_game()
        while GAME_LAYER.game_state.turn < GAME_LAYER.game_state.max_turns:
            take_turn()
        print("Done with game: " + GAME_LAYER.game_state.game_id)
        print("Final score was: " + str(GAME_LAYER.get_score()["finalScore"]))
    except KeyboardInterrupt:  # End game session in case of exceptions
        print(f"\nForce quit game: {GAME_LAYER.game_state.game_id}")
        GAME_LAYER.end_game()
    except Exception as e:  # Catching generic exceptions
        print(f"Error: {e}")
        GAME_LAYER.end_game()


def take_turn():
    state = GAME_LAYER.game_state

    # Take one of the following actions in order of priority #
    if residence_maintenance(state):
        pass
    elif regulate_temperature(state):
        pass
    elif build_residence(state):
        pass
    elif available_upgrades(state):
        pass
    elif place_residence(state):
        pass
    else:
        GAME_LAYER.wait()
    # --- #

    for message in GAME_LAYER.game_state.messages:
        print(message)
    for error in GAME_LAYER.game_state.errors:
        print("Error: " + error)


# Maintain a residence in need of maintenance
def residence_maintenance(state):
    for residence in state.residences:
        blueprint = GAME_LAYER.get_residence_blueprint(residence.building_name)
        if residence.health < 50 and state.funds > blueprint.maintenance_cost:
            GAME_LAYER.maintenance((residence.X, residence.Y))
            return True


# Regulate the temperature of a residence if it's too low/high
def regulate_temperature(state):
    # TODO: Avoid getting stuck with the following error
    # Error: The requested energy for the building at: (9, 4) can't be lower than the base energy need: 4.65
    for residence in state.residences:
        if (
            residence.temperature < 18 or residence.temperature > 24
        ) and state.funds > 150:
            blueprint = GAME_LAYER.get_residence_blueprint(residence.building_name)
            energy = (
                blueprint.base_energy_need
                + (21 - residence.temperature)
                + (residence.temperature - state.current_temp)
                * blueprint.emissivity
                / 1
                - residence.current_pop * 0.04
            )

            # This check lowers our score by roughly 1000 points
            # but avoids us from keep repeating same invalid turn
            # if blueprint.base_energy_need > energy:
            #     return False

            GAME_LAYER.adjust_energy_level((residence.X, residence.Y), energy)
            return True


# Build a residence that is under construction
def build_residence(state):
    for residence in state.residences:
        if residence.build_progress < 100:
            GAME_LAYER.build((residence.X, residence.Y))
            return True


# Place a new residence at an available spot
def place_residence(state):
    residence = _choose_residence(state)
    if state.funds >= residence.cost and state.housing_queue >= residence.max_pop:
        for i in range(len(state.map)):
            for j in range(len(state.map)):
                if state.map[i][j] == 0:
                    x = i
                    y = j
                    break
        state.map[x][y] = 1
        GAME_LAYER.place_foundation((x, y), residence.building_name)
        return True


def available_upgrades(state):
    upgrade = _choose_upgrade(state)
    for residence in state.residences:
        if state.funds > upgrade.cost and upgrade.name not in residence.effects:
            GAME_LAYER.buy_upgrade(
                (residence.X, residence.Y),
                upgrade.name,
            )
            return True


def _choose_upgrade(state):
    # TODO: Decision tree for choosing the right upgrade
    return max(state.available_upgrades, key=lambda x: x.cost)
    # return min(state.available_upgrades, key=lambda x: x.cost)


def _choose_residence(state):
    # TODO: Decision tree for choosing the right residence
    return max(state.available_residence_buildings, key=lambda x: x.cost)
    # return sorted(state.available_residence_buildings, key=lambda x: x.cost, reverse=True)[1]
    # return min(state.available_residence_buildings, key=lambda x: x.cost)
    # import random
    # return random.choice(state.available_residence_buildings)


if __name__ == "__main__":
    main()
