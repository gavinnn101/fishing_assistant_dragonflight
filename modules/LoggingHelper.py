import aiohttp
import asyncio
from discord import Webhook, Embed, File
from loguru import logger

class LoggingHelper():
    """Class to handle logging messages and stats to console, discord, database, etc."""
    def __init__(self, settings_helper, *args, **kwargs):
        self.settings_helper = settings_helper
        # Get webhook url
        self.webhook_url = self.settings_helper.settings['webhook']['DISCORD_WEBHOOK_URL']


    
    def send_discord_message(self, title: str, content: str, description: str = None, embed_fields: dict = None):
        """
        Sends a discord message with the provided title, description, and content as text.
        embed_fields should looks like: embed_fields = {"field text": ["field value", False]} where False is if the field should be inline.
        """
        async def _send_discord_message(message: str):
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(url=self.webhook_url, session=session)
                embed = Embed(title=title, description=description)
                if embed_fields is not None:
                    for embed_field, embled_value in embed_fields.items():
                        embed.add_field(name=embed_field, value=embled_value[0], inline=embled_value[1])
                await webhook.send(username=self.settings_helper.settings['user'].get('nickname'), embed=embed, content=message)
        asyncio.run(_send_discord_message(message=content))


    def send_break_notification(self, break_time: int, break_end: bool = False):
        """Sends a notification to console and discord with break information."""
        nickname = self.settings_helper.settings['user'].get('nickname')
        # Set action depending if break_end is True or not.
        action = "ended" if break_end else "started"
        logger.info(f"Account: {nickname} {action} a break for {break_time} minutes.")

        # Send webhook notification if enabled
        if self.settings_helper.settings['webhook'].getboolean('discord_webhook_enabled'):
                self.send_discord_message(title="Break notification", description=f"Break {action}", embed_fields={nickname: [break_time, False]})


    def send_progress_report(self, log_stats = True):
        """
        Sends a notification to console and discord with loot progress.
        If log_stats = True we'll also log the progress and nickname to database.
        """
        pass