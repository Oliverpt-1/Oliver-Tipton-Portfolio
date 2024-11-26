import requests
import time
from typing import List, Dict
import os


class TokenAnalyzer:
    def __init__(self):
        self.solscan_api_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjcmVhdGVkQXQiOjE3MzIwNDMyMDgyMzYsImVtYWlsIjoibXJvbGl2ZXJwdEBnbWFpbC5jb20iLCJhY3Rpb24iOiJ0b2tlbi1hcGkiLCJhcGlWZXJzaW9uIjoidjIiLCJpYXQiOjE3MzIwNDMyMDh9.UWWlKFfc2To1kmeepReENIWJhvxtU6sdA5FZkrjUsuc'
        self.headers = {
            'token': self.solscan_api_key,
            'accept': 'application/json'
        }
        self.base_url = "https://pro-api.solscan.io/v2.0"

    def get_top_holders(self, token_address: str, limit: int = 10) -> List[Dict]:
        """Get top holders for a token"""
        endpoint = f"{self.base_url}/token/holders"
        params = {
            'address': token_address,
            'page': 1,
            'page_size': 10
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('success') and 'data' in data and 'items' in data['data']:
                holders = []
                for holder in data['data']['items']:
                    holders.append({
                        'address': holder['owner'],
                        'amount': holder['amount'],
                        'decimals': holder['decimals'],
                        'rank': holder['rank']
                    })
                return holders[:limit]
            return []
            
        except Exception as e:
            print(f"Unexpected Error: {e}")
            return []

    def get_wallet_holdings(self, wallet_address: str) -> List[Dict]:
        """Get top holdings for a wallet"""
        endpoint = f"{self.base_url}/account/token-accounts"
        params = {
            'address': wallet_address,
            'type': 'token',
            'page': 1,
            'page_size': 10
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('success') and 'data' in data:
                holdings = []
                for token in data['data']:
                    holdings.append({
                        'token_account': token['token_account'],
                        'address': token['token_address'],
                        'amount': token['amount'],
                        'decimals': token['token_decimals'],
                        'owner': token['owner']
                    })
                return holdings
            else:
                return []
            
        except Exception as e:
            print(f"Debug: Exception occurred: {str(e)}")
            print(f"Debug: Exception type: {type(e)}")
            if hasattr(e, 'response'):
                print(f"Debug: Error response: {e.response.text}")
            return []
    
    def get_token_market_data(self, token_address: str) -> Dict:
        """Get market data for a token"""
        endpoint = f"{self.base_url}/token/meta"
        params = {'address': token_address}
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('success') and 'data' in data:
                return data['data']
            return None
            
        except Exception as e:
            print(f"Error fetching market data for {token_address}: {e}")
            return None

def main():
    try:
        analyzer = TokenAnalyzer()
        
        # Read wallets from wallet.txt
        with open('Spear/wallet.txt', 'r') as file:
            content = file.read()
            # Extract wallet addresses using string manipulation
            wallets = [line.split('Wallet: ')[1].strip() 
                      for line in content.split('\n') 
                      if line.startswith('Wallet: ')]
        
        print(f"\nAnalyzing {len(wallets)} wallets for interesting positions...")
        interesting_positions_found = False
        
        for wallet_address in wallets:
            print(f"\nChecking wallet: {wallet_address}")
            holdings = analyzer.get_wallet_holdings(wallet_address)
            
            if holdings:
                for token in holdings:
                    market_data = analyzer.get_token_market_data(token['address'])
                    if market_data and 'market_cap' in market_data:
                        market_cap = float(market_data['market_cap'])
                        
                        if 10000 <= market_cap <= 5000000:  # Market cap between 10k and 5M
                            token_amount = float(token['amount']) / (10 ** token['decimals'])
                            price = float(market_data.get('price', 0))
                            position_value = token_amount * price
                            
                            if position_value >= 1000:  # Position worth $1000 or more
                                if not interesting_positions_found:
                                    print("\nFound interesting positions:")
                                    interesting_positions_found = True
                                
                                print(f"\nWallet: {wallet_address}")
                                print(f"- Token: {market_data.get('symbol', 'Unknown')}")
                                print(f"  Contract: {token['address']}")
                                print(f"  Market Cap: ${market_cap:,.2f}")
                                print(f"  Position Value: ${position_value:,.2f}")
                                print(f"  Amount: {token_amount:,.2f}")
                                print("-" * 50)
            
            time.sleep(1)  # Rate limiting between wallets
        
        if not interesting_positions_found:
            print("\nNo interesting positions found matching criteria.")
            
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()