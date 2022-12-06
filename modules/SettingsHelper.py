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
            config.set("user", "debug", "True")
            config.set("user", "upper_reaction_time", "0.350")
            config.set("user", "lower_reaction_time", "0.170")
            config.set("user", "input_method", "virtual")
            # Add fishing settings to config
            config.set("fishing", "fishing_hotkey", "z")
            config.set("fishing", "min_confidence", "0.50")
            config.set("fishing", "timeout_threshold", "20")
            config.set("fishing", "dip_threshold", "7")
            config.set("fishing", "bobber_image_name", "bobber_dark.png")
            # Add break settings to config
            config.set("breaks", "breaks_enabled", "True")
            config.set("breaks", "wow_path", r"C:\Program Files (x86)\World of Warcraft\_retail_\Wow.exe")
            config.set("breaks", "account_password", "acc_password_here")
            config.set("breaks", "playtime_duration_range", "30,45")
            config.set("breaks", "break_duration_range", "2,10")
            # Add vendor settings to config
            config.add_section("vendor")
            config.set("vendor", "auto_vendor_enabled", "True")
            config.set("vendor", "mammoth_hotkey", "f1")
            config.set("vendor", "target_hotkey", "f2")
            config.set("vendor", "interact_hotkey", "f3")
            config.set("vendor", "vendor_interval", "30")
            # Add Discord Webhook settings to config
            config.add_section("webhook")
            config.set("webhook", "discord_webhook_enabled", "False")
            config.set("webhook", "discord_webhook_url", "webhook_url_goes_here")
            with open(settings_path, "w+") as config_file:
                config.write(config_file)
        # Add settings from settings file to config and return the config
        config.read(settings_path)
        return config
