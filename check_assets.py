import asyncio
import aiohttp
import os
import sys
sys.path.insert(0, '/Users/benjaminjeschke/Documents/apps/hyper-bot/hyper-bot')

from src.hyperliquid.client import HyperliquidClient
from src.config import config

async def main():
    client = HyperliquidClient(config.hyperliquid)
    
    async with client:
        # Get all available markets
        response = await client._request("POST", "/info", {"type": "allMids"})
        
        print("Available Assets on Hyperliquid:")
        print("=" * 50)
        
        assets = list(response.keys())
        assets.sort()
        
        # Check our wanted assets
        wanted = ["BTC", "ETH", "XRP", "SOL", "BNB"]
        
        for asset in wanted:
            status = "✅" if asset in assets else "❌"
            print(f"{status} {asset}")
        
        print("\n" + "=" * 50)
        print(f"Total available: {len(assets)} assets")
        print("\nTop 20 assets by volume:")
        for i, asset in enumerate(assets[:20], 1):
            print(f"{i:2}. {asset}")

asyncio.run(main())
