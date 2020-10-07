from collections import defaultdict

from constants import *


def nr_ticks_left(state):
    return state.max_turns - state.turn - 1


def residence_heuristic_score(state, residence, nr_ticks, nr_distinct_residences):
    """Logic for estimating a residence's contribution to the score at the end of the game

    Args:
        state (GameState) - The current game state
        residence (BlueprintResidenceBuilding) - The building blueprint
        nr_ticks (int) - Number of ticks the building will contribute to the score
        nr_distinct_residences (int) - Number of distinct residences used for the happiness bonus

    Returns:
        int - The chosen building's contribution to the final score
    """
    happiness = residence_heuristic_happiness(
        state, residence, nr_ticks, nr_distinct_residences
    )
    co2 = residence_heuristic_co2(state, residence, nr_ticks)
    return 15 * residence.max_pop + 0.1 * happiness - co2


def residence_heuristic_happiness(state, residence, nr_ticks, nr_distinct_residences):
    return (
        (residence.max_happiness * (1 + 0.1 * nr_distinct_residences))
        * residence.max_pop
        * nr_ticks
    )


def residence_heuristic_co2(state, residence, nr_ticks):
    avg_map_temp = (state.max_temp + state.min_temp) / 2
    base_energy = residence.base_energy_need
    energy = max(
        (
            (OPT_TEMP - avg_map_temp) * residence.emissivity
            - DEGREES_PER_POP * residence.max_pop
        )
        / DEGREES_PER_EXCESS_MWH
        + base_energy,
        base_energy,
    )
    return (
        residence.co2_cost
        + residence.max_pop * CO2_PER_POP * nr_ticks
        + CO2_PER_KWH * energy * nr_ticks
    )


def utility_heuristic_score(state, utility, nr_ticks, x, y):
    """Logic for estimating a utility's contribution to the score at the end of the game

    Args:
        state (GameState) - The current game state
        utility (BlueprintUtilityBuilding) - The utility blueprint
        nr_ticks (int) - Number of ticks the utility will contribute to the score
        x (int) - The utility's X coordinate
        y (int) - The utility's Y coordinate

    Returns:
        int - The chosen utility's contribution to the final score
    """
    happiness = 0
    co2 = utility.co2_cost + utility.base_energy_need * nr_ticks

    radius = 3 if utility.building_name == "Mall" else 2
    for x2 in range(len(state.map)):
        for y2 in range(len(state.map)):
            d = manhattan_distance(x, y, x2, y2)
            residence_blueprint = residence_blueprint_at_pos(state, x2, y2)
            utility_blueprint = utility_blueprint_at_pos(state, x2, y2)
            max_pop = residence_blueprint.max_pop if residence_blueprint else 40
            if (
                d > 0
                and d <= radius
                and state.map[x2][y2] in [POS_EMPTY, POS_RESIDENCE]
            ):
                if utility.building_name == "Mall":
                    happiness += 0.12 * max_pop * nr_ticks
                if utility.building_name == "Park":
                    happiness += 0.11 * max_pop * nr_ticks
                    co2 -= 0.007 * max_pop
                if utility.building_name == "WindTurbine":
                    co2 -= CO2_PER_KWH * 3.4 * nr_ticks
            if (
                utility_blueprint
                and d > 0
                and d <= 2
                and (
                    (
                        utility.building_name in ["Mall", "Park"]
                        and utility_blueprint.building_name == "WindTurbine"
                    )
                    or (
                        utility_blueprint.building_name in ["Mall", "Park"]
                        and utility.building_name == "WindTurbine"
                    )
                )
            ):
                co2 -= CO2_PER_KWH * min(
                    3.4,
                    utility_blueprint.base_energy_need or 3.4,
                    utility.base_energy_need or 3.4,
                )

    return 0.1 * happiness - co2


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
    emissivity = (
        blueprint.emissivity * 0.6
        if "Insulation" in residence.effects
        else blueprint.emissivity
    )
    energy_wanted = (
        OPT_TEMP
        - residence.temperature
        - DEGREES_PER_POP * residence.current_pop
        + (residence.temperature - state.current_temp) * emissivity
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
                        scores[(x1, y1)] += 0.001
                    if (
                        d <= 3
                        and state.map[x2][y2] == POS_RESIDENCE
                        and building_name == "Mall"
                    ):
                        residence_blueprint = residence_blueprint_at_pos(state, x2, y2)
                        scores[(x1, y1)] += 0.1 * 0.12 * residence_blueprint.max_pop
                    if (
                        d <= 2
                        and state.map[x2][y2] == POS_RESIDENCE
                        and building_name == "Park"
                    ):
                        residence_blueprint = residence_blueprint_at_pos(state, x2, y2)
                        scores[(x1, y1)] += 0.007 * residence_blueprint.max_pop
                    if (
                        d <= 2
                        and state.map[x2][y2] == POS_RESIDENCE
                        and building_name == "WindTurbine"
                    ):
                        residence_blueprint = residence_blueprint_at_pos(state, x2, y2)
                        scores[(x1, y1)] += CO2_PER_KWH * min(
                            3.4, residence_blueprint.base_energy_need
                        )
                    if (
                        d <= 2
                        and state.map[x2][y2] in [POS_MALL, POS_PARK]
                        and building_name == "WindTurbine"
                    ):
                        utility_blueprint = utility_blueprint_at_pos(state, x2, y2)
                        scores[(x1, y1)] += CO2_PER_KWH * min(
                            3.4, utility_blueprint.base_energy_need
                        )
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


def residence_blueprint_at_pos(state, x, y):
    for residence in state.residences:
        if residence.X == x and residence.Y == y:
            return next(
                (
                    blueprint
                    for blueprint in state.available_residence_buildings
                    if blueprint.building_name == residence.building_name
                ),
                None,
            )


def utility_blueprint_at_pos(state, x, y):
    for utility in state.utilities:
        if utility.X == x and utility.Y == y:
            return next(
                (
                    blueprint
                    for blueprint in state.available_utility_buildings
                    if blueprint.building_name == utility.building_name
                ),
                None,
            )


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
