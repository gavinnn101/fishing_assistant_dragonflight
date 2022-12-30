import sys
from loguru import logger

from modules.SettingsHelper import SettingsHelper
from modules.FishingBot import FishingBot

# Initialize SettingsHelper
settings_helper = SettingsHelper()

if not settings_helper.settings['user'].getboolean('debug'):
    # Set log level to INFO
    logger.remove()
    logger.add(sys.stderr, level="INFO")

# Initialize Fishing Bot
fishing_bot = FishingBot(settings_helper=settings_helper)

# Start bot
# bot class checks for breaks and input method internally
try:
    fishing_bot.run()
except KeyboardInterrupt:
    fishing_bot.break_helper.stop()  # Stop break helper thread
    sys.exit("Got keyboard interrupt. Exiting.")