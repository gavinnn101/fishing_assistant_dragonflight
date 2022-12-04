# wow_fisher_df
Fishing bot for WoW Dragonflight


# Setup
# # Install Requirements
* Open cmd / terminal in current folder (`shift + right-click` -> `Open Powershell window here`)
* pip install -r requirements.txt (Only need to do this once.)

# # Script Settings
* Change settings in main.py
# # # User Settings
* * `DEBUG = True` - Enables debug logging and images
* * `INPUT_METHOD = 'virtual'` - Set input method (virtual/interception/arduino) 
* * * (safest: arduino > interception > virtual)
* * `FISHING_HOTKEY = 'z'` - In-game hotkey with your fishing ability.
* * `MIN_CONFIDENCE = 0.50` - Confidence needed to find bobber. 
* * * Lower if it cant find the bobber.
* * * Higher if mouse moving to spots where the bobber isn't.
* * `TIMEOUT_THRESHOLD = 20`  - Timeout in seconds before casting new rod, if we didn't find a catch.
* * `DIP_THRESHOLD = 7`  - amount of y pixels deviated from average before deciding the movement means there was a catch.
# # # Fishing Settings
* `template` - image of bobber to match against. 
* * Check images in repo for examples.
* * Adjust to area that you're fishing in.

# In-game Settings
* I don't think it should matter to much but in testing I had the preset graphics slider set to 1/lowest.


# Running Script
* Open cmd / terminal in current folder (`shift + right-click` -> `Open Powershell window here`)
* Zoom all the way in, in game.
* Do a test fishing cast and make sure bobbers are near middle of game window.
* Might be beneficial to hide UI while fishing with `alt+z`
* Run this in terminal window: `python3 main.py`