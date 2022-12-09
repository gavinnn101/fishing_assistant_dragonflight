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
        self.break_allowed = True  # Flag getting set in FishingBot.catch_fish()


    def start(self):
        """Starts check_break thread"""
        self.stopped = False
        t = threading.Thread(target=self.run)
        t.start()


    def stop(self):
        self.stopped = True


    def close_game(self):
        """Kills the process for the game client."""
        subprocess.call(['taskkill.exe', '/IM', 'Wow.exe'])


    def launch_game(self):
        """Launches the game and loads the currently selected character."""
        logger.info('Launching game')
        # Open the game
        path = r"{}".format(self.wow_path)  # format path to raw string
        proc = subprocess.Popen([path])
        # Give some time for the game to load just in case. No real check to know that we're on the login screen...
        time.sleep(10)
        logger.debug('Entering password to login')
        password = self.settings_helper.settings['breaks']['account_password']
        for letter in password:
            self.input_helper.press_key(letter)
        # Hit enter to login to the account
        logger.debug('Hitting enter to login to the account')
        self.input_helper.press_key('enter')
        # Give some time for the character select screen to load
        time.sleep(10)
        # Hit enter to login to the selected character
        logger.debug('Loading into game / character')
        self.input_helper.press_key('enter')
        time.sleep(20)
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
        if self.settings_helper.settings['webhook']['discord_webhook_enabled']:
            webhook = DiscordWebhook(
            url=self.webhook_url,
            rate_limit_retry=True,
            content=break_finished_msg)
            webhook.execute()


    def check_break_required(self):
        """Check if it's time to take a break."""
        lower_bound, upper_bound = self.playtime_duration_range.split(',')
        play_time = random.randrange(int(lower_bound), int(upper_bound))
        logger.info(f'Playing for {play_time} minutes before breaking.')
        while get_duration(then=self.play_start_time, now=datetime.now(), interval='minutes') < play_time or not self.break_allowed:
            time.sleep(1)
        logger.info('Setting time_to_break to True')
        self.time_to_break = True


    def run(self):
        while not self.stopped:
            self.play_start_time = datetime.now()
            self.check_break_required()
            self.close_game()
            self.take_break()
            self.launch_game()
