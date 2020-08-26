# StarterKit Python Considition 2020
This is the StarterKit for Considition 2020, a help to get going as quickly as possible with the competition. The StarterKit contains four main parts.

 - **The Main Program:** This is where you implement your solution. There is already an example solution implemented that works out of the box, but you will have to develop it further to get a better score.
 - **The Game Layer:** A wrapper between the API and the Main Program. Helps you with formatting the input to the API and keep an updated game state.
 - **The API:** A representation of the REST-API that the game is played with. Can be used directly or through the Game Layer.
 - **The Game State:** A representation of the Game State and the information about the current game.

Each part us described in greater detail below. The competition itself is also described on [Considition.com/rules](considition.com/rules).

# Installation and running
Run *main.py*

# Main Program
The Main Program is a simple loop. Each run of the program does the following:
 - Create a new game
 - Start the game
 - Take 700 actions
	- This is where you can implement your solution. Depending on the current Game State, take actions that maximize your final score.
 - Print the final score
# Game Layer
The game layer has all the functions you need to play the game.

**Game Setup**
- **New Game** Create a new game and get the *Game Info*.
- **Start Game** Start an already created game and get the initial *Game State*.
- **End Game** End a started game prematurely. Since there is a limit on how many games can be active at the same time for each team, you might have to use this to free up slots.
- **Score** Get the score for a finished game. The final turn of the game has to have happened for the score to be available.
- **Game Info** This can be used to get the *Game Info* of an already started game, for example if you want to resume an ongoing game after making changes.
- **Game State** This can be used to get the current *Game State* of an ongoing game.

**Actions**
Each Action returns an updated *Game State*
- **Place Foundation** Places a new building on a free spot on the map. Is used both for *Residences* and *Utility Buildings*. A building must be in either the *Available Residences* or *Available Utilities* and the current *Turn* has to be at least equal to the buildings *Release Tick* for it to be placed. The building has to be constructed before it has any effect on the game.
- **Build** Builds an already placed building. A building is finished when its *Build Progess* reaches 100.
- **Demolish** Demolishes a building. If a building has the attribute *Can Be Demolished* set to false, the demolish action will have no effect on that building.
- **Buy Upgrade** Buys and activates an upgrade for a *Residence*. If the building is already affected by the *Effect* of the upgrade, this will have no effect.
- **Maintenance** Repairs a *Residence*, resetting its *Health* to 100.
- **Adjust Energy** Sets the *Requested Energy In* for a *Residence* to the specified value. This is used to control the temperature of a building and costs **150 Funds** each time.

**Helpers**
- **Get Blueprint** Returns a blueprint matching the name of a building. This is useful to look up the static information of a building. There are variants for both *Residences* and *Utilities*.
- **Get Effect** Returns an effect matching that name. This is useful to look up what the effects on a building does.

# API
The definition of the API and what it returns can be found on [game.Considition.com/swagger](game.considition.com/swagger), or on [Considition.com/rules](considition.com/rules).
If you want to view the Replay of a game, use [visualizer.Considition.com/swagger](visualizer.considition.com).

# Game State
The Game State is split into two parts. One that is static per map, called *Game Info* and one that changes depending on your actions, called *Game State*.

**Game Info**
- **Game Id** The ID of the current game, useful if you want to view the replay or you have multiple games going at the same time.
- **Map Name** The name of the map you are currently playing on.
- **Max Turns** The maximum number of turns the game will go on for.
- **Max Temp** Approximately the highest temperature that can be reached on this map.
- **Min Temp** Approximately the lowest temperature that can be reached ont his map.
- **Map** An array of arrays of integers representing the map. Buildable slots are **0**'s. The map is not changing and thus will not reflect where buildings get placed.
- **Energy Levels** A list of the types of energy that can be purchased.
	- **Energy Threshold** If the amount of energy you buy is above this threshold, this is the type of energy you have to buy. This changes depending on the map.
	- **Cost per Mwh**  The cost to buy the energy. This is the same even among different maps.
	- **Co2 per Mwh** The amount of Co2 released when buying this energy. This is the same even among different maps.
- **Available Residences** The residences that can be bought on this map. Some buildings might not be available right away, depending on their *Release Tick*.
	- **Building Name** The name of the building.
	- **Cost** Cost in funds to buy the building.
	- **Co2 Cost** Cost in Co2 to buy the building.
	- **Base Energy Need** The lowest amount of energy needed to sustain the building. You always have to buy at least this much energy if able.
	- **Build Speed** How much the build progress is increased each time you call **Build** on this building.
	- **Type** A residence or a utility.
	- **Release Tick** When is the building available on this map.
	- **Max Pop** The maximum number of pops that can live in this residenceat the same time.
	- **Income Per Pop** The income you gain each turn for each pop in this residence.
	- **Emissivity** A multiplier on how much heat the residence loses to the environment depending on the difference in temperature.
	- **Maintenance Cost** How much it costs to do the **Maintenance** action on this residence.
	- **Decay Rate** How much *Health*, on average, this residence loses each turn.
	- **Max Happinesss** The maximum happiness each pop can generate each turn in this residence.
- **Available Utilities** The utility buildings that can be bought on this map. Some buildings might not be available right away, depending on their *Release Tick*.
	- **Building Name** The name of the building.
	- **Cost** Cost in funds to buy the building.
	- **Co2 Cost** Cost in Co2 to buy the building.
	- **Base Energy Need** The lowest amount of energy needed to sustain the building. You always have to buy at least this much energy if able.
	- **Build Speed** How much the build progress is increased each time you call **Build** on this building.
	- **Type** A residence or a utility.
	- **Release Tick** When is the building available on this map.
	- **Effects** A list of *Effect Name* which describes which effects this utility will produce when finished.
	- **Queue Increase** How much faster the *Queue* will grow, on average, if this utility is finished. Can only be applied once per type of utility.
- **Upgrades** A list of the upgrades that can be bought for residences.
	- **Name** The name of the upgrade. This is the name that you use when calling **Buy Upgrade**.
	- **Effect** The name of the effect this upgrade has.
	- **Cost** The cost in funds to purhcase this upgrade.
- **Effects** A list of all effects.
	- **Name** The name of the effect.
	- **Radius** If the effect has a radius of 0 it only affects the building it is on. The radius is measured in manhattan distance.
	- **Emissivity Multiplier** Changes the emissivity of the affected building.
	- **Decay Multiplier** Changes the decay rate of the affected building. 
	- **Building Income Increase** Changes the amount of funds generated by this building. Can be negative.
	- **Max Happiness Increase** Increases the maximum happiness each pop in this building can generate.
	- **Mwh Production** Generates free energy that is automatically removed from the *Requested Energy*
	- **Base Energy Mwh Increase** Increases the *Base Energy Need* of a building.
	- **Co2 per Pop Increase** Increases the amount of Co2 generated by each pop in this building. Can be negative.
	- **Decay Increase** A flat increase in the decay rate. Is applied before the **Decay Multiplier**.

**Game State**
-  **Turn** The current turn of the game.
- **Funds** The amount of funds available to purchase energy, buildings, upgrades and take actions.
- **Total Co2** The total amount of Co2 generated during the game. This is used to help calculate your score.
- **Total Happinesss** The total amount of happiness generated during the game. This is used to help calculate your score.
- **Current Temp** The current outdoor temperature.
- **Queue Happiness** How happy the pops in the queue are. Keep the queue short to make them happier.
- **Housing Queue** How many pops are currently in the queue.
- **Residences** The built residences. On some maps there are already pre-constructed residences when the map starts.
	- **Building Name** The name of the building. This matches the name in *Available Buildings* and in *Get Blueprint*.
	- **Position X** The buildings x-position on the map.
	- **Position Y** The buildings y-position on the map.
	- **Effective Energy In** How much energy the building receives. This can differ from the *Requested Energy In* if you can't afford to purchase all your energy.
	- **Build Progress** How close to finished the building is. At 100 the building is done.
	- **Can Be Demolished** If the building can be demolished or not.
	- **Effects** A list of *Effect Name* which tells which effects are currently active.
	- **Current Pop** The number of pops currently living in the residence.
	- **Temperature** The indoor temperature of the residence.
	- **Requested Energy In** The energy this residence wants. Can be changed by calling **Adjust Energy**.
	- **Happiness Per Tick Per Pop** The amount of happiness each pop generate on each turn. If the happiness is too low, pops will start to move out.
	- **Health** The current health of the building. If it's too low the pops will start to become unhappy.
- **Utilities** The built utilities. On some maps there are already pre-constructed utilities when the map starts.
	- **Building Name** The name of the building. This matches the name in *Available Buildings* and in *Get Blueprint*.
	- **Position X** The buildings x-position on the map.
	- **Position Y** The buildings y-position on the map.
	- **Effective Energy In** How much energy the building receives. This can differ from the *Base Energy Need* if you can't afford to purchase all your energy.
	- **Build Progress** How close to finished the building is. At 100 the building is done.
	- **Can Be Demolished** If the building can be demolished or not.
	- **Effects** A list of *Effect Name* which tells which effects are currently active.
