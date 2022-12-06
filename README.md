# Fishing Assistant - Dragonflight
Fishing Assistant bot rewritten from scratch for Dragonflight. Cleaner codebase, lighter weight, more stable, more features.

# Table of Contents
- [Fishing Assistant - Dragonflight](#fishing-assistant---dragonflight)
- [Table of Contents](#table-of-contents)
- [Setup](#setup)
  - [Install Requirements](#install-requirements)
  - [Choosing an input method](#choosing-an-input-method)
  - [Setting up interception driver input](#setting-up-interception-driver-input)
  - [Setting up arduino hardware input](#setting-up-arduino-hardware-input)
  - [Script Settings](#script-settings)
    - [User Settings](#user-settings)
    - [Fishing](#fishing)
    - [Breaks](#breaks)
    - [Auto Vendor](#auto-vendor)
    - [Discord Webhook](#discord-webhook)
- [In-game Settings](#in-game-settings)
- [Running Script](#running-script)

# Setup
## Install Requirements
* Open cmd / terminal in current folder (`shift + right-click` -> `Open Powershell window here`)
* pip install -r requirements.txt (Only need to do this once.)

## Choosing an input method
* `virtual` - Can be used by just installing the requirements from above. Least safe method.
* `interception` - Input driver that needs to be installed to the system. Should be safer than `virtual`.
* * Some games / anti-cheats may block you from playing with this installed, like faceit.
* `arduino` - Hardware that can send input to the system that looks like a real hardware device (or your mouse if descriptors are changed.)
* * Not yet added.
* * Will require arduino leonardo, host shield, and usb hub (2 ports)

## Setting up interception driver input
* This isn't required but should be safer to use than `virtual` input. 
* * Optionally proceed with installation steps and change the `input_method` in settings.ini to `interception`
* Open cmd / terminal in `fishing_assistant\Interception\command line installer` (`shift + right-click` -> `Open Powershell window here`)
* * Run: `.\install-interception.exe /install`
* * Must reboot the computer/vm after.

## Setting up arduino hardware input
* Coming soon(tm)

## Script Settings
* Change appropriate user settings in `settings/settings.ini`

### User Settings
* * `debug = True` - Enables debug logging and images
* * `input_method = virtual` - Set input method (virtual/interception/arduino) 
* * * (safest: arduino > interception > virtual)

### Fishing
* * `fishing_hotkey = z` - In-game hotkey with your fishing ability.
* * `min_confidence = 0.50` - Confidence needed to find bobber. 
* * * Lower if it cant find the bobber.
* * * Higher if mouse moving to spots where the bobber isn't.
* * `timeout_threshold = 20`  - Timeout in seconds before casting new rod, if we didn't find a catch.
* * `dip_threshold = 7`  - amount of y pixels deviated from average before deciding the movement means there was a catch.
* * `bobber_image_name = bobber_blue.png` - Name of file for your bobber image
* * * You should update the bobber image to your own or it may not find the bobber very well.
* * * Make it similar to example templates in size / whats shown in the image.

### Breaks
* * `breaks_enabled = True` - Enable or disable taking breaks during while botting fishing.
* * `wow_path = C:\Program Files (x86)\World of Warcraft\_retail_\Wow.exe` - Path to your `World of Warcraft\_retail\Wow.exe`
* * `account_password = account_password_here` - The way the bot launches the game doesn't auto log you in so you need to save your password. It's only stored locally in this file.
* * * It expects you've already launched the game from wow_path and saved the account login.
* * * If you load the game from wow_path it should only require you to type your password and hit enter to login.

### Auto Vendor
* * `auto_vendor_enabled = True` - Enable or disable auto vendor feature
* * `mount_hotkey = f1` - Hotkey to get on vendor mount
* * `target_hotkey = f2` - Hotkey with `/target Gnimo` macro
* * `interact_hotkey = f3` - Hotkey bound to - in-game options -> Gameplay -> keybindings -> targetting -> interact with target

### Discord Webhook
* `discord_webhook_enabled = False` - Set to `True` to enable sending progress reports via webhook.
* * Must have a valid webhook url!
* `discord_webhook_url = webhook_url_goes_here` - Paste your discord webhook's url here.

# In-game Settings
* I don't think it should matter to much but in testing I had the preset graphics slider set to 1/lowest.

# Running Script
* Zoom all the way in, in game.
* Do a test fishing cast and make sure bobbers are near middle of game window.
* * Having debug enabled will show the area of interest window if you need help.
* It is beneficial to hide UI while fishing with `alt+z`
* Open cmd / terminal in current folder (`shift + right-click` -> `Open Powershell window here`)
* * Run this in terminal window: `python main.py`