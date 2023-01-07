import pytz
import random
import subprocess
import threading
import time
from datetime import datetime
from loguru import logger
from modules.LoggingHelper import LoggingHelper
from utility.util import has_time_passed


class BreakHelper():
    stopped = True
    """Class to handle taking breaks during automation sessions."""
    def __init__(self, settings_helper, input_helper, *args, **kwargs):
        self.settings_helper = settings_helper
        # Get breaks settings from settings.ini
        self.playtime_duration_range = self.settings_helper.settings['breaks']['playtime_duration_range']
        self.break_duration_range = self.settings_helper.settings['breaks']['break_duration_range']
        # Initialize input helper
        self.input_helper = input_helper
        # Initialize logging helper
        self.logging_helper = LoggingHelper(self.settings_helper)
        # Get WoW path
        self.wow_path = self.settings_helper.settings['breaks']['wow_path']
        self.break_start_time = None
        self.time_to_break = False
        self.break_allowed = False


    def start(self):
        """Starts check_break thread"""
        self.stopped = False
        t = threading.Thread(target=self.run)
        t.start()


    def stop(self):
        self.stopped = True


    def check_tuesday_reset(self):
        """If it's Tuesday between 6:00 AM and 9:30 AM PST, return the amount of minutes until 9:30."""
        # Get the current date and time
        current_time = datetime.now()

        # Get the current time in PST
        pst_tz = pytz.timezone('US/Pacific')
        pst_time = current_time.astimezone(pst_tz)

        # Create a datetime object representing 9:30 A.M. PST on the current day
        target_time = pst_time.replace(hour=9, minute=30, second=0, microsecond=0)

        # Calculate the difference between the current time and 9:30 A.M. PST in minutes
        delta = target_time - pst_time
        minutes = delta.total_seconds() / 60

        # Check if the current day is Tuesday
        if pst_time.weekday() != 1:
            # Negative minutes means it isn't between our break hours
            return -1
        # Check if the current time is between 6:00 A.M. and 9:30 A.M. PST
        elif (pst_time.hour >= 6 and pst_time.hour < 9) or (pst_time.hour == 9 and pst_time.minute < 30):
            return minutes


    def close_game(self):
        """Kills the process for the game client."""
        subprocess.call(['taskkill.exe', '/IM', 'Wow.exe'])


    def launch_game(self):
        """Launches the game and loads the currently selected character."""
        logger.info('Launching game')
        # Open the game
        path = r"{}".format(self.wow_path)  # format path to raw string
        proc = subprocess.Popen([path])
        # sleep while game finishes loading...
        # subprocess.call([path]) should block until process opens but doesn't seem to ever return... Same with subprocess.wait()
        # Could probably check if a process is open by certain name as a hack
        logger.info('sleeping 60 seconds after opening game')
        time.sleep(60)
        logger.debug('Entering password to login')
        password = self.settings_helper.settings['breaks']['account_password']
        for letter in password:
            self.input_helper.press_key(letter)
        # Hit enter to login to the account
        logger.debug('Hitting enter to login to the account')
        self.input_helper.press_key('enter')
        # Give some time for the character select screen to load
        time.sleep(60)
        # Hit enter to login to the selected character
        logger.debug('Loading into game / character')
        self.input_helper.press_key('enter')
        time.sleep(60)


    def take_break(self, break_time: int = None):
        """Sends a discord notification if enabled about the break and then sleeps until break is finished.
        
        Params:
            break_time: The amount of minutes to take a break for. If none are provided, a random time will be used within the limit set in settings.ini.
        """
        if break_time == None:
            # Get random time in minutes to take a break for
            lower_bound, upper_bound = map(int, self.break_duration_range.split(','))
            break_time = random.randrange(lower_bound, upper_bound)
        # Notify that we're about to take a break
        self.logging_helper.send_break_notification(break_time=break_time)
        self.break_start_time = datetime.now()
        # Loop until our break duration is over.
        while not has_time_passed(start_time=self.break_start_time, interval='minutes', threshold=break_time):
            time.sleep(1)
        # Notify that the break is finished
        self.logging_helper.send_break_notification(break_time=break_time, break_end=True)



    def handle_break(self, break_time = None):
        """Wrapper function to handle closing the game, taking a break, and launching the game."""
        # Set flag for FishingBot to stop
        self.time_to_break = True
        # Close current game client
        self.close_game()
        # Loop for the duration of the break
        self.take_break(break_time=break_time)
        # Relaunch the game client
        self.launch_game()
        # End break
        self.time_to_break = False
        self.stop()   


    def run(self):
        # Get random amount of time (within settings limits) to play before breaking
        lower_bound, upper_bound = map(int, self.playtime_duration_range.split(','))
        minutes_to_play = random.randrange(lower_bound, upper_bound)
        logger.info(f'Playing for {minutes_to_play} minutes before breaking.')
        play_start_time = datetime.now()
        while not self.stopped:
            time.sleep(1)
            # Early return if we're in the middle of a fishing loop
            if self.break_allowed == False:
                continue
            # Check if we need to take an extended break for Tuesday reset
            minutes = self.check_tuesday_reset()
            if minutes > 0:
                self.handle_break(break_time=minutes)
            elif has_time_passed(start_time=play_start_time, interval='minutes', threshold=minutes_to_play):
                self.handle_break()
