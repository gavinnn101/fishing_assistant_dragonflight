import aiohttp
import asyncio
from discord import Webhook, Embed, File

class LoggingHelper():
    """Class to handle logging messages and stats to console, discord, database, etc."""
    def __init__(self, settings_helper, *args, **kwargs):
        self.settings_helper = settings_helper
        # Get webhook url
        self.webhook_url = self.settings_helper.settings['webhook']['DISCORD_WEBHOOK_URL']


    
    def send_discord_message(self, title: str, content: str, description: str = None):
        """Sends a discord message with the provided title, description, and content as text."""
        async def _send_discord_message(message: str):
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(url=self.webhook_url, session=session)
                embed = Embed(title=title, description=description)
                await webhook.send(username=self.settings_helper.settings['user'].get('nickname'), embed=embed, content=message)
        asyncio.run(_send_discord_message(message=content))


