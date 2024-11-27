import discord
from discord.ext import commands, tasks
import requests
import datetime
from typing import Dict, List
import os
from dotenv import load_dotenv
import http.server
import socketserver
import asyncio

class WhaleTracker(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        # Solscan configuration
        self.solscan_api_key = os.getenv('SOLSCAN_API_KEY')
        self.headers = {
            'token': self.solscan_api_key,
            'accept': 'application/json'
        }
        self.base_url = "https://pro-api.solscan.io/v2.0"
        
        # Discord channel configuration
        self.DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))

    async def setup_hook(self):
        print("🚀 Setup hook called...")
        try:
            self.track_whales.start()
            print("✅ Tracking loop started!")
        except Exception as e:
            print(f"❌ ERROR STARTING TRACKING LOOP: {e}")

    def get_balance_changes(self, wallet_address: str) -> Dict:
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
            print(f"Making API call to Solscan for {wallet_address[:8]}...")
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
                
        except Exception as e:
            print(f"API Error: {e}")
            return {"status": "error", "message": str(e)}

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

    def get_token_price(self, token_address: str) -> float:
        """Get token price from Solscan"""
        endpoint = f"{self.base_url}/token/price"
        today = datetime.datetime.now().strftime('%Y%m%d')

        params = {
            'address': token_address,
            'time[]': today
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data['data'][0]['price']
        except Exception as e:
            print(f"Error getting token price: {e}")
            return 0

    async def monitor_wallet(self, wallet_address: str):
        """Monitor a single wallet for significant changes"""
        try:
            await self.send_alert(f"👀 Checking wallet: {wallet_address[:8]}...")
            response = self.get_balance_changes(wallet_address)
            await self.send_alert(f"📥 Got response for {wallet_address[:8]}: {response.get('success', False)}")
            
            if response['success'] and 'data' in response:
                transactions = response['data']
                await self.send_alert(f"📊 Found {len(transactions)} transactions for {wallet_address[:8]}")
                recent_txs = []
                
                for tx in transactions:
                    tx_time = datetime.datetime.fromtimestamp(tx.get('block_time', 0))
                    current_time = datetime.datetime.now()
                    time_diff = current_time - tx_time
                    
                    await self.send_alert(f"⏰ Transaction time: {tx_time}, Time diff: {time_diff.total_seconds()/60:.2f} minutes")
                    
                    # Check if transaction is from the last 5 minutes
                    if tx_time > current_time - datetime.timedelta(minutes=5):
                        raw_amount = float(tx.get('amount', 0))
                        token_decimals = tx.get('token_decimals', 9)
                        token_address = tx.get('token_address', 'Unknown')
                        
                        # Get current token price
                        price_usd = self.get_token_price(token_address) if token_address else 0
                        
                        # Calculate actual amount and USD value
                        actual_amount = raw_amount / (10 ** token_decimals)
                        usd_value = actual_amount * price_usd
                        
                        recent_txs.append((actual_amount, usd_value, tx_time, token_address))
                
                if recent_txs:
                    await self.send_alert(f"✨ Found {len(recent_txs)} recent transactions for {wallet_address[:8]}")
                    # Sort by USD value, largest first
                    recent_txs.sort(key=lambda x: x[1], reverse=True)
                    
                    for amount, usd_value, tx_time, token_address in recent_txs:
                        message = (
                            f"💰 **Transaction Alert** 💰\n"
                            f"**Wallet:** {wallet_address[:8]}...{wallet_address[-6:]}\n"
                            f"**Token:** {token_address}\n"
                            f"**Amount:** {amount:.4f} (USD: ${usd_value:.2f})\n"
                            f"**Time:** {tx_time.strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                        await self.send_alert(message)
                else:
                    await self.send_alert(f"😴 No recent transactions found for {wallet_address[:8]}")
            
        except Exception as e:
            await self.send_alert(f"❌ Error monitoring wallet {wallet_address}: {e}")

    @tasks.loop(minutes=5)
    async def track_whales(self):
        """Check whale wallets every minute"""
        print("🔄 TRACK_WHALES LOOP RUNNING")
        try:
            print(f"\n[{datetime.datetime.now()}] 🔍 Starting wallet check cycle...")
            await self.send_alert("🔍 Checking wallets...")
            current_dir = os.path.dirname(os.path.abspath(__file__))
            wallet_file = os.path.join(current_dir, 'wallet.txt')

            with open(wallet_file, 'r') as f:
                whale_addresses = [line.strip() for line in f.readlines() if line.strip()]
                
            await self.send_alert(f"📋 Found {len(whale_addresses)} wallets to monitor")
            
            for address in whale_addresses:
                await self.monitor_wallet(address)
                
            print(f"✅ Completed check cycle at {datetime.datetime.now()}\n")
                
        except Exception as e:
            print(f"❌ Error in tracking loop: {e}")

    @track_whales.before_loop
    async def before_tracking(self):
        """Wait until the bot is ready before starting the tracking loop"""
        await self.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self):
        print("🤖 BOT IS READY AND CONNECTED TO DISCORD")
        channel = self.get_channel(self.DISCORD_CHANNEL_ID)
        if channel:
            await channel.send("Bot is online and monitoring!")

def start_server():
    PORT = int(os.getenv('PORT', 10000))
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()

def main():
    import threading
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True  # This ensures the thread closes when the main program exits
    server_thread.start()
    bot = WhaleTracker()
    bot.run(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    print("🚀 MAIN FUNCTION STARTING")
    main()
