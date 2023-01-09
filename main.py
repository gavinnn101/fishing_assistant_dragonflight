import sys
from loguru import logger

from modules.FishingBot import FishingBot
from modules.LoggingHelper import LoggingHelper
from modules.SettingsHelper import SettingsHelper

# Initialize SettingsHelper
settings_helper = SettingsHelper()

# Initialize LoggingHelper
logging_helper = LoggingHelper(settings_helper=settings_helper)

if not settings_helper.settings['user'].getboolean('debug'):
    # Set log level to INFO
    logger.remove()
    logger.add(sys.stderr, level="INFO")

# Initialize Fishing Bot
fishing_bot = FishingBot(settings_helper=settings_helper, logging_helper=logging_helper)

# Start bot
# bot class checks for breaks and input method internally
try:
    fishing_bot.run()
except KeyboardInterrupt:
    fishing_bot.break_helper.stop()  # Stop break helper thread
    sys.exit("Got keyboard interrupt. Exiting.")
