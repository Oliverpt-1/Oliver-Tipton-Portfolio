import discord
from discord.ext import commands, tasks
import requests
import datetime
from typing import Dict, List
import os
from dotenv import load_dotenv

class WhaleTracker(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        # Load environment variables
        load_dotenv()
        
        # Solscan configuration
        self.solscan_api_key = os.getenv('SOLSCAN_API_KEY')
        self.headers = {
            'token': self.solscan_api_key,
            'accept': 'application/json'
        }
        self.base_url = "https://pro-api.solscan.io/v2.0"
        
        # Discord channel configuration
        self.DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
        
        # Track last checked timestamps for each wallet
        self.last_checked = {}

    async def setup_hook(self):
        # Start the tracking loop when the bot is ready
        self.track_whales.start()

    def get_balance_changes(self, wallet_address: str, since_timestamp: int) -> List[Dict]:
        """Get recent balance changes for a wallet"""
        endpoint = f"{self.base_url}/account/balance_change"
        params = {
            'address': wallet_address,
            'page': 1,
            'page_size': 20,
            'sort_by': 'block_time',
            'sort_order': 'desc'
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('success') and 'data' in data:
                return [change for change in data['data'] 
                       if change['block_time'] > since_timestamp]
            
        except Exception as e:
            print(f"Error fetching balance changes for {wallet_address}: {e}")
        
        return []

    def get_token_price(self, token_address: str) -> float:
        """Get current token price"""
        endpoint = f"{self.base_url}/token/meta"
        params = {'address': token_address}
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('success') and 'data' in data:
                return float(data['data'].get('price', 0))
            
        except Exception as e:
            print(f"Error fetching token price for {token_address}: {e}")
        
        return 0

    async def send_alert(self, message: str):
        """Send Discord alert"""
        try:
            channel = self.get_channel(self.DISCORD_CHANNEL_ID)
            if channel:
                await channel.send(message)
                print(f"Alert sent: {message}")
            else:
                print("Could not find Discord channel")
        except Exception as e:
            print(f"Error sending Discord alert: {e}")

    async def monitor_wallet(self, wallet_address: str):
        """Monitor a single wallet for significant changes"""
        current_time = int(datetime.datetime.now().timestamp())
        last_check = self.last_checked.get(wallet_address, current_time - 300)
        
        changes = self.get_balance_changes(wallet_address, last_check)
        
        for change in changes:
            token_address = change['token_address']
            amount = abs(float(change['amount'])) / (10 ** change['token_decimals'])
            price = self.get_token_price(token_address)
            value_usd = amount * price
            
            if value_usd >= 1000:  # Alert threshold
                direction = "bought" if change['change_type'] == 'inc' else "sold"
                symbol = change.get('token_symbol', 'Unknown Token')
                
                message = (
                    f"🐋 **Whale Alert!** 🐋\n"
                    f"**Wallet:** {wallet_address[:8]}...{wallet_address[-6:]}\n"
                    f"**Action:** {direction.title()} {amount:.2f} {symbol}\n"
                    f"**Value:** ${value_usd:,.2f}\n"
                    f"**Time:** {datetime.datetime.fromtimestamp(change['block_time']).strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
                await self.send_alert(message)
        
        self.last_checked[wallet_address] = current_time

    @tasks.loop(minutes=1)
    async def track_whales(self):
        """Check whale wallets every minute"""
        try:
            with open('whale_addresses.txt', 'r') as f:
                whale_addresses = [addr.strip() for addr in f.readlines() if addr.strip()]
                
            for address in whale_addresses:
                await self.monitor_wallet(address)
                await asyncio.sleep(1)  # Rate limiting between wallets
                
        except Exception as e:
            print(f"Error in tracking loop: {e}")

    @track_whales.before_loop
    async def before_tracking(self):
        """Wait until the bot is ready before starting the tracking loop"""
        await self.wait_until_ready()

def main():
    # Create and run the bot
    bot = WhaleTracker()
    bot.run(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    main()
