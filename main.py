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

game_layer: GameLayer = GameLayer(API_KEY)


def main():
    try:
        game_layer.new_game(map_name)
        print("Starting game: " + game_layer.game_state.game_id)
        print("Map:", map_name)
        game_layer.start_game()
        while game_layer.game_state.turn < game_layer.game_state.max_turns:
            take_turn()
        print("Done with game: " + game_layer.game_state.game_id)
        print("Final score was: " + str(game_layer.get_score()["finalScore"]))
    except KeyboardInterrupt:  # End game session in case of exceptions
        print(f"\nForce quit game: {game_layer.game_state.game_id}")
        game_layer.end_game()
    except Exception as e:  # Catching generic exceptions
        print(f"Error: {e}")
        game_layer.end_game()


def take_turn():
    state = game_layer.game_state

    # TODO: Make decisions #
    build_residences(state)
    # --- #

    for message in game_layer.game_state.messages:
        print(message)
    for error in game_layer.game_state.errors:
        print("Error: " + error)


def build_residences(state):
    pass


if __name__ == "__main__":
    main()