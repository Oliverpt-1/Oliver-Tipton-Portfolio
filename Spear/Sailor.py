import requests
import time
import datetime
from typing import Dict, List
from twilio.rest import Client
import os
from dotenv import load_dotenv

class WhaleTracker:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Solscan configuration
        self.solscan_api_key = os.getenv('SOLSCAN_API_KEY')
        self.headers = {
            'token': self.solscan_api_key,
            'accept': 'application/json'
        }
        self.base_url = "https://pro-api.solscan.io/v2.0"
        
        # Twilio configuration
        self.twilio_client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        self.twilio_from_number = os.getenv('TWILIO_FROM_NUMBER')
        self.twilio_to_number = os.getenv('TWILIO_TO_NUMBER')
        
        # Track last checked timestamps for each wallet
        self.last_checked = {}

    def get_balance_changes(self, wallet_address: str, since_timestamp: int) -> List[Dict]:
        """Get recent balance changes for a wallet"""
        endpoint = f"{self.base_url}/account/balance_change"
        params = {
            'address': wallet_address,
            'page': 1,
            'page_size': 20,
            'sort_by': 'block_time',
            'sort_order': 'desc'  # Get most recent first
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('success') and 'data' in data:
                # Filter changes after since_timestamp
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

    def send_alert(self, message: str):
        """Send SMS alert via Twilio"""
        try:
            self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_from_number,
                to=self.twilio_to_number
            )
            print(f"Alert sent: {message}")
        except Exception as e:
            print(f"Error sending SMS alert: {e}")

    def monitor_wallet(self, wallet_address: str):
        """Monitor a single wallet for significant changes"""
        current_time = int(time.time())
        last_check = self.last_checked.get(wallet_address, current_time - 300)  # Default to 5 mins ago
        
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
                    f"🐋 Whale Alert! 🐋\n"
                    f"Wallet: {wallet_address[:8]}...{wallet_address[-6:]}\n"
                    f"{direction.title()} {amount:.2f} {symbol}\n"
                    f"Value: ${value_usd:,.2f}\n"
                    f"Time: {datetime.datetime.fromtimestamp(change['block_time']).strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
                self.send_alert(message)
        
        self.last_checked[wallet_address] = current_time

def main():
    tracker = WhaleTracker()
    
    # Read whale addresses from a file
    try:
        with open('whale_addresses.txt', 'r') as f:
            whale_addresses = [addr.strip() for addr in f.readlines() if addr.strip()]
    except FileNotFoundError:
        print("Please create whale_addresses.txt with one wallet address per line")
        return

    print(f"Starting whale tracker for {len(whale_addresses)} addresses...")
    
    while True:
        for address in whale_addresses:
            tracker.monitor_wallet(address)
            time.sleep(1)  # Rate limiting between wallets
        
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()
