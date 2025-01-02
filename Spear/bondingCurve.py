from web3 import Web3
import time
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

class BondingCurve(commands.Bot):
    def __init__(self):
        # Initialize properties
        self.RPC_URL = "https://base-mainnet.g.alchemy.com/v2/PkGfBEuppZDsdfWHSFOkYDJ9Y-VJjkxx"  # Replace with your RPC URL
        self.web3 = Web3(Web3.HTTPProvider(self.RPC_URL))
        self.PROXY_CONTRACT_ADDRESS = self.web3.to_checksum_address("0xf66dea7b3e897cd44a5a231c61b6b4423d613259")
        self.ABI = [
            {"inputs": [], "stateMutability": "nonpayable", "type": "constructor"},
            {"inputs": [{"internalType": "address", "name": "target", "type": "address"}], "name": "AddressEmptyCode", "type": "error"},
            {"inputs": [{"internalType": "address", "name": "account", "type": "address"}], "name": "AddressInsufficientBalance", "type": "error"},
            {"inputs": [], "name": "FailedInnerCall", "type": "error"},
            {"inputs": [], "name": "InvalidInitialization", "type": "error"},
            {"inputs": [], "name": "NotInitializing", "type": "error"},
            {"inputs": [{"internalType": "address", "name": "owner", "type": "address"}], "name": "OwnableInvalidOwner", "type": "error"},
            {"inputs": [{"internalType": "address", "name": "account", "type": "address"}], "name": "OwnableUnauthorizedAccount", "type": "error"},
            {"inputs": [], "name": "ReentrancyGuardReentrantCall", "type": "error"},
            {"inputs": [{"internalType": "address", "name": "token", "type": "address"}], "name": "SafeERC20FailedOperation", "type": "error"},
            {"anonymous": False, "inputs": [{"indexed": True, "internalType": "address", "name": "token", "type": "address"}, {"indexed": False, "internalType": "uint256", "name": "amount0", "type": "uint256"}, {"indexed": False, "internalType": "uint256", "name": "amount1", "type": "uint256"}], "name": "Deployed", "type": "event"},
            {"anonymous": False, "inputs": [{"indexed": True, "internalType": "address", "name": "token", "type": "address"}, {"indexed": False, "internalType": "address", "name": "agentToken", "type": "address"}], "name": "Graduated", "type": "event"},
            {"anonymous": False, "inputs": [{"indexed": False, "internalType": "uint64", "name": "version", "type": "uint64"}], "name": "Initialized", "type": "event"},
            {"anonymous": False, "inputs": [{"indexed": True, "internalType": "address", "name": "token", "type": "address"}, {"indexed": True, "internalType": "address", "name": "pair", "type": "address"}, {"indexed": False, "internalType": "uint256", "name": "", "type": "uint256"}], "name": "Launched", "type": "event"},
            {"anonymous": False, "inputs": [{"indexed": True, "internalType": "address", "name": "previousOwner", "type": "address"}, {"indexed": True, "internalType": "address", "name": "newOwner", "type": "address"}], "name": "OwnershipTransferred", "type": "event"},
            {"inputs": [], "name": "K", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "agentFactory", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "assetRate", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
            {"inputs": [{"internalType": "uint256", "name": "amountIn", "type": "uint256"}, {"internalType": "address", "name": "tokenAddress", "type": "address"}], "name": "buy", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "payable", "type": "function"},
            {"inputs": [], "name": "factory", "outputs": [{"internalType": "contract FFactory", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "fee", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
            {"inputs": [{"internalType": "address", "name": "account", "type": "address"}], "name": "getUserTokens", "outputs": [{"internalType": "address[]", "name": "", "type": "address[]"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "gradThreshold", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "initialSupply", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
            {"inputs": [{"internalType": "address", "name": "factory_", "type": "address"}, {"internalType": "address", "name": "router_", "type": "address"}, {"internalType": "address", "name": "feeTo_", "type": "address"}, {"internalType": "uint256", "name": "fee_", "type": "uint256"}, {"internalType": "uint256", "name": "initialSupply_", "type": "uint256"}, {"internalType": "uint256", "name": "assetRate_", "type": "uint256"}, {"internalType": "uint256", "name": "maxTx_", "type": "uint256"}, {"internalType": "address", "name": "agentFactory_", "type": "address"}, {"internalType": "uint256", "name": "gradThreshold_", "type": "uint256"}], "name": "initialize", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
            {"inputs": [{"internalType": "string", "name": "_name", "type": "string"}, {"internalType": "string", "name": "_ticker", "type": "string"}, {"internalType": "uint8[]", "name": "cores", "type": "uint8[]"}, {"internalType": "string", "name": "desc", "type": "string"}, {"internalType": "string", "name": "img", "type": "string"}, {"internalType": "string[4]", "name": "urls", "type": "string[4]"}, {"internalType": "uint256", "name": "purchaseAmount", "type": "uint256"}], "name": "launch", "outputs": [{"internalType": "address", "name": "", "type": "address"}, {"internalType": "address", "name": "", "type": "address"}, {"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"},
            {"inputs": [], "name": "maxTx", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "owner", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
            {"inputs": [{"internalType": "address", "name": "", "type": "address"}], "name": "profile", "outputs": [{"internalType": "address", "name": "user", "type": "address"}], "stateMutability": "view", "type": "function"},
            {"inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "name": "profiles", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "renounceOwnership", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
            {"inputs": [], "name": "router", "outputs": [{"internalType": "contract FRouter", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
            {"inputs": [{"internalType": "uint256", "name": "amountIn", "type": "uint256"}, {"internalType": "address", "name": "tokenAddress", "type": "address"}], "name": "sell", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
            {"inputs": [{"internalType": "uint256", "name": "newRate", "type": "uint256"}], "name": "setAssetRate", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
            {"inputs": [{"components": [{"internalType": "bytes32", "name": "tbaSalt", "type": "bytes32"}, {"internalType": "address", "name": "tbaImplementation", "type": "address"}, {"internalType": "uint32", "name": "daoVotingPeriod", "type": "uint32"}, {"internalType": "uint256", "name": "daoThreshold", "type": "uint256"}], "internalType": "struct Bonding.DeployParams", "name": "params", "type": "tuple"}], "name": "setDeployParams", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
            {"inputs": [{"internalType": "uint256", "name": "newFee", "type": "uint256"}, {"internalType": "address", "name": "newFeeTo", "type": "address"}], "name": "setFee", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
            {"inputs": [{"internalType": "uint256", "name": "newThreshold", "type": "uint256"}], "name": "setGradThreshold", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
            {"inputs": [{"internalType": "uint256", "name": "newSupply", "type": "uint256"}], "name": "setInitialSupply", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
            {"inputs": [{"internalType": "uint256", "name": "maxTx_", "type": "uint256"}], "name": "setMaxTx", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
            {"inputs": [{"internalType": "address", "name": "", "type": "address"}], "name": "tokenInfo", "outputs": [{"internalType": "address", "name": "creator", "type": "address"}, {"internalType": "address", "name": "token", "type": "address"}, {"internalType": "address", "name": "pair", "type": "address"}, {"internalType": "address", "name": "agentToken", "type": "address"}, {"components": [{"internalType": "address", "name": "token", "type": "address"}, {"internalType": "string", "name": "name", "type": "string"}, {"internalType": "string", "name": "_name", "type": "string"}, {"internalType": "string", "name": "ticker", "type": "string"}, {"internalType": "uint256", "name": "supply", "type": "uint256"}, {"internalType": "uint256", "name": "price", "type": "uint256"}, {"internalType": "uint256", "name": "marketCap", "type": "uint256"}, {"internalType": "uint256", "name": "liquidity", "type": "uint256"}, {"internalType": "uint256", "name": "volume", "type": "uint256"}, {"internalType": "uint256", "name": "volume24H", "type": "uint256"}, {"internalType": "uint256", "name": "prevPrice", "type": "uint256"}, {"internalType": "uint256", "name": "lastUpdated", "type": "uint256"}], "internalType": "struct Bonding.Data", "name": "data", "type": "tuple"}, {"internalType": "string", "name": "description", "type": "string"}, {"internalType": "string", "name": "image", "type": "string"}, {"internalType": "string", "name": "twitter", "type": "string"}, {"internalType": "string", "name": "telegram", "type": "string"}, {"internalType": "string", "name": "youtube", "type": "string"}, {"internalType": "string", "name": "website", "type": "string"}, {"internalType": "bool", "name": "trading", "type": "bool"}, {"internalType": "bool", "name": "tradingOnUniswap", "type": "bool"}], "stateMutability": "view", "type": "function"},
            {"inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "name": "tokenInfos", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
            {"inputs": [{"internalType": "address", "name": "newOwner", "type": "address"}], "name": "transferOwnership", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
            {"inputs": [{"internalType": "address", "name": "srcTokenAddress", "type": "address"}, {"internalType": "address[]", "name": "accounts", "type": "address[]"}], "name": "unwrapToken", "outputs": [], "stateMutability": "nonpayable", "type": "function"}
        ]
        self.contract = self.web3.eth.contract(address=self.PROXY_CONTRACT_ADDRESS, abi=self.ABI)
        self.launched_event = '0x714aa39317ad9a7a7a99db52b44490da5d068a0b2710fffb1a1282ad3cadae1f'
        self.graduated_event = '0x381d54fa425631e6266af114239150fae1d5db67bb65b4fa9ecc65013107e07e'
        self.DISCORD_CHANNEL_ID = '1324219120530493552'

    # Extract token address from topics
    def extract_token_address(self, topic):
        return self.web3.to_checksum_address("0x" + topic.hex()[-40:])

    async def setup_hook(self):
        print("🚀 Setup hook called...")
        try:
            self.listen_to_events.start()
            print("✅ Tracking loop started!")
        except Exception as e:
            print(f"❌ ERROR STARTING TRACKING LOOP: {e}")

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

    # Main loop
    async def listen_to_events(self):
        await self.send_alert("Onchain sleuth is up bitchessss.....")
        event_filter = self.web3.eth.filter({'address': self.PROXY_CONTRACT_ADDRESS})
        while True:
            events = event_filter.get_new_entries()
            for event in events:
                try:
                    if "0x" + event['topics'][0].hex() == self.launched_event:
                        token_address = self.extract_token_address(event['topics'][1])
                        print(f"[Launched] Token: {token_address}")
                        await self.send_alert(message)
                    elif "0x" + event['topics'][0].hex() == self.graduated_event:
                        print(event)
                        token_address = self.extract_token_address(event['data'])
                        print(f"[Graduated] Token: {token_address}")
                        message = f"[Graduated] Token: {token_address}"
                        await self.send_alert(message)
                except Exception as e:
                    print(f"Error processing event: {e}")
            time.sleep(2)

    @commands.Cog.listener()
    async def on_ready(self):
        print("🤖 BOT IS READY AND CONNECTED TO DISCORD")
        channel = self.get_channel(self.DISCORD_CHANNEL_ID)
        if channel:
            await channel.send("Bot is online and monitoring!")

def start_server():
    PORT = int(os.getenv('PORT', 10001))
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()

def main():
    import threading
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True  # This ensures the thread closes when the main program exits
    server_thread.start()
    bot = BondingCurve()
    bot.run(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    print("🚀 MAIN FUNCTION STARTING")
    main()