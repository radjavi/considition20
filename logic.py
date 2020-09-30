from collections import defaultdict
from constants import *


def best_residence_location(state):
    scores = defaultdict(int)
    available = available_map_slots(state)
    for x1, y1 in available:
        scores[(x1, y1)] = 0
        for x2 in range(len(state.map)):
            for y2 in range(len(state.map)):
                d = manhattan_distance(x1, y1, x2, y2)
                if d > 0:
                    if state.map[x2][y2] == POS_EMPTY:
                        scores[(x1, y1)] += 1 / d
                    if state.map[x2][y2] == POS_UTILITY and d <= 3:
                        scores[(x1, y1)] += 100 / d
    if not scores:
        return (-1, -1)
    return max(scores, key=lambda x: scores[x])  # Key with max value


def best_utility_location(state):
    scores = defaultdict(int)
    available = available_map_slots(state)
    for x1, y1 in available:
        scores[(x1, y1)] = 0
        for x2 in range(len(state.map)):
            for y2 in range(len(state.map)):
                d = manhattan_distance(x1, y1, x2, y2)
                if d > 0 and state.map[x2][y2] in [
                    POS_EMPTY,
                    POS_RESIDENCE,
                ]:
                    scores[(x1, y1)] += 1 / d
                if d <= 3 and state.map[x2][y2] == 3:
                    scores[(x1, y1)] = -1e5
    if not scores:
        return (-1, -1)
    return max(scores, key=lambda x: scores[x])  # Key with max value


def available_map_slots(state):
    # Go through the map and find available slots
    return [
        (i, j)
        for i in range(len(state.map))
        for j in range(len(state.map))
        if state.map[i][j] == 0
    ]


def manhattan_distance(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)