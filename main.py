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
    utility_heuristic_score,
    calculate_energy_need,
    nr_ticks_left,
)

load_dotenv()
API_KEY = os.getenv("API_KEY")

# The different map names can be found on considition.com/rules
# Map name taken as command line argument.
# If left empty, the map "training1" will be selected.
map_name = sys.argv[1] if len(sys.argv) > 1 else "training1"
VERBOSE = sys.argv[2] if len(sys.argv) > 2 else False

GAME_LAYER: GameLayer = GameLayer(API_KEY)


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
        if VERBOSE:
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
    """Preproccess the map, if there are any buildings or utilties already
    instantiated add them to our GameState map.
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
    strategy(state)

    _score = str(int(state.current_score))
    for message in GAME_LAYER.game_state.messages:
        print(f"[{_score}]: ", message)
    for error in GAME_LAYER.game_state.errors:
        print(f"[{_score}]: ", error)


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
    elif place_building(state):
        pass
    # elif place_residence(state):
    #     pass
    # elif place_utility(state):
    #     pass
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
    """Regulate the temperature of a residence

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
            key=lambda residence: abs(
                calculate_energy_need(
                    state,
                    residence,
                    GAME_LAYER.get_residence_blueprint(residence.building_name),
                )
                - residence.requested_energy_in
            ),
            reverse=True,
        )
        for residence in residences:
            if residence.build_progress == 100:
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


def place_building(state):
    """Places a new building (residence or utility) on the map at an available spot

    Args:
        state (GameState) - The current game state

    Returns:
        Bool
    """
    residence, residence_score = _choose_residence(state)
    utility, utility_score = _choose_utility(state)
    # print(state.max_estimated_score, residence_score, utility_score)
    # print(
    #     current_estimated_final_score(
    #         state, len(set(x.building_name for x in state.residences))
    #     )
    # )

    if residence and residence_score >= utility_score:
        place_residence(state, residence, residence_score)
    elif utility:
        place_utility(state, utility, utility_score)


def place_residence(state, residence, residence_score):
    """Places a new residence on the map at an available spot

    Args:
        state (GameState) - The current game state
        residence (BlueprintResidenceBuilding) - The residence to place
        residence_score (number) - The estimated final score including the residence

    Returns:
        Bool
    """
    if (
        residence
        and state.funds - residence.cost >= FUNDS_MIN
        and state.queue_happiness < 20
    ):
        x, y = best_residence_location(state)
        if x < 0 or y < 0:
            return False

        state.map[x][y] = POS_RESIDENCE
        state.max_estimated_score = residence_score
        GAME_LAYER.place_foundation((x, y), residence.building_name)
        return True


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
    residence, score = None, 0
    for r in feasible_residences:
        current_distinct_residences = set(x.building_name for x in state.residences)
        nr_distinct_residences = len(current_distinct_residences) + (
            1 if r.building_name not in current_distinct_residences else 0
        )
        estimated_final_score = current_estimated_final_score(
            state, nr_distinct_residences
        ) + residence_heuristic_score(  # Contribution from new residence
            state,
            r,
            nr_ticks_left(state) - math.ceil(100 / r.build_speed) - 20,
            nr_distinct_residences,
        )
        if estimated_final_score > score:
            residence, score = r, estimated_final_score

    if residence and score > 100:
        return residence, score
    else:
        return None, 0


def place_utility(state, utility, utility_score):
    """Places a new utility on the map at an available spot

    Args:
        state (GameState) - The current game state
        utility (BlueprintUtilityBuilding) - The utility to place
        utility_score (number) - The estimated final score including the utility

    Returns:
        Bool
    """
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
        state.max_estimated_score = utility_score
        GAME_LAYER.place_foundation((x, y), utility.building_name)
        return True


def _choose_utility(state):
    """Chooses the most optimal utility to place

    Args:
        state (GameState) - The current game state

    Returns:
        BlueprintUtilityBuilding - The most optimal utility
    """
    return _optimal_utility(state, _feasible_utilities(state))


def _feasible_utilities(state):
    return [
        x for x in state.available_utility_buildings if x.release_tick <= state.turn
    ]


def _optimal_utility(state, feasible_utilities):
    """Choose the utility that potentially maximizes the final score

    Args:
        state (GameState) - The current game state
        feasible_utilities ([BlueprintResidenceBuilding]) - List of utility blueprints

    Returns:
        BlueprintUtilityBuilding - The most optimal utility
    """
    utility, score = None, 0
    for u in feasible_utilities:
        X, Y = best_utility_location(state, u.building_name)
        if X < 0 or Y < 0:
            continue
        nr_distinct_residences = len(set(x.building_name for x in state.residences))
        estimated_final_score = current_estimated_final_score(
            state, nr_distinct_residences
        ) + utility_heuristic_score(  # Contribution from new utility
            state,
            u,
            nr_ticks_left(state) - math.ceil(100 / u.build_speed) - 20,
            X,
            Y,
        )
        if estimated_final_score > score:
            utility, score = u, estimated_final_score

    if utility and score > 100:
        return utility, score
    else:
        return None, 0


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
        if upgrade := _choose_upgrade(state, residence):
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


def current_estimated_final_score(state, nr_distinct_residences):
    # Contribution from current residences
    current_residences_heuristic = sum(
        [
            residence_heuristic_score(
                state,
                GAME_LAYER.get_blueprint(x.building_name),
                nr_ticks_left(state),
                nr_distinct_residences,
            )
            for x in state.residences
        ]
    )
    # Contribution from current utilities
    current_utilities_heuristic = sum(
        [
            utility_heuristic_score(
                state,
                GAME_LAYER.get_blueprint(y.building_name),
                nr_ticks_left(state),
                y.X,
                y.Y,
            )
            for y in state.utilities
        ]
    )
    return (
        state.current_score + current_residences_heuristic + current_utilities_heuristic
    )


if __name__ == "__main__":
    main()
