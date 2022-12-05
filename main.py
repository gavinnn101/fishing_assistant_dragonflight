import sys
from loguru import logger

from modules.SettingsHelper import SettingsHelper
from modules.FishingBot import FishingBot

# Initialize SettingsHelper
settings_helper = SettingsHelper()

if not settings_helper.settings['user'].get('debug'):
    # Set log level to INFO
    logger.remove()
    logger.add(sys.stderr, level="INFO")

# Initialize Fishing Bot
fishing_bot = FishingBot(settings_helper=settings_helper)

# Start fishing bot (this will loop forever)
fishing_bot.run_fish_loop()
