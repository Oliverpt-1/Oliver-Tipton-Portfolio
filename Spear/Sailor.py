import discord
from discord.ext import commands, tasks
import requests
import datetime
from typing import Dict, List
import os
from dotenv import load_dotenv
import http.server
import asyncio
import socketserver

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

    def format_amount(self, amount, decimals, price_usd=None):
        """Convert raw amount to proper decimal value and USD if available"""
        actual_amount = float(amount) / (10 ** decimals)
        if price_usd:
            usd_value = actual_amount * price_usd
            return f"{actual_amount:.4f} (${usd_value:.2f})", usd_value
        return f"{actual_amount:.4f}", None

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
            print(f"API Status Code: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API Error Response: {response.text}")
                return {"status": "error", "code": response.status_code}
                
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
        endpoint = f"{self.base_url}/token/meta"
        params = {
            'token': token_address
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {}).get('price_usd', 0)
            return 0
        except Exception as e:
            print(f"Error getting token price: {e}")
            return 0

    async def monitor_wallet(self, wallet_address: str):
        """Monitor a single wallet for significant changes"""
        try:
            response = self.get_balance_changes(wallet_address)
            
            if response.get('success') and 'data' in response:
                transactions = response['data']
                significant_txs = []
                
                for tx in transactions:
                    tx_time = datetime.datetime.fromtimestamp(tx.get('block_time', 0))
                    
                    # Check if transaction is from the last minute
                    if tx_time > datetime.datetime.fromtimestamp(self.last_checked.get(wallet_address, 0)):
                        raw_amount = float(tx.get('amount', 0))
                        decimals = tx.get('decimals', 9)  # default to 9 for SOL
                        token = tx.get('token_symbol', 'Unknown')
                        token_address = tx.get('token_address')
                        
                        # Get current token price
                        price_usd = self.get_token_price(token_address) if token_address else 0
                        
                        formatted_amount, usd_value = self.format_amount(raw_amount, decimals, price_usd)
                        
                        # Only add transactions worth more than $500
                        if usd_value and abs(usd_value) > 500:
                            significant_txs.append((formatted_amount, token, tx_time, abs(usd_value)))
                
                if significant_txs:
                    # Sort by USD value, largest first
                    significant_txs.sort(key=lambda x: x[3], reverse=True)
                    
                    for amount, token, tx_time, usd_value in significant_txs:
                        message = (
                            f"🐋 **Whale Alert!** 🐋\n"
                            f"**Wallet:** {wallet_address[:8]}...{wallet_address[-6:]}\n"
                            f"**Amount:** {amount} {token}\n"
                            f"**Time:** {tx_time.strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                        await self.send_alert(message)
            
            # Update last checked time
            self.last_checked[wallet_address] = int(datetime.datetime.now().timestamp())
            
        except Exception as e:
            print(f"Error monitoring wallet {wallet_address}: {e}")

    @tasks.loop(minutes=5)
    async def track_whales(self):
        """Check whale wallets every minute"""
        try:
            print(f"\n[{datetime.datetime.now()}] 🔍 Starting wallet check cycle...")
            
            with open('Spear/wallet.txt', 'r') as f:
                whale_addresses = [line.strip() for line in f.readlines() if line.strip()]
                
            print(f"📋 Found {len(whale_addresses)} wallets to monitor")
            
            for address in whale_addresses:
                await self.monitor_wallet(address)
                await asyncio.sleep(1)  # Rate limiting between wallets
                
            print(f"✅ Completed check cycle at {datetime.datetime.now()}\n")
                
        except Exception as e:
            print(f"❌ Error in tracking loop: {e}")

    @track_whales.before_loop
    async def before_tracking(self):
        """Wait until the bot is ready before starting the tracking loop"""
        await self.wait_until_ready()

def start_server():
    PORT = int(os.getenv('PORT', 10000))
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()

def main():
    # Create and run the bot in a separate thread
    import threading
    bot = WhaleTracker()
    bot_thread = threading.Thread(target=bot.run, args=(os.getenv('DISCORD_TOKEN'),))
    bot_thread.start()
    
    # Start the HTTP server
    start_server()

if __name__ == "__main__":
    main()
