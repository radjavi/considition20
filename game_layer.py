from typing import Tuple

import api
from game_state import GameState


class GameLayer:
    def __init__(self, api_key):
        self.game_state: GameState = None
        self.api_key: str = api_key
    
    def new_game(self, map_name: str = "training0"):
        """
        Create a new game.
        """
        if map_name:
            game_options = {"mapName": map_name}
        else:
            game_options = ""    
        
        self.game_state = GameState(api.new_game(self.api_key, game_options))

    def end_game(self):
        """
        End the current game
        """
        api.end_game(self.api_key, self.game_state.game_id)

    def start_game(self):
        """
        Starts the game.
        """
        self.game_state.update_state(api.start_game(self.api_key, self.game_state.game_id))

    def place_foundation(self, pos: Tuple[int, int], building_name: str):
        """
        Places a building with name building_name at the given position.
        :param pos: (int, int) - the position
        :param building_name: string - the name, check available_residence_buildings or available_residence_utilities for which buildings are available
        """
        position = {'X': pos[0], 'Y': pos[1]}
        foundation = {'Position': position, 'BuildingName': building_name}
        self.game_state.update_state(api.place_foundation(self.api_key, foundation, self.game_state.game_id))

    def build(self, pos: Tuple[int, int]):
        """
        Continues the construction of a building at the given position.
        :param pos: (int, int) - the position
        """
        position = {'position': {"X": pos[0], "Y": pos[1]}}
        self.game_state.update_state(api.build(self.api_key, position, self.game_state.game_id))

    def maintenance(self, pos: Tuple[int, int]):
        """
        Performs maintenance on the building at the given position.
        :param pos: (int, int) - the position
        """
        position = {'position': {"x": pos[0], "y": pos[1]}}
        self.game_state.update_state(api.maintenance(self.api_key, position, self.game_state.game_id))

    def demolish(self, pos: Tuple[int, int]):
        """
        Demolishes the building at the given position.
        :param pos: (int, int) - the position
        """
        position = {'position': {"x": pos[0], "y": pos[1]}}
        self.game_state.update_state(api.demolish(self.api_key, position, self.game_state.game_id))

    def adjust_energy_level(self, pos: Tuple[int, int], value: float):
        """
        Adjusts the requested energy to value on the building at the given position.
        :param pos: (int, int) - the position
        :param value: float - the new requested value
        """
        position = {"x": pos[0], "y": pos[1]}
        self.game_state.update_state(api.adjust_energy(self.api_key, {"position": position, "value": value}, self.game_state.game_id))

    def wait(self):
        """
        Advances the game by one turn.
        """
        self.game_state.update_state(api.wait(self.api_key, self.game_state.game_id))

    def buy_upgrade(self, pos: Tuple[int, int], upgrade: str):
        """
        Adds the specified upgrade to the building at the given position.
        You can find the available upgrades in available_upgrades
        Parameters
        ----------
        :param pos: (int, int) - the position
        :param upgrade: string - the upgrade to purchase
        """
        position = {"x": pos[0], "y": pos[1]}
        self.game_state.update_state(api.buy_upgrades(self.api_key, {"position": position, "upgradeAction": upgrade}, self.game_state.game_id))

    def get_score(self):
        """
        Gets the score for the game.
        :return An object with partial and total scores.
        """
        return api.get_score(self.api_key, self.game_state.game_id)

    def get_game_info(self, game_id: str):
        """
        Gets the game info of an already ongoing game and updates the state.
        :param game_id: string - the id of the game to get info about.
        """
        self.game_state = GameState(api.get_game_info(self.api_key, game_id))

    def get_game_state(self, game_id: str):
        """
        Gets the game state of an already ongoing game and updates the state. Can be used to resume a game.
        :param game_id: string - the id of the game to get the state.
        """
        self.game_state.update_state(api.get_game_state(self.api_key, game_id))

    def get_blueprint(self, building_name: str):
        """
        Returns the matching blueprint for a building
        :param building_name: string - the name of the building to get a blueprint.
        """
        res_blueprint = self.get_residence_blueprint(building_name)
        if res_blueprint:
            return res_blueprint
        return self.get_utility_blueprint(building_name)

    def get_residence_blueprint(self, building_name: str):
        """
        Returns the matching blueprint for a residence
        :param building_name: string - the name of the building to get a blueprint.
        """
        for blueprint in self.game_state.available_residence_buildings:
            if blueprint.building_name == building_name:
                return blueprint
        return None

    def get_utility_blueprint(self, building_name: str):
        """
        Return the matching blueprint for a utility building
        :param building_name: string - the name of the building to get a blueprint.
        """
        for blueprint in self.game_state.available_utility_buildings:
            if blueprint.building_name == building_name:
                return blueprint
        return None

    def get_effect(self, effect_name: str):
        """
        Return the matching effect for an effect name.
        :param effect_name: string - the name of the effect to get.
        """
        for effect in self.game_state.effects:
            if effect.name == effect_name:
                return effect
        return None
