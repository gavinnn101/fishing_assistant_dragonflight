import configparser
import sys
from loguru import logger
import os

class SettingsHelper:
    """Wrapper utility class for config settings."""
    def __init__(self, *args, **kwargs):
        # Full path to directory where the script is launched from.
        self.root_dir = sys.path[0]
        # Create settings directory if needed
        self.create_settings_dir()
        # Load settings from settings.ini
        self.settings = self.get_settings()


    def create_settings_dir(self):
        """Creates the profile directory and subdirectories if they don't exist."""
        logger.info("create_settings_dir called")
        settings_path = f"{self.root_dir}\\settings"

        if not os.path.exists(settings_path):
            os.makedirs(settings_path)
            logger.info(f"Created directory {settings_path}")
        else:
            logger.info(f"Directory {settings_path} already exists")


    def get_settings(self):
        """returns settings from settings.ini or creates a default if it doesn't exist."""
        logger.info("Getting settings...")
        config = configparser.ConfigParser()
        settings_path = f"{self.root_dir}\\settings\\settings.ini"
        # Create a default settings file if one doesn't already exist.
        if not os.path.isfile(settings_path):
            logger.info(f"Creating default settings.ini")
            # Add user settings to config
            config.add_section("user")
            config.set("user", "DEBUG", "True")
            config.set("user", "UPPER_REACTION_TIME", "0.350")
            config.set("user", "LOWER_REACTION_TIME", "0.170")
            config.set("user", "INPUT_METHOD", "virtual")
            config.set("user", "FISHING_HOTKEY", "z")
            config.set("user", "MIN_CONFIDENCE", "0.50")
            config.set("user", "TIMEOUT_THRESHOLD", "20")
            config.set("user", "DIP_THRESHOLD", "7")
            config.set("user", "BOBBER_IMAGE_NAME", "bobber_dark.png")
            # Add vendor settings to config
            config.add_section("vendor")
            config.set("vendor", "AUTO_VENDOR_ENABLED", "True")
            config.set("vendor", "MAMMOTH_HOTKEY", "f1")
            config.set("vendor", "TARGET_HOTKEY", "f2")
            config.set("vendor", "INTERACT_HOTKEY", "f3")
            config.set("vendor", "VENDOR_INTERVAL", "30")
            # Add Discord Webhook settings to config
            config.add_section("webhook")
            config.set("webhook", "DISCORD_WEBHOOK_ENABLED", "False")
            config.set("webhook", "DISCORD_WEBHOOK_URL", "webhook_url_goes_here")
            with open(settings_path, "w+") as config_file:
                config.write(config_file)
        # Add settings from settings file to config and return the config
        config.read(settings_path)
        return config
