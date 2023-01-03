import pytz
import random
import subprocess
import threading
import time
from datetime import datetime
from discord_webhook import DiscordWebhook
from loguru import logger
from utility.util import get_duration


class BreakHelper():
    stopped = True
    """Class to handle taking breaks during automation sessions."""
    def __init__(self, settings_helper, input_helper, *args, **kwargs):
        self.settings_helper = settings_helper
        # Get breaks settings from settings.ini
        self.playtime_duration_range = self.settings_helper.settings['breaks']['playtime_duration_range']
        self.break_duration_range = self.settings_helper.settings['breaks']['break_duration_range']
        # Input helper
        self.input_helper = input_helper
        # Get webhook url
        self.webhook_url = self.settings_helper.settings['webhook']['DISCORD_WEBHOOK_URL']
        # Get WoW path
        self.wow_path = self.settings_helper.settings['breaks']['wow_path']
        self.play_start_time = None
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
        """Return True if the current time is between 6:00 A.M. PST and 9:30 A.M. PST"""
        # Get the current date and time
        current_time = datetime.datetime.now()

        # Get the current time in PST
        pst_tz = pytz.timezone('US/Pacific')
        pst_time = current_time.astimezone(pst_tz)

        # Check if the current day is Tuesday
        if pst_time.weekday() == 1:
            # Check if the current time is between 6:00 A.M. and 9:30 A.M. PST
            if pst_time.hour >= 6 and pst_time.hour < 9:
                return True
            elif pst_time.hour == 9 and pst_time.minute < 30:
                return True
        return False


    def check_break_required(self):
        """Check if it's time to take a break."""
        lower_bound, upper_bound = self.playtime_duration_range.split(',')
        play_time = random.randrange(int(lower_bound), int(upper_bound))
        logger.info(f'Playing for {play_time} minutes before breaking.')
        while (get_duration(then=self.play_start_time, now=datetime.now(), interval='minutes') < play_time) or (self.break_allowed == False) and not (self.check_tuesday_reset()):
            time.sleep(1)
        logger.info('Setting time_to_break to True')
        self.time_to_break = True


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
        self.time_to_break = False
        self.stop()


    def take_break(self):
        # Get random time in minutes to take a break for
        lower_bound, upper_bound = self.break_duration_range.split(',')
        break_time = random.randrange(int(lower_bound), int(upper_bound))
        # Notify that we're about to take a break
        break_msg = f'Break Notification: Taking a break for: {break_time} minutes.'
        logger.info(break_msg)
        if self.settings_helper.settings['webhook'].getboolean('discord_webhook_enabled'):
            webhook = DiscordWebhook(
            url=self.webhook_url,
            rate_limit_retry=True,
            content=break_msg)
            webhook.execute()
        self.break_start_time = datetime.now()
        # Loop until our break duration is over.
        while get_duration(then=self.break_start_time, now=datetime.now(), interval='minutes') < break_time:
            time.sleep(1)
        # Notify that the break is finished
        break_finished_msg = f'Break Notification: {break_time} minute break finished.'
        logger.info(break_finished_msg)
        if self.settings_helper.settings['webhook'].getboolean('discord_webhook_enabled'):
            webhook = DiscordWebhook(
            url=self.webhook_url,
            rate_limit_retry=True,
            content=break_finished_msg)
            webhook.execute()


    def run(self):
        while not self.stopped:
            self.play_start_time = datetime.now()
            self.check_break_required()
            self.close_game()
            self.take_break()
            self.launch_game()
