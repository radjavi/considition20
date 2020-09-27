import api
from game_layer import GameLayer
import sys

api_key = "af79a1fd-d071-4109-8776-a31b815057ad"
# The different map names can be found on considition.com/rules
# Map name taken as command line argument. 
# If left empty, the map "training1" will be selected.
map_name = sys.argv[1] if len(sys.argv) > 1 else "training1"

game_layer: GameLayer = GameLayer(api_key)


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
    except: # End game session in case of exceptions
        print("\nEnding game: ", game_layer.game_state.game_id)
        game_layer.end_game()


def take_turn():
    # TODO Implement your artificial intelligence here.
    # TODO Take one action per turn until the game ends.
    # TODO The following is a short example of how to use the StarterKit

    state = game_layer.game_state
    if len(state.residences) < 1:
        for i in range(len(state.map)):
            for j in range(len(state.map)):
                if state.map[i][j] == 0:
                    x = i
                    y = j
                    break
        game_layer.place_foundation((x, y), game_layer.game_state.available_residence_buildings[0].building_name)
    else:
        the_only_residence = state.residences[0]
        if the_only_residence.build_progress < 100:
            game_layer.build((the_only_residence.X, the_only_residence.Y))
        elif the_only_residence.health < 50:
            game_layer.maintenance((the_only_residence.X, the_only_residence.Y))
        elif the_only_residence.temperature < 18:
            blueprint = game_layer.get_residence_blueprint(the_only_residence.building_name)
            energy = blueprint.base_energy_need + 0.5 \
                     + (the_only_residence.temperature - state.current_temp) * blueprint.emissivity / 1 \
                     - the_only_residence.current_pop * 0.04
            game_layer.adjust_energy_level((the_only_residence.X, the_only_residence.Y), energy)
        elif the_only_residence.temperature > 24:
            blueprint = game_layer.get_residence_blueprint(the_only_residence.building_name)
            energy = blueprint.base_energy_need - 0.5 \
                     + (the_only_residence.temperature - state.current_temp) * blueprint.emissivity / 1 \
                     - the_only_residence.current_pop * 0.04
            game_layer.adjust_energy_level((the_only_residence.X, the_only_residence.Y), energy)
        elif state.available_upgrades[0].name not in the_only_residence.effects:
            game_layer.buy_upgrade((the_only_residence.X, the_only_residence.Y), state.available_upgrades[0].name)
        else:
            game_layer.wait()
    for message in game_layer.game_state.messages:
        print(message)
    for error in game_layer.game_state.errors:
        print("Error: " + error)


if __name__ == "__main__":
    main()
