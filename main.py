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
    elif place_utility(state):
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
    if len(state.residences) < 1:
        return False

    residence = min(state.residences, key=lambda x: x.health)
    blueprint = GAME_LAYER.get_residence_blueprint(residence.building_name)
    if residence.health < 70 and state.funds > blueprint.maintenance_cost:
        GAME_LAYER.maintenance((residence.X, residence.Y))
        return True


# Regulate the temperature of a residence if it's too low/high
def regulate_temperature(state):
    if len(state.residences) < 1 or state.turn < 2:
        return False
    optimal_temperature = 21
    degrees_per_pop = 0.04
    degrees_per_excess_mwh = 0.75
    if state.funds >= 150:
        residence = max(state.residences, key=lambda x: abs(x.temperature - 21))
        if residence.build_progress >= 100:
            # residence_prev_state = next(
            #     r
            #     for r in state.prev_state.residences
            #     if residence.X == r.X and residence.Y == r.Y
            # )
            blueprint = GAME_LAYER.get_residence_blueprint(residence.building_name)

            base_energy_need = (
                blueprint.base_energy_need + 1.8
                if "Charger" in residence.effects
                else blueprint.base_energy_need
            )
            energy_wanted = (
                optimal_temperature
                - residence.temperature
                - degrees_per_pop * residence.current_pop
                + (residence.temperature - state.current_temp) * blueprint.emissivity
            ) / degrees_per_excess_mwh + base_energy_need
            energy = max(energy_wanted, base_energy_need + 1e-2)

            if (
                abs(residence.temperature - 21)
                >= 1.5
                # and abs(residence.temperature - residence_prev_state.temperature) <= 0.3
                # and abs(energy - residence_prev_state.requested_energy_in) >= 0.1
            ):
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
    # TODO: Add logic to place building near utilities
    residence = _choose_residence(state)
    if (
        state.funds >= residence.cost
        and state.housing_queue >= residence.max_pop / 4
        # and state.current_temp >= state.max_temp * 0.75 # Don't build when it's cold outside
    ):
        for i in range(len(state.map)):
            for j in range(len(state.map)):
                if state.map[i][j] == 0:
                    x = i
                    y = j
                    break
        state.map[x][y] = 1
        GAME_LAYER.place_foundation((x, y), residence.building_name)
        return True


def place_utility(state):
    # TODO: Add logic to place utilities near buildings
    if len(state.utilities) > 2:
        return False 

    utility = _choose_utility(state)
    if utility and state.funds >= utility.cost:  # TODO: Re-Evaluate this check
        for i in range(len(state.map)):
            for j in range(len(state.map)):
                if state.map[i][j] == 0:
                    x = i
                    y = j
                    break
        state.map[x][y] = 2
        GAME_LAYER.place_foundation((x, y), utility.building_name)
        return True


def available_upgrades(state):
    for residence in state.residences:
        upgrade = _choose_upgrade(state, residence)
        if upgrade:
            GAME_LAYER.buy_upgrade(
                (residence.X, residence.Y),
                upgrade.name,
            )
            return True


def _choose_utility(state):
    # TODO: Decision tree for chosing the right utility
    available_utilities = state.available_utility_buildings
    # Cost is only found on blueprint
    utility_blueprints = [GAME_LAYER.get_utility_blueprint(utility.building_name) for utility in available_utilities]
    utility = max(utility_blueprints, key=lambda x: x.cost)
    # utility = sorted(utility_blueprints, key=lambda x: x.cost, reverse=True)[1]
    if state.funds > utility.cost:
        return utility


def _choose_upgrade(state, residence):
    # TODO: Decision tree for choosing the right upgrade
    return _choose_all_upgrades(state, residence)
    # return _cheapest_upgrade(state, residence)


def _choose_all_upgrades(state, residence):
    for upgrade in sorted(state.available_upgrades, key=lambda x: x.cost):
        if state.funds > upgrade.cost and upgrade.name not in residence.effects:
            return upgrade


def _cheapest_upgrade(state, residence):
    upgrade = min(state.available_upgrades, key=lambda x: x.cost)
    if state.funds > upgrade.cost and upgrade.name not in residence.effects:
        return upgrade


def _choose_residence(state):
    # TODO: Decision tree for choosing the right residence
    # TODO: Choose residence based on funds, map temperature, ...
    return max(
        state.available_residence_buildings,
        key=lambda x: x.cost,
    )
    # return sorted(state.available_residence_buildings, key=lambda x: x.cost, reverse=True)[1]
    # return min(state.available_residence_buildings, key=lambda x: x.cost)
    # import random
    # return random.choice(state.available_residence_buildings)


if __name__ == "__main__":
    main()
