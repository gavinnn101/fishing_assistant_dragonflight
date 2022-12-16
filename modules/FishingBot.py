import cv2 as cv
import numpy as np
import random
import sys
import time
from datetime import datetime
from discord_webhook import DiscordWebhook, DiscordEmbed
from loguru import logger
from mss import mss
from win32gui import FindWindow, GetWindowRect, GetClientRect

from modules.BreakHelper import BreakHelper
from modules.InputHelper import InputHelper
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
        self.template_name = self.settings_helper.settings['fishing'].get('bobber_image_name')
        self.template_path = f'templates\\{self.template_name}'
        self.bobber_template = cv.imread(self.template_path, 0)
        self.w, self.h = self.bobber_template.shape[::-1]
        # Initialize fishing stats
        self.fish_caught = 0
        self.no_fish_casts = 0
        self.bait_used = 0
        self.rods_cast = 0
        self.DIP_THRESHOLD = self.settings_helper.settings['fishing'].getint('dip_threshold')
        self.time_since_bait = None
        # Set start time of bot
        self.start_time = datetime.now()
        # Start auto vendor timer if enabled
        self.auto_vendor_enabled = self.settings_helper.settings['vendor'].get('auto_vendor_enabled')
        if self.auto_vendor_enabled:
            self.vendor_time = self.start_time

        # Game Client Variables
        self.game_window_name = "World of Warcraft"
        self.game_window_class = "GxWindowClass"
        self.game_window_handle = FindWindow(self.game_window_class, self.game_window_name)
        self.game_window_rect = GetWindowRect(self.game_window_handle)  # left, top, right, bottom
        self.game_size = GetClientRect(self.game_window_handle)

        # # First set of offsets (30,8) will remove window title bar / border
        # top_offset = 30
        # bot_offset = 8
        # Second set of offsets will only show middle of game window
        self.top_offset = (self.game_size[2] // 2) - int((0.20 * self.game_size[2]))
        self.bot_offset = (self.game_size[3] // 2) - int((0.30 * self.game_size[3]))
        logger.info(f'Full Game Rect: {self.game_window_rect}')
        self.game_window_rect = (
            self.game_window_rect[0] + self.bot_offset,
            self.game_window_rect[1] + self.top_offset,
            self.game_window_rect[2] - self.bot_offset,
            self.game_window_rect[3] - self.bot_offset
        )

        # Set log level
        if not settings_helper.settings['user'].get('debug'):
            # Set log level to INFO
            logger.remove()
            logger.add(sys.stderr, level="INFO")


    def find_bobber(self, screenshot):
        methods = ['cv.TM_CCOEFF_NORMED']  #, 'cv.TM_CCORR_NORMED', 'cv.TM_SQDIFF', 'cv.TM_SQDIFF_NORMED'
        match = cv.matchTemplate(screenshot, self.bobber_template, eval(methods[0]))
        results = cv.minMaxLoc(match) # (min_val, max_val, min_loc, max_loc)
        return (results[1], results[3]) # max_val, max_loc


    def get_bobber_box(self, location):
        """Returns coordinates of box to watch around found bobber."""
        # Bobber coordinates
        top_left = location
        top_left = (top_left[0] - 20, top_left[1] - 20)  # position of box
        bottom_right = (top_left[0] + self.w + 40, top_left[1] + self.h + 20)  # size of box
        return (top_left, bottom_right)


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
        # Don't start a break in the middle of a fishing loop
        self.break_helper.break_allowed = False
        while get_duration(then=start_time, now=datetime.now(), interval='seconds') < self.settings_helper.settings['fishing'].getint('timeout_threshold'):
            with mss() as sct:
                # Take screenshot of the bobber_box area
                screenshot = sct.grab((box[0][0], box[0][1], box[1][0], box[1][1]))
                screenshot = cv.cvtColor(np.array(screenshot), cv.COLOR_BGR2GRAY)
                # Check that we found the bobber
                confidence, location = self.find_bobber(screenshot)
                logger.debug(f'Confidence: {confidence} | Location: {location}')
                # Keep track of bobbber position (confidence doesn't need to be high since it's a very small area to watch.)
                if (confidence >= 0.30):
                    # Get average y value
                    counter += 1
                    total_y += location[1]
                    average_y_value = total_y // counter
                    if self.settings_helper.settings['user'].get('debug'):
                        # Draw rectangle around bobber being tracked
                        bottom_right = (location[0] + self.w, location[1] + self.h)
                        cv.rectangle(screenshot, location, bottom_right, (0,255,0), 1)
                    # Check if the new bobber_y_value is greater than our difference threshold
                    logger.debug(f'Checking if {location[1]} - {average_y_value} >= {self.DIP_THRESHOLD}')
                    if (abs(location[1] - average_y_value) >= self.DIP_THRESHOLD):
                        # Change in y position > threshold so we're going to click the bobber / catch the fish.
                        self.input_helper.click_mouse()
                        # Sleep for a second so it can finish looting
                        time.sleep(1 + random.random())
                        self.break_helper.break_allowed = True
                        return True
                # Display bobber debug window if enabled
                if self.settings_helper.settings['user'].get('debug'):
                    cv.imshow('bobber debug', screenshot)
                    key = cv.waitKey(1)
                    if key == ord('q'):
                        cv.destroyAllWindows()
                        sys.exit()
        # Hit TIMEOUT_THRESHOLD
        self.break_helper.break_allowed = True
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
            # Cast fishing rod
            self.input_helper.press_key(self.settings_helper.settings['fishing'].get('fishing_hotkey'))
            self.rods_cast += 1
            # Wait for bobber to appear
            time.sleep(3 + random.uniform(self.REACTION_TIME_RANGE[0], self.REACTION_TIME_RANGE[1]))
            with mss() as sct:
                # Grab Screenshot of game window
                screenshot = sct.grab(self.game_window_rect)
                if self.settings_helper.settings['vendor'].get('auto_vendor_enabled'):
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
                # Convert screenshot to gray for image matching
                screenshot = cv.cvtColor(np.array(screenshot), cv.COLOR_BGR2GRAY)
                # Check game for bobber
                confidence, location = self.find_bobber(screenshot)
                logger.debug(f'Confidence: {confidence}')
                # Show Game window if DEBUG is enabled
                if self.settings_helper.settings['user'].get('debug'):
                    cv.imshow('WoW Debug', screenshot)
                    key = cv.waitKey(1)
                    if key == ord('q'):
                        cv.destroyAllWindows()
                        sys.exit()
                # Check if the match is above our confidence threshold
                if confidence >= self.settings_helper.settings['fishing'].getfloat('min_confidence'):
                    logger.success(f"Bobber Found | Confidence: {confidence} | location: {location}")
                    # Get box coordinates to watch around bobber
                    bobber_box = self.get_bobber_box(location)
                    # Get screen coords of new bobber
                    screen_coords = self.translate_coords(location)
                    # Move mouse to bobber
                    logger.success(f'Moving mouse to: location: {location} | screen_coords: {screen_coords}')
                    self.input_helper.move_mouse(screen_coords[0], screen_coords[1])
                    # Wait for catch
                    if (self.catch_fish(bobber_box)):
                        self.fish_caught += 1
                    else:
                        logger.warning('Failed to get catch.')
                        self.no_fish_casts += 1


    def auto_vendor(self, mammoth_hotkey, target_hotkey, interact_hotkey):
        """Gets on mount, targets shop npc, and opens shop for addon to auto sell trash."""
        # Don't start a break in the middle of vendoring
        self.break_helper.break_allowed = False
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
        # Unset break flag
        self.break_helper.break_allowed = True


    def send_stats(self, game_screenshot):
        """Prints stats for current run and sends via webhook if enabled."""
        time_ran = get_duration(then=self.start_time, now=datetime.now(), interval='default')
        gold_earned = self.fish_caught * 10
        # Print progress report to console.
        logger.success('-----------------------')
        logger.success('Progress Report:')
        logger.success(f'Time Ran: {time_ran} minute(s)')
        logger.success(f'Estimated Gold Earned: {gold_earned}g')
        logger.success(f'Rods Cast: {self.rods_cast}')
        logger.success(f'Fish Caught: {self.fish_caught}')
        logger.success(f'Bait Used: {self.bait_used}')
        logger.success('-----------------------')

        # Send a progress report via discord webhook if it's enabled.
        if self.settings_helper.settings['webhook'].getboolean('discord_webhook_enabled'):
            # Create embeds with fishing stats to send
            embed = DiscordEmbed(title='Progress Report', description='Fishing Assistant Progress Report', color='03b2f8')
            embed.add_embed_field('Time Ran:', time_ran)
            embed.add_embed_field('Estimated Gold Earned:', gold_earned)
            embed.add_embed_field('Rods Cast:', self.rods_cast)
            embed.add_embed_field('Fish Caught:', self.fish_caught)
            embed.add_embed_field('No catch casts:', self.no_fish_casts)
            embed.add_embed_field('Bait Used:', self.bait_used)
            # Create webhook and send it
            webhook = DiscordWebhook(url=self.webhook_url, rate_limit_retry=True)
            # Add game screenshot to embed
            import mss.tools
            mss.tools.to_png(game_screenshot.rgb, game_screenshot.size, output='game_screenshot.png')
            with open("game_screenshot.png", "rb") as f:
                webhook.add_file(file=f.read(), filename='game_screenshot.png')
            embed.set_thumbnail(url='attachment://game_screenshot.png')
            webhook.add_embed(embed)
            response = webhook.execute()


    def translate_coords(self, coords):
        """Translates game coords to screen coords."""
        return (coords[0] + self.w // 2 + self.game_window_rect[0], coords[1] + self.h // 2 + self.game_window_rect[1])


    def set_game_window_data(self):
        """Set new game window data after it's relaunched from a break."""
        self.game_window_handle = FindWindow(self.game_window_class, self.game_window_name)
        self.game_window_rect = GetWindowRect(self.game_window_handle)  # left, top, right, bottom
        self.game_size = GetClientRect(self.game_window_handle)

        # # First set of offsets (30,8) will remove window title bar / border
        # top_offset = 30
        # bot_offset = 8
        # Second set of offsets will only show middle of game window
        self.top_offset = (self.game_size[2] // 2) - int((0.20 * self.game_size[2]))
        self.bot_offset = (self.game_size[3] // 2) - int((0.30 * self.game_size[3]))
        logger.info(f'Full Game Rect: {self.game_window_rect}')
        self.game_window_rect = (
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
    SetForegroundWindow(window_id)
    SetActiveWindow(window_id)
