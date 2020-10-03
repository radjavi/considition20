import operator
import os
import sys
from pathlib import Path  # Python 3.6+ only

from dotenv import load_dotenv

import api
from game_layer import GameLayer
from logic import (
    building_score,
    calculate_energy_need,
    best_residence_location,
    best_utility_location,
)
from constants import *

load_dotenv()
API_KEY = os.getenv("API_KEY")
# The different map names can be found on considition.com/rules
# Map name taken as command line argument.
# If left empty, the map "training1" will be selected.
map_name = sys.argv[1] if len(sys.argv) > 1 else "training1"

GAME_LAYER: GameLayer = GameLayer(API_KEY)

LAST_RESIDENCE_BUILD_TURN = 0


def main():
    try:
        GAME_LAYER.new_game(map_name)
        print("Starting game: " + GAME_LAYER.game_state.game_id)
        print("Map:", map_name)
        GAME_LAYER.start_game()
        preprocess_map()  # Make neccessary pre-processing of the map
        # clean_map()  # Demolish existing buildings
        while GAME_LAYER.game_state.turn < GAME_LAYER.game_state.max_turns:
            take_turn()
        print("Done with game: " + GAME_LAYER.game_state.game_id)
        print("Final score was: " + str(GAME_LAYER.get_score()["finalScore"]))
        print("Total happiness:", GAME_LAYER.game_state.total_happiness)
        print("Total CO2:", GAME_LAYER.game_state.total_co2)
    except KeyboardInterrupt:  # End game session in case of exceptions
        print(f"\nForce quit game: {GAME_LAYER.game_state.game_id}")
        GAME_LAYER.end_game()
    except Exception as e:  # Catching generic exceptions
        GAME_LAYER.end_game()
        raise (e)
        # print(f"Error: {e}")


# Modify map numbers to satisfy custom identifiers
def preprocess_map():
    print("Preprocessing map...")
    state = GAME_LAYER.game_state
    for residence in state.residences:
        x, y = residence.X, residence.Y
        state.map[x][y] = POS_RESIDENCE
    for utility in state.utilities:
        x, y = utility.X, utility.Y
        if utility.building_name == "Park":
            state.map[x][y] = POS_PARK
        elif utility.building_name == "Mall":
            state.map[x][y] = POS_MALL
        elif utility.building_name == "WindTurbine":
            state.map[x][y] = POS_WINDTURBINE


def clean_map():
    print("Cleaning up map...")
    state = GAME_LAYER.game_state
    if len(state.residences) > 0:
        for residence in state.residences:
            GAME_LAYER.demolish((residence.X, residence.Y))
    else:
        print("Nothing to clean up.")


def take_turn():
    state = GAME_LAYER.game_state

    strategy(state)

    for message in GAME_LAYER.game_state.messages:
        print(message)
    for error in GAME_LAYER.game_state.errors:
        print("Error: " + error)


def strategy(state):
    # Take one of the following actions in order of priority #
    if residence_maintenance(state):
        pass
    elif residence_regulator(state):
        pass
    elif regulate_temperature(state):
        pass
    elif perform_construction(state):
        pass
    elif place_residence(state):
        pass
    elif place_utility(state):
        pass
    elif residence_upgrade(state):
        pass
    else:
        GAME_LAYER.wait()


# Maintain a residence in need of maintenance
def residence_maintenance(state):
    if len(state.residences) < 1:
        return False

    residence = min(state.residences, key=lambda x: x.health)
    blueprint = GAME_LAYER.get_residence_blueprint(residence.building_name)
    if (
        residence.health < HEALTH_MIN
        and residence.happiness_per_tick_per_pop
        < GAME_LAYER.get_blueprint(residence.building_name).max_happiness + 0.16
        and state.funds - blueprint.maintenance_cost > FUNDS_MIN
    ):
        GAME_LAYER.maintenance((residence.X, residence.Y))
        return True


# Regulate the temperature of a residence if it's too low/high
def regulate_temperature(state):
    if len(state.residences) < 1 or state.turn < 2:
        return False
    if state.funds > 150:
        residence = max(state.residences, key=lambda x: abs(x.temperature - 21))
        if residence.build_progress >= 100:
            blueprint = blueprint = GAME_LAYER.get_residence_blueprint(
                residence.building_name
            )
            energy = calculate_energy_need(state, residence, blueprint)

            if abs(residence.temperature - 21) >= 1.5:
                GAME_LAYER.adjust_energy_level((residence.X, residence.Y), energy)
                return True


# Perform construction on a residence or utility that is not finished
def perform_construction(state):
    for residence in state.residences:
        if residence.build_progress < 100:
            GAME_LAYER.build((residence.X, residence.Y))
            return True
    for utility in state.utilities:
        if utility.build_progress < 100:
            GAME_LAYER.build((utility.X, utility.Y))
            return True


# Place a new residence at an available spot
def place_residence(state):
    residence = _choose_residence(state)
    if (
        residence
        and state.funds - residence.cost >= FUNDS_MIN
        and state.queue_happiness < 20
    ):
        x, y = best_residence_location(state)
        if x < 0 or y < 0:
            return False

        state.map[x][y] = POS_RESIDENCE
        global LAST_RESIDENCE_BUILD_TURN
        LAST_RESIDENCE_BUILD_TURN = state.turn
        GAME_LAYER.place_foundation((x, y), residence.building_name)
        return True


def place_utility(state):
    # Alternate between utility and residence
    if (len(state.utilities) + len(state.residences)) % 3:
        return False

    utility = _choose_utility(state)
    if utility and state.funds - utility.cost > FUNDS_MIN:
        x, y = best_utility_location(state, utility.building_name)
        if x < 0 or y < 0:
            return False

        if utility.building_name == "Park":
            state.map[x][y] = POS_PARK
        elif utility.building_name == "Mall":
            state.map[x][y] = POS_MALL
        elif utility.building_name == "WindTurbine":
            state.map[x][y] = POS_WINDTURBINE
        GAME_LAYER.place_foundation((x, y), utility.building_name)
        return True


def _choose_utility(state):
    available_utilities = state.available_utility_buildings
    # Cost is only found on blueprint
    utility_blueprints = [
        GAME_LAYER.get_utility_blueprint(utility.building_name)
        for utility in available_utilities
    ]

    # # If mall is already placed, choose WindTurbine or Park
    # if next((x for x in state.utilities if x.building_name == "Mall"), None):
    #     utility = next(
    #         (x for x in utility_blueprints if x.building_name == "WindTurbine"), None
    #     )
    # else:
    #     utility = next(
    #         (x for x in utility_blueprints if x.building_name == "Mall"), None
    #     )
    if len(state.residences) >= 5:
        utility = next(
            (x for x in utility_blueprints if x.building_name == "WindTurbine"), None
        )
    # If mall is already placed, choose Park
    elif state.funds > FUNDS_MED:
        utility = next(
            (x for x in utility_blueprints if x.building_name == "Mall"), None
        )
    else:
        utility = next(
            (x for x in utility_blueprints if x.building_name == "Park"), None
        )
    return utility


def residence_regulator(state):
    for residence in state.residences:
        if residence.build_progress < 100:
            continue
        if "Regulator" not in residence.effects:
            GAME_LAYER.buy_upgrade(
                (residence.X, residence.Y),
                "Regulator",
            )
            return True


def residence_upgrade(state):
    for residence in state.residences:
        if residence.build_progress < 100:
            continue
        upgrade = _choose_upgrade(state, residence)
        if upgrade:
            GAME_LAYER.buy_upgrade(
                (residence.X, residence.Y),
                upgrade.name,
            )
            return True


def _choose_upgrade(state, residence):
    # TODO: Decision tree for choosing the right upgrade
    return _choose_all_upgrades(state, residence)
    # return _cheapest_upgrade(state, residence)
    # return _choose_upgrades(
    #     state, residence, ["SolarPanel", "Caretaker", "Charger", "Playground"]
    # )


def _choose_all_upgrades(state, residence):
    for upgrade in sorted(state.available_upgrades, key=lambda x: x.cost):
        if (
            state.funds - upgrade.cost > FUNDS_MED
            and upgrade.name not in residence.effects
        ):
            return upgrade


def _choose_upgrades(state, residence, upgrades):
    for upgrade in sorted(
        (
            x
            for x in state.available_upgrades
            if x.name in upgrades and x.name not in residence.effects
        ),
        key=lambda x: x.cost,
    ):
        if state.funds - upgrade.cost >= FUNDS_MED:
            return upgrade


def _cheapest_upgrade(state, residence):
    upgrade = min(state.available_upgrades, key=lambda x: x.cost)
    if state.funds - upgrade.cost > FUNDS_MIN and upgrade.name not in residence.effects:
        return upgrade


def _choose_residence(state):
    return _optimal_building(state, _feasible_buildings(state))


def _choose_residence2(state):
    return _optimal_building2(state, _feasible_buildings2(state))


def _feasible_buildings(state):
    return [
        x for x in state.available_residence_buildings if x.release_tick <= state.turn
    ]


def _feasible_buildings2(state):
    return [
        x
        for x in state.available_residence_buildings
        if x.release_tick <= state.turn
        and len([y for y in state.residences if x.building_name == y.building_name])
        < RESIDENCE_LIMITS[x.building_name]
    ]


# Choose the building that maximizes building_score
def _optimal_building(state, feasible_buildings):
    return max(feasible_buildings, key=lambda x: building_score(state, x), default=None)


# Choose the building that matches the housing queue closest
def _optimal_building2(state, feasible_buildings):
    func = lambda x: abs(state.housing_queue - x.max_pop)
    # Building with max_pop that matches housing queue closest
    building = min(feasible_buildings, key=func, default=None)
    if building:
        buildings = [x for x in feasible_buildings if func(x) == func(building)]
        # If multiple buldings, choose based on second condition
        if len(buildings) > 1:
            return max(buildings, key=lambda x: x.max_pop)
        else:
            return building


if __name__ == "__main__":
    main()
