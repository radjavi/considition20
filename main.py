import operator
import os
import sys
from pathlib import Path  # Python 3.6+ only

from dotenv import load_dotenv

import api
from game_layer import GameLayer
from logic import best_residence_location, best_utility_location
from constants import *

load_dotenv()
API_KEY = os.getenv("API_KEY")
# The different map names can be found on considition.com/rules
# Map name taken as command line argument.
# If left empty, the map "training1" will be selected.
map_name = sys.argv[1] if len(sys.argv) > 1 else "training1"
verbose = sys.argv[2] if len(sys.argv) > 2 else False

GAME_LAYER: GameLayer = GameLayer(API_KEY)


def main():
    try:
        GAME_LAYER.new_game(map_name)
        print(f"Starting game: {GAME_LAYER.game_state.game_id}")
        print(f"Map: {map_name}")
        GAME_LAYER.start_game()
        preprocess_map()  # Make neccessary pre-processing of the map
        while GAME_LAYER.game_state.turn < GAME_LAYER.game_state.max_turns:
            take_turn()

        print(f"Done with game: {GAME_LAYER.game_state.game_id}")
        if verbose:
            print("----------")
            print(f"Total Happiness: {int(GAME_LAYER.game_state.total_happiness)}")
            print(f"Total CO2: {int(GAME_LAYER.game_state.total_co2)}")
            print("----------")
        print(f"Final score was: {str(GAME_LAYER.get_score()['finalScore'])}")

    except KeyboardInterrupt:  # End game session in case of ctrl c
        print(f"\nForce quit game: {GAME_LAYER.game_state.game_id}")
        GAME_LAYER.end_game()

    except Exception as e:  # Catching generic exceptions
        GAME_LAYER.end_game()
        raise (e)


# Modify map numbers to satisfy custom identifiers
def preprocess_map():
    print("Preprocessing map...")
    state = GAME_LAYER.game_state
    for residence in state.residences:
        x, y = residence.X, residence.Y
        state.map[x][y] = POS_RESIDENCE
    for utility in state.utilities:
        x, y = utility.X, utility.Y
        state.map[x][y] = POS_UTILITY


def take_turn():
    state = GAME_LAYER.game_state

    strategy(state)

    for message in GAME_LAYER.game_state.messages:
        print(message)
    for error in GAME_LAYER.game_state.errors:
        print("Error: " + error)


def strategy(state):
    # Take one of the following actions in order of priority #
    # if state.turn > 650:
    #     if build_residence(state):
    #         pass
    #     elif regulate_temperature(state):
    #         pass
    #     elif residence_maintenance(state):
    #         pass
    #     elif place_residence(state):
    #         pass
    #     else:
    #         GAME_LAYER.wait()
    if residence_maintenance(state):
        pass
    elif residence_upgrade(state):
        pass
    elif regulate_temperature(state):
        pass
    elif build_residence(state):
        pass
    elif place_utility(state):
        pass
    elif place_residence(state):
        pass
    else:
        GAME_LAYER.wait()


# Maintain a residence in need of maintenance
def residence_maintenance(state):
    if len(state.residences) < 1:
        return False

    residence = min(state.residences, key=lambda x: x.health)
    blueprint = GAME_LAYER.get_residence_blueprint(residence.building_name)
    if residence.health < MAINTENANCE_THRESHOLD and state.funds > blueprint.maintenance_cost:
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

            if abs(residence.temperature - 21) >= 1.5:
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
    # if state.total_co2 >= CO2_MAX:
    #     return False

    residence = _choose_residence(state)
    if (
        residence
        and state.housing_queue >= 10
        # and state.current_temp >= state.max_temp * 0.75 # Don't build when it's cold outside
    ):
        x, y = best_residence_location(state)
        if x < 0 or y < 0:
            print('No good location to place residence, returning...')
            return False

        state.map[x][y] = POS_RESIDENCE
        GAME_LAYER.place_foundation((x, y), residence.building_name)
        return True


def place_utility(state):
    # Alternate between utility and residence
    if (len(state.utilities) + len(state.residences)) % 5:
        return False

    utility = _choose_utility(state)
    if utility and state.funds > utility.cost:
        x, y = best_utility_location(state)
        if x < 0 or y < 0:
            return False

        state.map[x][y] = POS_UTILITY
        GAME_LAYER.place_foundation((x, y), utility.building_name)
        return True


def _choose_utility(state):
    available_utilities = state.available_utility_buildings
    # Cost is only found on blueprint
    utility_blueprints = [
        GAME_LAYER.get_utility_blueprint(utility.building_name)
        for utility in available_utilities
    ]

    # If mall is already placed, choose Park
    if "Mall" in (x.building_name for x in state.utilities if x.building_name):
        utility = GAME_LAYER.get_utility_blueprint("Park")
    else:
        utility = GAME_LAYER.get_utility_blueprint("Mall")

    if state.funds > utility.cost * 1.1:
        return utility


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
    # return _eco_happiness_upgrades(state, residence)


def _choose_all_upgrades(state, residence):
    for upgrade in sorted(state.available_upgrades, key=lambda x: x.cost):
        if state.funds > upgrade.cost and upgrade.name not in residence.effects:
            return upgrade


def _eco_happiness_upgrades(state, residence):
    if regulator := _choose_upgrades(state, residence, ["Regulator"]):
        return regulator
    elif state.total_co2 >= CO2_LIMIT or state.funds > FUNDS_LOW:
        return _choose_upgrades(state, residence, ["Charger", "Playground"])


def _choose_upgrades(state, residence, upgrades):
    for upgrade in sorted(
        (
            x
            for x in state.available_upgrades
            if x.name in upgrades and x.name not in residence.effects
        ),
        key=lambda x: x.cost,
    ):
        if state.funds > upgrade.cost:
            return upgrade


def _cheapest_upgrade(state, residence):
    upgrade = min(state.available_upgrades, key=lambda x: x.cost)
    if state.funds > upgrade.cost and upgrade.name not in residence.effects:
        return upgrade


def _choose_residence(state):
    # TODO: Decision tree for choosing the right residence, based on funds, map condition, etc.
    # if state.turn > 650:
    #     residence = min(state.available_residence_buildings, key=lambda x: x.cost)
    #     if state.funds > residence.cost:
    #         return residence

    # if len(state.residences) % 2:
    #     residence = sorted(state.available_residence_buildings, key=lambda x: x.cost, reverse=True)[1]
    #     if state.funds > residence.cost:
    #         return residence
    # if state.turn > 550:
    # residence = sorted(state.available_residence_buildings, key=lambda x: x.cost, reverse=True)[1]
    # else:
    if len(state.residences) > 5:
        residence = sorted(state.available_residence_buildings, key=lambda x: x.cost, reverse=True)[1]
    else:
        residence = max(state.available_residence_buildings, key=lambda x: x.cost)
    if state.funds > residence.cost:
        return residence
    # feasible_buildings = [
    #     x
    #     for x in state.available_residence_buildings
    #     if x.release_tick <= state.turn and state.funds > x.cost
    # ]
    # if feasible_buildings and max_total_maintenance_cost(
    #     state
    # ) <= state.funds - 5 * min_total_income(state):
    #     if state.total_co2 < CO2_LIMIT:
    #         if state.funds < FUNDS_LOW and len(state.residences) > 0:
    #             return False
    #         elif state.funds < FUNDS_MED:
    #             # Maximize population
    #             return max(
    #                 [
    #                     x
    #                     for x in feasible_buildings
    #                     if len(
    #                         [
    #                             y
    #                             for y in state.residences
    #                             if x.building_name == y.building_name
    #                         ]
    #                     )
    #                     < 4
    #                 ],
    #                 key=lambda x: x.max_pop,
    #                 default=None,
    #             )
    #         else:
    #             # Maximize happiness
    #             return max(
    #                 feasible_buildings, key=lambda x: x.max_happiness * x.max_pop
    #             )
    #     else:
    #         # Minimize co2
    #         return min(feasible_buildings, key=lambda x: x.co2_cost + x.max_pop * 0.03)


# The current maximum maintenance cost (i.e. excluding any upgrades)
def max_total_maintenance_cost(state):
    return sum(
        GAME_LAYER.get_blueprint(x.building_name).maintenance_cost
        for x in state.residences
    )


# The current minimum total income (i.e. excluding any upgrades)
def min_total_income(state):
    return sum(
        GAME_LAYER.get_blueprint(x.building_name).income_per_pop
        * GAME_LAYER.get_blueprint(x.building_name).max_pop
        for x in state.residences
    )


if __name__ == "__main__":
    main()
