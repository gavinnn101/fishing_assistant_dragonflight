import requests
import time
import sys
from datetime import datetime
from loguru import logger
from utility.util import get_duration

class TSMWrapper():
    """Class makes API calls to TSM's pricing api to get the prices of fish for stat tracking."""
    def __init__(self, settings_helper) -> None:
        self.settings_manager = settings_helper
        # Map of fish names to their item id and price
        self.fish_map = {
            'scalebelly_mackerel': {
                'id': 194730,
                'price': 0,},
            'temporal_dragonhead': {
                'id': 194969,
                'price': 0,},
            'thousandbite_piranha': {
                'id': 194966,
                'price': 0,},
            'islefin_dorado': {
                'id': 194970,
                'price': 0,},
            'cerulean_spinefish': {
                'id': 194968,
                'price': 0
            },
            'aileron_seamoth': {
                'id': 194967,
                'price': 0
            },
            'dull_spined_clam': {
                'id': 198395,
                'price': 0
            }
        }
        # Get TSM API token to fetch our pricing-api access token
        self.api_token = self.settings_manager.settings['tsm'].get('api_key')

        # Get access token to use with the pricing api
        self.access_token = self.get_access_token()

        # Cache fish prices
        self.cache_fish_prices()


    def get_access_token(self):
        url = ' https://auth.tradeskillmaster.com/oauth2/token'
        payload = {
            "client_id": "c260f00d-1071-409a-992f-dda2e5498536",
            "grant_type": "api_token",
            "scope": "app:pricing-api",
            "token": self.api_token
        }
        start_time = datetime.now()
        while get_duration(then=start_time, now=datetime.now(), interval='seconds') < 30:
            resp = requests.post(url, json=payload).json()
            if 'access_token' in resp:
                return resp['access_token']
            else:
                logger.warning(f"Couldn't get access_token. \n Response: {resp} \n Waiting 5 seconds and trying again.")
                time.sleep(5)
        sys.exit(logger.error(f"Timed out getting access token... Last Response: {resp}"))

    def get_item_stats(self, item_id: int):
        headers =  {"Authorization": f"Bearer {self.access_token}"}
        url = f"https://pricing-api.tradeskillmaster.com/region/1/item/{item_id}"  # `region/1` is North America retail. fish are shared across the region.
        item = requests.get(url, headers=headers).json()
        logger.debug(f"Item: {item}")
        return item

    def cache_fish_prices(self):
        for fish, fish_data in self.fish_map.items():
            # Make api call to get stats of fish
            fish_stats = self.get_item_stats(fish_data['id'])
            # Get price of fish from stats
            price = fish_stats['avgSalePrice'] / 10_000
            logger.debug(f"{fish} Cost: {fish_stats['avgSalePrice']}")
            logger.debug(f"Converted cost: {price}")
            # Cache fish price
            self.fish_map[fish]['price'] = price
            logger.success(f"Cached {fish} - {price}")


    def get_gold_earned(self, fish_map: dict):
        """Calculates total gold earned based on cached prices and fish looted"""
        logger.info("Getting total gold earned")
        for fish_name in self.fish_map:  # Only loop over fish in the TSMWrapper map (loot that actually has a price)
            fish_map[fish_name]['gold_earned'] = fish_map[fish_name]['loot_count'] * self.fish_map[fish_name]['price']
            logger.success(f"Total gold earned from {fish_name}: {fish_map[fish_name]['gold_earned']}g")
        return fish_map
