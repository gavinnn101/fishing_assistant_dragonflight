import aiohttp
import asyncio
import cv2 as cv
import numpy as np
import os
import random
import sys
import time
from datetime import datetime
from discord import Webhook, Embed, File
from loguru import logger
from mss import mss
from win32gui import FindWindow, GetWindowRect, GetClientRect

from modules.BreakHelper import BreakHelper
from modules.InputHelper import InputHelper
from modules.TSMWrapper import TSMWrapper
from utility.util import get_duration


class FishingBot():
    stopped = True
    """Class to handle in-game fishing automation."""
    def __init__(self, settings_helper, *args, **kwargs):
        # Initialize settings helper
        self.settings_helper = settings_helper
        # Get webhook url
        self.webhook_url = self.settings_helper.settings['webhook']['DISCORD_WEBHOOK_URL']
        # Get reaction time settings
        self.REACTION_TIME_RANGE = (
            self.settings_helper.settings['user'].getfloat('reaction_time_lower'),
            self.settings_helper.settings['user'].getfloat('reaction_time_upper')
            )
        # Initialize input helper
        self.input_helper = InputHelper(settings_helper=self.settings_helper)
        # Initialize Break handler
        self.break_helper = BreakHelper(settings_helper=self.settings_helper, input_helper=self.input_helper)
        self.breaks_enabled = self.settings_helper.settings['breaks'].getboolean('breaks_enabled')
        # Bobber template
        self.bobber_template_name = self.settings_helper.settings['fishing'].get('bobber_image_name')
        self.bobber_template_path = f'templates\\bobber_templates\\{self.bobber_template_name}'
        self.bobber_template = cv.imread(self.bobber_template_path, 0)
        self.w, self.h = self.bobber_template.shape[::-1]
        # Initialize fishing stats
        self.fish_caught = 0
        self.no_fish_casts = 0
        self.bait_used = 0
        self.rods_cast = 0
        self.DIP_THRESHOLD = self.settings_helper.settings['fishing'].getint('dip_threshold')
        self.time_since_bait = None
        # Initialize TSMWrapper for fish prices
        self.tsm = TSMWrapper(settings_helper=self.settings_helper)
        self.fish_map = {
            'scalebelly_mackerel': {
                'template': None,
                'loot_count': 0,
                'gold_earned': 0,
            },
            'temporal_dragonhead': {
                'template': None,
                'loot_count': 0,
                'gold_earned': 0,
            },
            'thousandbite_piranha': {
                'template': None,
                'loot_count': 0,
                'gold_earned': 0,
            },
            'islefin_dorado': {
                'template': None,
                'loot_count': 0,
                'gold_earned': 0,
            },
            'dull_spined_clam': {
                'template': None,
                'loot_count': 0,
                'gold_earned': 0,
            },
            'cerulean_spinefish': {
                'template': None,
                'loot_count': 0,
                'gold_earned': 0,
            },
            'aileron_seamoth': {
                'template': None,
                'loot_count': 0,
                'gold_earned': 0,
            },
            'copper_coin': {
                'template': None,
                'loot_count': 0,
                'gold_earned': 0,
            },
            'recipe_bottle': {
                'template': None,
                'loot_count': 0,
                'gold_earned': 0,
            }
        }
        # Set loot templates
        self.cache_loot_templates()
        # Set start time of bot
        self.start_time = datetime.now()
        # Start auto vendor timer if enabled
        self.auto_vendor_enabled = self.settings_helper.settings['vendor'].get('auto_vendor_enabled')
        if self.auto_vendor_enabled:
            self.vendor_time = self.start_time

        # Game Client Variables
        self.game_window_name = "World of Warcraft"
        self.game_window_class = "GxWindowClass"
        self.game_window_handle = None
        self.game_window_rect = None  # left, top, right, bottom
        self.fishing_area = None
        # Set Game window vars
        self.set_game_window_data()

        # Set log level
        if not settings_helper.settings['user'].getboolean('debug'):
            # Set log level to INFO
            logger.remove()
            logger.add(sys.stderr, level="INFO")


    def find_template(self,
                        screenshot, template,
                        scale_min: float = 0.8, scale_max: float = 1.4, scale_steps: int = 25
                    ):
        """Resizes template and finds the best match"""
        import imutils
        # screenshot w,h
        (tH, tW) = screenshot.shape[:2]

        # best match found
        best_conf = None
        best_loc = None
        best_scale = None

        # Loop over scale values to check for template
        for scale in np.linspace(scale_min, scale_max, scale_steps)[::-1]:  # start_scale, max_scale, total increments between start-max
            resized = imutils.resize(template, width = int(template.shape[1] * scale))
            # r = screenshot.shape[1] / float(resized.shape[1])  # Not used
            # Break if resized template is bigger than the screenshot. (shouldn't happen) 
            if resized.shape[0] > tH or resized.shape[1] > tW:
                break
            # Check template match results
            result = cv.matchTemplate(screenshot, resized, cv.TM_CCOEFF_NORMED)
            _, maxVal, _, maxLoc = cv.minMaxLoc(result)
            logger.debug(f"confidence: {maxVal} | location: {maxLoc} | scale: {scale}")
            # Assign new best values if needed
            if best_conf is None or maxVal > best_conf:
                best_conf = maxVal
                best_loc = maxLoc
                best_scale = scale
        # Return best match
        return (best_conf, best_loc, best_scale)



    def get_bobber_box(self, location):
        """Returns coordinates of box to watch around found bobber."""
        # Bobber coordinates
        top_left = location
        top_left = (top_left[0] - 20, top_left[1] - 20)  # position of box
        bottom_right = (top_left[0] + self.w + 40, top_left[1] + self.h + 20)  # size of box
        return (top_left, bottom_right)

    def get_loot_box(self, location):
        """Returns coordinates of box to watch for loot window."""
        # loot window coordinates
        top_left = location
        top_left = (top_left[0] - 20, top_left[1] - 20)  # position of box
        bottom_right = (top_left[0] + self.w + 100, top_left[1] + self.h + 50)  # size of box
        return (top_left, bottom_right)


    def check_for_loot_window(self, screenshot):
        # Use inRange to find pixels that are black (i.e. have a value of 0)
        mask = cv.inRange(screenshot, 0, 3)

        # Find the contours of the black pixels
        contours, _ = cv.findContours(mask, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
        
        # Draw a light colored box around the contours
        for contour in contours:
            x, y, w, h = cv.boundingRect(contour)
            logger.info(f"Countour width: {w}")
            if (w > 100):
                logger.debug(f"Found side with width: {w}")
                # Draw found side
                cv.rectangle(screenshot, (x, y), (x+w, y+h), (200, 200, 200), 2)
                return True
        return False


    # This function could probably be done in a separate thread since it takes a few seconds on slower machines/VMs.
    def count_loot(self, loot_box):
        logger.info("Tracking what loot we got")
        highest_fish, highest_conf, highest_loc, highest_scale = None, None, None, None
        start_time = datetime.now()
        # Get screen coordinates of bobber box
        box = (self.translate_coords(loot_box[0]), self.translate_coords(loot_box[1]))
        while get_duration(then=start_time, now=datetime.now(), interval='seconds') < 3:
            with mss() as sct:
                # Take screenshot of the bobber_box area
                screenshot = sct.grab((box[0][0], box[0][1], box[1][0], box[1][1]))
                screenshot = cv.cvtColor(np.array(screenshot), cv.COLOR_BGR2GRAY)
                # Check that the loot window is open
                if not self.check_for_loot_window(screenshot):
                    continue
                # Extra time for loot window to finish appearing
                time.sleep(0.5)
                # Grab new screenshot of fully opened loot window
                screenshot = sct.grab((box[0][0], box[0][1], box[1][0], box[1][1]))
                screenshot = cv.cvtColor(np.array(screenshot), cv.COLOR_BGR2GRAY)
                # Loot window debug
                if self.settings_helper.settings['user'].getboolean('debug'):
                    cv.imshow('loot debug', screenshot)
                    key = cv.waitKey(1)
                    if key == ord('q'):
                        cv.destroyAllWindows()
                        sys.exit()                
                # Check what the loot is
                for fish_name, fish_data in self.fish_map.items():
                    # logger.debug(f"Checking template: {template_name} \n {template}")
                    confidence, location, scale = self.find_template(screenshot, fish_data['template'])
                    logger.debug(f'Template: {fish_name} | Confidence: {confidence} | Location: {location} | Scale: {scale}')
                    # Keep track of our best find for debugging
                    if highest_conf == None or confidence > highest_conf:
                        highest_fish = fish_name
                        highest_conf = confidence
                        highest_loc = location
                        highest_scale = scale
                # Assume best find is correct and count it.
                # thresholding doesn't seem to be a good option here as other templates can also rank high for some reason..
                logger.success(f"Found {highest_fish} - {highest_conf} - {highest_scale}")
                self.fish_map[highest_fish]['loot_count'] += 1
                return highest_loc


    def catch_fish(self, bobber_box):
        """Watches for change in bobber_y position and clicks when over threshold.
            Need to refactor!
        """
        logger.info('Watching for catch')
        start_time = datetime.now()
        average_y_value = 0
        counter = 0
        total_y = 0
        
        # Get screen coordinates of bobber box
        box = (self.translate_coords(bobber_box[0]), self.translate_coords(bobber_box[1]))
        while get_duration(then=start_time, now=datetime.now(), interval='seconds') < self.settings_helper.settings['fishing'].getint('timeout_threshold') and not self.break_helper.time_to_break:
            with mss() as sct:
                # Take screenshot of the bobber_box area
                screenshot = sct.grab((box[0][0], box[0][1], box[1][0], box[1][1]))
                screenshot = cv.cvtColor(np.array(screenshot), cv.COLOR_BGR2GRAY)
                # Check that we found the bobber
                confidence, location, scale = self.find_template(screenshot, self.bobber_template, scale_min=0.8, scale_max=1.2, scale_steps=10)
                logger.debug(f'Confidence: {confidence} | Location: {location} | Scale: {scale}')
                # Keep track of bobbber position (confidence doesn't need to be high since it's a very small area to watch.)
                if (confidence >= 0.30):
                    # Get average y value
                    counter += 1
                    total_y += location[1]
                    average_y_value = total_y // counter
                    if self.settings_helper.settings['user'].getboolean('debug'):
                        # Draw rectangle around bobber being tracked
                        bottom_right = (location[0] + self.w, location[1] + self.h)
                        cv.rectangle(screenshot, location, bottom_right, (0,255,0), 1)
                    # Check if the new bobber_y_value is greater than our difference threshold
                    logger.debug(f'Checking if {location[1]} - {average_y_value} >= {self.DIP_THRESHOLD}')
                    if (abs(location[1] - average_y_value) >= self.DIP_THRESHOLD):
                        # Change in y position > threshold so we're going to click the bobber / catch the fish.
                        self.input_helper.click_mouse()
                        return True
                # Display bobber debug window if enabled
                if self.settings_helper.settings['user'].getboolean('debug'):
                    cv.imshow('bobber debug', screenshot)
                    key = cv.waitKey(1)
                    if key == ord('q'):
                        cv.destroyAllWindows()
                        sys.exit()
        # Hit TIMEOUT_THRESHOLD
        return False


    def run_fish_loop(self):
        """Runs loop to catch fish.
            Need to refactor!
        """
        logger.info('Setting game window to foreground.')
        # Bring game client to foreground
        set_active_window(self.game_window_handle)
        # Wait for game window to enter foreground before starting to fish
        time.sleep(1)
        while not self.break_helper.time_to_break:
            # # Check if we should use fishing bait
            # if self.settings_helper.settings['fishing'].getboolean('use_bait'):
            #     self.time_since_bait = get_duration(then=self.bait_time, now=datetime.now(), interval='minutes')
            #     if self.time_since_bait >= 30 or self.time_since_bait == None:  # Fishing bait has expired
            #         logger.info('Applying fishing bait...')
            #         self.input_helper.press_key(self.settings_helper.settings['fishing'].get('bait_hotkey'))
            #         self.bait_used += 1
            #         self.bait_time = datetime.now()
            with mss() as sct:
                # Chech if we need to vendor / send progress report
                if self.settings_helper.settings['vendor'].getboolean('auto_vendor_enabled'):
                    # Check if it's time to get on vendor mount to sell gray items
                    time_since_vendor = get_duration(then=self.vendor_time, now=datetime.now(), interval='minutes')
                    if time_since_vendor >= self.settings_helper.settings['vendor'].getint('vendor_interval'):
                        logger.info('Now vendoring trash...')
                        # time.sleep(5)
                        self.auto_vendor(
                            self.settings_helper.settings['vendor'].get('mammoth_hotkey'),
                            self.settings_helper.settings['vendor'].get('target_hotkey'),
                            self.settings_helper.settings['vendor'].get('interact_hotkey')
                            )
                        self.vendor_time = datetime.now()
                        # Print progress report / stats
                        self.send_stats(sct.grab(self.game_window_rect))
                        continue  # Start at beginning of loop so we cast our rod
                # Cast fishing rod
                logger.info("Casting fishing rod")
                self.input_helper.press_key(self.settings_helper.settings['fishing'].get('fishing_hotkey'))
                self.rods_cast += 1
                # Wait for bobber to appear
                bobber_wait_time = 2.5
                logger.debug(f"Sleeping {bobber_wait_time} seconds for bobber to appear.")
                time.sleep(bobber_wait_time)
                # Grab Screenshot of game window
                screenshot = sct.grab(self.fishing_area)
                # Convert screenshot to gray for image matching
                screenshot = cv.cvtColor(np.array(screenshot), cv.COLOR_BGR2GRAY)
                # Check game for bobber
                confidence, location, scale = self.find_template(screenshot, self.bobber_template, scale_min=0.8, scale_max=1.4, scale_steps=15)
                logger.debug(f'Potential Bobber - Confidence: {confidence} | Location: {location} | Scale: {scale}')
                # Show Game window if DEBUG is enabled
                if self.settings_helper.settings['user'].getboolean('debug'):
                    cv.imshow('WoW Debug', screenshot)
                    key = cv.waitKey(1)
                    if key == ord('q'):
                        cv.destroyAllWindows()
                        sys.exit()
                # Check if the match is above our confidence threshold
                if confidence >= self.settings_helper.settings['fishing'].getfloat('min_confidence'):
                    logger.success(f"Bobber Found | Confidence: {confidence} | location: {location}")
                    # Get screen coords of new bobber
                    screen_coords = self.translate_coords(location)
                    # Move mouse to bobber
                    logger.success(f'Moving mouse to: location: {location} | screen_coords: {screen_coords}')
                    self.input_helper.move_mouse(screen_coords[0], screen_coords[1])
                    # Get box coordinates to watch around bobber
                    bobber_box = self.get_bobber_box(location)
                    # Wait for catch
                    if (self.catch_fish(bobber_box)):
                        # Identify loot and add it to counter for progress report
                        loot_box = self.get_loot_box(location)
                        # Track what loot we got
                        loot_loc = self.count_loot(loot_box)
                        self.fish_caught += 1
                        # Click on fish in loot window
                        logger.info("Looting fish from loot window.")
                        box = (self.translate_coords(loot_box[0]), self.translate_coords(loot_box[1]))

                        loot_screen_coords = self.translate_coords(loot_loc, (box[0][0], box[0][1], box[1][0], box[1][1]))
                        self.input_helper.move_mouse(loot_screen_coords[0], loot_screen_coords[1])
                        self.input_helper.click_mouse()
                    else:
                        logger.warning('Failed to get catch.')
                        self.no_fish_casts += 1


    def auto_vendor(self, mammoth_hotkey, target_hotkey, interact_hotkey):
        """Gets on mount, targets shop npc, and opens shop for addon to auto sell trash."""
        logger.info('Starting auto vendor')
        # Get on mount
        logger.debug('getting on mount')
        self.input_helper.press_key(mammoth_hotkey)
        time.sleep(3 + random.random())
        # Target shop npc with target macro
        logger.debug('targetting npc')
        self.input_helper.press_key(target_hotkey)
        time.sleep(1 + random.random())
        # Interact with target
        logger.debug('interacting with npc / opening shop')
        self.input_helper.press_key(interact_hotkey)
        time.sleep(1 + random.random())
        # Vendor addon should now sell all of the non-valuable fish
        logger.debug('Sleeping while Vendor addon sells trash')
        time.sleep(5 + random.random())
        # Close shop window
        logger.debug('closing shop window')
        self.input_helper.press_key('esc')  # escape
        time.sleep(1 + random.random())


    def cache_loot_templates(self):
        """Load loot templates into memory on start."""
        loot_templates_dir = "templates\\loot_templates"
        for template_file in os.listdir(loot_templates_dir):
            # Get template path
            template_path = os.path.join(loot_templates_dir, template_file)
            logger.debug(f"Loading in template: {template_path}")
            # Load in template
            template = cv.imread(template_path, 0)
            # Add to dict
            template_name = template_file.removesuffix('.png')
            self.fish_map[template_name]['template'] = template


    def send_stats(self, game_screenshot):
        """Prints stats for current run and sends via webhook if enabled."""
        time_ran = get_duration(then=self.start_time, now=datetime.now(), interval='default')
        self.fish_map = self.tsm.get_gold_earned(self.fish_map)
        # Calculate and formate total gold earned
        gold_earned = round(sum([self.fish_map[fish]['loot_count'] * self.tsm.fish_map[fish]['price'] for fish in self.tsm.fish_map]), 2)
        gold_earned = f"{gold_earned}g"
        # Print progress report to console.
        logger.success('-----------------------')
        logger.success('Progress Report:')
        logger.success(f'Time Ran: {time_ran} minute(s)')
        logger.success(f'Estimated Gold Earned: {gold_earned}')
        logger.success(f'Rods Cast: {self.rods_cast}')
        logger.success(f'Fish Caught: {self.fish_caught}')
        logger.success(f'Bait Used: {self.bait_used}')
        logger.success('-----------------------')

        # Send a progress report via discord webhook if it's enabled.
        if self.settings_helper.settings['webhook'].getboolean('discord_webhook_enabled'):
            logger.debug('sending webhook notification')

            async def send_discord_progress_report():
                async with aiohttp.ClientSession() as session:
                    webhook = Webhook.from_url(url=self.webhook_url, session=session)
                    embed = Embed(title='Progress Report', description='Fishing Assistant Progress Report')
                    embed.add_field(name='Time Ran:', value=time_ran)
                    embed.add_field(name='Rods Cast:', value=self.rods_cast)
                    embed.add_field(name='Fish Caught:', value=self.fish_caught)
                    embed.add_field(name='Estimated Gold Earned:', value=gold_earned)
                    embed.add_field(name='Bait Used:', value=self.bait_used)
                    embed.add_field(name='No catch casts:', value=self.no_fish_casts)
                    for fish in self.fish_map:
                        if self.fish_map[fish]['loot_count'] > 0:
                            embed.add_field(name=fish, value=self.fish_map[fish]['loot_count'])
                    import mss.tools
                    mss.tools.to_png(game_screenshot.rgb, game_screenshot.size, output='game_screenshot.png')
                    file = File("game_screenshot.png", filename="game_screenshot.png")
                    embed.set_image(url="attachment://game_screenshot.png")
                    await webhook.send(embed=embed, file=file, username=self.settings_helper.settings['user'].get('nickname'))

            asyncio.run(send_discord_progress_report())


    def translate_coords(self, coords, sub_region = None):
        """Translates game coords to screen coords."""
        if sub_region == None:
            sub_region_one, sub_region_two = self.fishing_area[0], self.fishing_area[1]
        else:
            sub_region_one, sub_region_two = sub_region[0], sub_region[1]
        
        return (coords[0] + self.w // 2 + sub_region_one, coords[1] + self.h // 2 + sub_region_two)


    def set_game_window_data(self):
        """Set new game window data after it's relaunched from a break."""
        self.game_window_handle = FindWindow(self.game_window_class, self.game_window_name)
        # Launch the game if it's not already open.
        if self.game_window_handle == 0:
            logger.info(f"Couldn't find an open WoW client. Launching game.")
            # Open game
            self.break_helper.launch_game()
            # Get new handle after opening game
            self.game_window_handle = FindWindow(self.game_window_class, self.game_window_name)
        # Set game client variables
        self.game_window_rect = GetWindowRect(self.game_window_handle)  # left, top, right, bottom
        self.game_size = GetClientRect(self.game_window_handle)

        # # First set of offsets (30,8) will remove window title bar / border
        # top_offset = 30
        # bot_offset = 8
        # Second set of offsets will only show middle of game window
        self.top_offset = (self.game_size[2] // 2) - int((0.20 * self.game_size[2]))
        self.bot_offset = (self.game_size[3] // 2) - int((0.30 * self.game_size[3]))
        logger.info(f'Full Game Rect: {self.game_window_rect}')
        self.fishing_area = (
            self.game_window_rect[0] + self.bot_offset,
            self.game_window_rect[1] + self.top_offset,
            self.game_window_rect[2] - self.bot_offset,
            self.game_window_rect[3] - self.bot_offset
        )


    def run(self):
        self.stopped = False
        while not self.stopped:
            if self.breaks_enabled:
                while not self.break_helper.time_to_break:
                    self.set_game_window_data()
                    self.break_helper.start()
                    self.run_fish_loop()
            else:
                self.run_fish_loop()


# https://stackoverflow.com/questions/6312627/windows-7-how-to-bring-a-window-to-the-front-no-matter-what-other-window-has-fo/6324105#6324105
# Sometimes setforegroundwindow gives an error so we'll try this
from win32gui import GetWindowPlacement, ShowWindow, SetForegroundWindow, SetActiveWindow
from win32con import (SW_SHOW, SW_RESTORE)
def set_active_window(window_id):
    if GetWindowPlacement(window_id)[1] == 2:
        ShowWindow(window_id, SW_RESTORE)
    else:
        ShowWindow(window_id, SW_SHOW)
    try:
        SetForegroundWindow(window_id)
        SetActiveWindow(window_id)
    except Exception as e:
        logger.warning('Got error while trying to foreground window. Continuing anyways(not sure how this will go)')
