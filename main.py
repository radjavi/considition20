import os
import sys
import math
from dotenv import load_dotenv

from constants import *
from game_layer import GameLayer
from logic import (
    best_residence_location,
    best_utility_location,
    residence_heuristic_score,
    calculate_energy_need,
    nr_ticks_left,
)

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
        print("-----------")
        print("Total happiness: ", int(GAME_LAYER.game_state.total_happiness))
        print("Total CO2: ", int(GAME_LAYER.game_state.total_co2))
        print("-----------")
        print("Final score was: " + str(GAME_LAYER.get_score()["finalScore"]))
    except KeyboardInterrupt:  # End game session in case of exceptions
        print(f"\nForce quit game: {GAME_LAYER.game_state.game_id}")
        GAME_LAYER.end_game()
    except Exception as e:  # Catching generic exceptions
        GAME_LAYER.end_game()
        raise (e)


# Modify map numbers to satisfy custom identifiers
def preprocess_map():
    """Preproccess the map, if there are any buildings or utilties already instantiated
    add them to our GameState map.
    """
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
    """Cleans the map"""
    print("Cleaning up map...")
    state = GAME_LAYER.game_state
    if len(state.residences) > 0:
        for residence in state.residences:
            GAME_LAYER.demolish((residence.X, residence.Y))
    else:
        print("Nothing to clean up.")


def take_turn():
    """Takes a turn"""
    state = GAME_LAYER.game_state
    print("Current score:", state.current_score)

    strategy(state)

    for message in GAME_LAYER.game_state.messages:
        print(message)
    for error in GAME_LAYER.game_state.errors:
        print("Error: " + error)


def strategy(state):
    """Main logic/strategy for game plan.

    Args:
        state (GameState) - The current game state
    """
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


def residence_maintenance(state):
    """Maintain a residence in need of maintenance

    Args:
        state (GameState) - The current game state
    """
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


def regulate_temperature(state):
    """Regulate the temperature of a residence if it's too low or high

    Args:
        state (GameState) - The current game state

    Returns:
        Bool
    """
    if len(state.residences) < 1 or state.turn < 2:
        return False

    if state.funds > FUNDS_MIN:
        residences = sorted(
            state.residences,
            key=lambda x: abs(
                calculate_energy_need(
                    state, x, GAME_LAYER.get_residence_blueprint(x.building_name)
                )
                - x.requested_energy_in
            ),
            reverse=True,
        )
        for residence in residences:
            if residence.build_progress >= 100:
                blueprint = blueprint = GAME_LAYER.get_residence_blueprint(
                    residence.building_name
                )
                energy = calculate_energy_need(state, residence, blueprint)

                if abs(energy - residence.requested_energy_in) >= ENERGY_DIFF_LIMIT:
                    GAME_LAYER.adjust_energy_level((residence.X, residence.Y), energy)
                    return True


def perform_construction(state):
    """Perform construction on a residence or utility that is not finished

    Args:
        state (GameState) - The current game state

    Returns:
        Bool
    """
    for residence in state.residences:
        if residence.build_progress < 100:
            GAME_LAYER.build((residence.X, residence.Y))
            return True

    for utility in state.utilities:
        if utility.build_progress < 100:
            GAME_LAYER.build((utility.X, utility.Y))
            return True


def place_residence(state):
    """Places a new residence on the map at an available spot

    Args:
        state (GameState) - The current game state

    Returns:
        Bool
    """
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
    """Places a new utility on the map at an available spot

    Args:
        state (GameState) - The current game state

    Returns:
        Bool
    """
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
    """Chooses the most optimal utility to place

    Args:
        state (GameState) - The current game state

    Returns:
        BlueprintUtilityBuilding - The most optimal utility
    """
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
    """Checks if the building has a regulator and buys one if needed

    Args:
        state (GameState) - The current game state

    Returns:
        Bool
    """
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
    """Chooses and buys a upgrade for a residence if needed

    Args:
        state (GameState) - The current game state

    Returns:
        Bool
    """
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
    """
    Args:
        state (GameState) - The current game state
        residence (BlueprintResidenceBuilding) - The residence blueprint

    Returns:
        Upgrade - The upgrade
    """
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
    return _optimal_residence(state, _feasible_residences(state))


def _feasible_residences(state):
    return [
        x for x in state.available_residence_buildings if x.release_tick <= state.turn
    ]


def _optimal_residence(state, feasible_residences):
    """Choose the building that potentially maximizes the final score

    Args:
        state (GameState) - The current game state
        feasible_residences ([BlueprintResidenceBuilding]) - List of residence blueprints

    Returns:
        BlueprintResidenceBuilding - The most optimal building
    """
    current_residences_heuristic = sum(
        [
            residence_heuristic_score(
                state, GAME_LAYER.get_blueprint(y.building_name), nr_ticks_left(state)
            )
            for y in state.residences
        ]
    )
    estimated_final_score = (
        lambda x: state.current_score
        + current_residences_heuristic
        + residence_heuristic_score(
            state, x, nr_ticks_left(state) - math.ceil(100 / x.build_speed)
        )
    )
    return max(
        [x for x in feasible_residences if estimated_final_score(x) > state.max_score],
        key=estimated_final_score,
        default=None,
    )


if __name__ == "__main__":
    main()
