import aiohttp
import asyncio
import mss.tools
from datetime import datetime
from discord import Webhook, Embed, File
from loguru import logger

from utility.util import get_duration
from modules.TSMWrapper import TSMWrapper

class LoggingHelper():
    """Class to handle logging messages and stats to console, discord, database, etc."""
    def __init__(self, settings_helper, *args, **kwargs):
        self.settings_helper = settings_helper
        # Get webhook url
        self.webhook_url = self.settings_helper.settings['webhook']['DISCORD_WEBHOOK_URL']
        # Initialize tsm wrapper to get prices of fish
        logger.debug("init tsmWrapper from LoggingHelper")
        self.tsm = TSMWrapper(settings_helper=self.settings_helper)


    def send_break_notification(self, break_time: int, break_end: bool = False):
        """Sends a notification to console and discord with break information."""

        async def _send_break_notification(action: str):
            account_name = self.settings_helper.settings['user'].get('nickname')
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(url=self.webhook_url, session=session)
                embed = Embed(title='Break Notification', description=f'Break {action} for {account_name}')
                embed.add_field(name='Break duration (minutes):', value=break_time)
                try:
                    await webhook.send(embed=embed, username=account_name)
                except Exception as e:
                    logger.error(f"Caugh exception while sending break notification: {e}")
        nickname = self.settings_helper.settings['user'].get('nickname')
        # Set action depending if break_end is True or not.
        action = "ended" if break_end else "started"
        logger.info(f"Account: {nickname} {action} a break for {break_time} minutes.")

        # Send webhook notification if enabled
        if self.settings_helper.settings['webhook'].getboolean('discord_webhook_enabled'):
            asyncio.run(_send_break_notification(action=action))


    def send_progress_report(self, fish_map: dict, fishing_stats: dict, start_time, game_screenshot, log_stats: bool = True):
        """
        Sends a notification to console and discord with loot progress.
        If log_stats = True we'll also log the progress and nickname to database.
        """

        async def _send_progress_report(stat_embeds: dict):
            account_name = self.settings_helper.settings['user'].get('nickname')
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(url=self.webhook_url, session=session)
                embed = Embed(title='Progress Report', description='Fishing Assistant Progress Report')
                for stat, stat_value in stat_embeds.items():
                    embed.add_field(name=stat, value=stat_value)
                mss.tools.to_png(game_screenshot.rgb, game_screenshot.size, output='game_screenshot.png')
                file = File("game_screenshot.png", filename="game_screenshot.png")
                embed.set_image(url="attachment://game_screenshot.png")
                try:
                    await webhook.send(embed=embed, username=account_name, file=file)
                except Exception as e:
                    logger.error(f"Caugh exception while sending progress report: {e}")



        time_ran = get_duration(then=start_time, now=datetime.now(), interval='default')
        fish_map = self.tsm.get_gold_earned(fish_map)
        # Calculate and formate total gold earned
        gold_earned = round(sum([fish_map[fish]['loot_count'] * self.tsm.fish_map[fish]['price'] for fish in self.tsm.fish_map]), 2)
        gold_earned = f"{gold_earned}g"

        # Log fishing stats to database
        if log_stats:
            pass

        # Print progress report to console.
        rods_cast = fishing_stats['rods_cast']
        no_fish_casts = fishing_stats['no_fish_casts']
        fish_caught = fishing_stats['fish_caught']
        bait_used = fishing_stats['bait_used']

        logger.success('-----------------------')
        logger.success('Progress Report:')
        logger.success(f'Time Ran: {time_ran} minute(s)')
        logger.success(f'Estimated Gold Earned: {gold_earned}')
        logger.success(f'Rods Cast: {rods_cast}')
        logger.success(f'No Fish Casts: {no_fish_casts}')
        logger.success(f'Fish Caught: {fish_caught}')
        logger.success(f'Bait Used: {bait_used}')
        logger.success('-----------------------')


        # Send progress report to discord
        if self.settings_helper.settings['webhook'].getboolean('discord_webhook_enabled'):
            logger.debug('Sending progress report webhook')
            # Build dict of fish loot count and fishing stats that send_discord_message() expects, to show in progress report
            embed_stats = {}
            # Add time ran to embed dict
            embed_stats['time_ran'] = time_ran
            # Add gold earned to embed dict
            embed_stats['gold_earned'] = gold_earned
            # Add fishing stats to embed dict
            for stat_name, stat_value in fishing_stats.items():
                embed_stats[stat_name] = stat_value
            # Add fish loot count to embed dict
            for fish_name, values in fish_map.items():
                fish_count = values['loot_count']
                embed_stats[fish_name] = fish_count
            # Send discord message with progress report.
            asyncio.run(_send_progress_report(stat_embeds=embed_stats))
