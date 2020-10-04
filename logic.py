from collections import defaultdict

from constants import *


def nr_ticks_left(state):
    return state.max_turns - state.turn - 1


def building_heuristic_score(state, building, nr_ticks):
    """Logic for estimating a new building's contribution to the score at the end of the game

    Args:
        state (GameState) - The current game state
        building (BlueprintResidenceBuilding) - The new building blueprint
        nr_ticks (int) - Number of ticks the building will contribute to the score

    Returns:
        int - The chosen building's contribution to the final score
    """
    happiness = building_heuristic_happiness(state, building, nr_ticks)
    co2 = building_heuristic_co2(state, building, nr_ticks)
    return 15 * building.max_pop + 0.1 * happiness - co2


def building_heuristic_happiness(state, building, nr_ticks):
    return (
        (
            building.max_happiness
            + (
                building.max_happiness * 0.1
                if not any(
                    building.building_name == y.building_name for y in state.residences
                )
                else 0
            )
        )
        * building.max_pop
        * nr_ticks
    )


def building_heuristic_co2(state, building, nr_ticks):
    avg_map_temp = (state.max_temp + state.min_temp) / 2
    return (
        building.co2_cost
        + building.max_pop * CO2_PER_POP * nr_ticks
        + 0.15
        * (
            (
                (OPT_TEMP - avg_map_temp) * building.emissivity
                - DEGREES_PER_POP * building.max_pop
            )
            / DEGREES_PER_EXCESS_MWH
            + building.base_energy_need
        )
        * nr_ticks
    )


def calculate_energy_need(state, residence, blueprint):
    """Logic for determinating the energy need for a building

    Args:
        state (GameState) - The current game state
        residence (Residence) - The residence
        blueprint (BlueprintResidenceBuilding) - The building blueprint

    Returns:
        int - The energy needed
    """
    base_energy_need = (
        blueprint.base_energy_need + 1.8
        if "Charger" in residence.effects
        else blueprint.base_energy_need
    )
    energy_wanted = (
        OPT_TEMP
        - residence.temperature
        - DEGREES_PER_POP * residence.current_pop
        + (residence.temperature - state.current_temp) * blueprint.emissivity
    ) / DEGREES_PER_EXCESS_MWH + base_energy_need

    return max(energy_wanted, base_energy_need + 1e-2)


def best_residence_location(state):
    """Logic for determinating the best residence location based on the current game state

    Args:
        state (GameState) - The current game state

    Returns:
        (int, int) - x and y coordinates for the best residence location
    """
    scores = defaultdict(int)
    available = available_map_slots(state)
    for x1, y1 in available:
        scores[(x1, y1)] = 0
        for x2 in range(len(state.map)):
            for y2 in range(len(state.map)):
                d = manhattan_distance(x1, y1, x2, y2)
                if d > 0:
                    if d <= 3 and state.map[x2][y2] == POS_EMPTY:
                        scores[(x1, y1)] += 1 / d
                    if state.map[x2][y2] == POS_RESIDENCE:
                        scores[(x1, y1)] += 10 / d
                    if d <= 3 and state.map[x2][y2] == POS_MALL:
                        scores[(x1, y1)] += 100 / d
                    if d <= 2 and state.map[x2][y2] == POS_PARK:
                        scores[(x1, y1)] += 100 / d
                    if d <= 2 and state.map[x2][y2] == POS_WINDTURBINE:
                        scores[(x1, y1)] += 100 / d
    if not scores:
        return (-1, -1)
    return max(scores, key=lambda x: scores[x])  # Key with max value


def best_utility_location(state, building_name):
    """Logic for determinating the best utility location based on the current game state

    Args:
        state (GameState) - The current game state
        building_name (str) - The building name

    Returns:
        (int, int) - x and y coordinates for the best residence location
    """
    scores = defaultdict(int)
    available = available_map_slots(state)
    for x1, y1 in available:
        scores[(x1, y1)] = 0
        for x2 in range(len(state.map)):
            for y2 in range(len(state.map)):
                d = manhattan_distance(x1, y1, x2, y2)
                if d > 0:
                    if d <= 3 and state.map[x2][y2] == POS_EMPTY:
                        scores[(x1, y1)] += 1 / d
                    if (
                        d <= 3
                        and state.map[x2][y2] == POS_RESIDENCE
                        and building_name == "Mall"
                    ):
                        scores[(x1, y1)] += 100 / d
                    if (
                        d <= 2
                        and state.map[x2][y2] == POS_RESIDENCE
                        and (building_name == "Park" or building_name == "WindTurbine")
                    ):
                        scores[(x1, y1)] += 100 / d
                    if (  # Don't place in range of identical utility
                        d <= 3 * 2
                        and state.map[x2][y2] == POS_MALL
                        and building_name == "Mall"
                    ):
                        scores[(x1, y1)] = -1e5
                    if (  # Don't place in range of identical utility
                        d <= 2 * 2
                        and state.map[x2][y2] == POS_PARK
                        and building_name == "Park"
                    ):
                        scores[(x1, y1)] = -1e5
                    if (  # Don't place in range of identical utility
                        d <= 2 * 2
                        and state.map[x2][y2] == POS_WINDTURBINE
                        and building_name == "WindTurbine"
                    ):
                        scores[(x1, y1)] = -1e5
    if not scores:
        return (-1, -1)
    return max(scores, key=lambda x: scores[x])  # Key with max value


def available_map_slots(state):
    """Goes through the map and finds available slots

    Args:
        state (GameState) - The current game state

    Returns:
        [(int,int)] - A list of tuples containing ints indicating the available locations
    """
    # Go through the map and find available slots
    return [
        (i, j)
        for i in range(len(state.map))
        for j in range(len(state.map))
        if state.map[i][j] == 0
    ]


def manhattan_distance(x1, y1, x2, y2):
    """Calculates the manhattan distance"""
    return abs(x1 - x2) + abs(y1 - y2)
