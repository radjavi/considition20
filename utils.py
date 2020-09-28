from collections import defaultdict


def calc_best_utility_location(state, available_slots):
    score = defaultdict(int)
    for x, y in available_slots:
        try:
            if state.map[x + 1][y] == 2:
                score[(x, y)] = score[(x, y)] + 1
        except IndexError:
            pass
        try:
            if state.map[x - 1][y] == 2:
                score[(x, y)] = score[(x, y)] + 1
        except IndexError:
            pass
        try:
            if state.map[x][y + 1] == 2:
                score[(x, y)] = score[(x, y)] + 1
        except IndexError:
            pass
        try:
            if state.map[x][y - 1] == 2:
                score[(x, y)] = score[(x, y)] + 1
        except IndexError:
            pass
        try:
            if state.map[x - 1][y - 1] == 2:
                score[(x, y)] = score[(x, y)] + 1
        except IndexError:
            pass
        try:
            if state.map[x + 1][y + 1] == 2:
                score[(x, y)] = score[(x, y)] + 1
        except IndexError:
            pass
        try:
            if state.map[x - 1][y + 1] == 2:
                score[(x, y)] = score[(x, y)] + 1
        except IndexError:
            pass
        try:
            if state.map[x + 1][y - 1] == 2:
                score[(x, y)] = score[(x, y)] + 1
        except IndexError:
            pass
        try:
            if state.map[x + 1][y] == 3:
                score[(x, y)] = 0
                break
        except IndexError:
            pass
        try:
            if state.map[x - 1][y] == 3:
                score[(x, y)] = 0
                break
        except IndexError:
            pass
        try:
            if state.map[x][y + 1] == 3:
                score[(x, y)] = 0
                break
        except IndexError:
            pass
        try:
            if state.map[x][y - 1] == 3:
                score[(x, y)] = 0
                break
        except IndexError:
            pass
        try:
            if state.map[x - 1][y - 1] == 3:
                score[(x, y)] = 0
                break
        except IndexError:
            pass
        try:
            if state.map[x + 1][y + 1] == 3:
                score[(x, y)] = 0
                break
        except IndexError:
            pass
        try:
            if state.map[x - 1][y + 1] == 3:
                score[(x, y)] = 0
                break
        except IndexError:
            pass
        try:
            if state.map[x + 1][y - 1] == 3:
                score[(x, y)] = 0
                break
        except IndexError:
            pass

    return score
