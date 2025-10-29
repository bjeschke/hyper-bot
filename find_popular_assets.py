import asyncio
import aiohttp
import sys
sys.path.insert(0, '/Users/benjaminjeschke/Documents/apps/hyper-bot/hyper-bot')

from src.hyperliquid.client import HyperliquidClient
from src.config import config

async def main():
    client = HyperliquidClient(config.hyperliquid)
    
    async with client:
        # Get meta info
        response = await client._request("POST", "/info", {"type": "meta"})
        
        # Filter for major coins
        popular = []
        for asset in response.get('universe', []):
            name = asset.get('name', '')
            # Look for major cryptos
            if name in ['BTC', 'ETH', 'SOL', 'BNB', 'DOGE', 'ADA', 'AVAX', 'DOT', 'LINK', 'MATIC', 'UNI', 'ATOM', 'LTC', 'BCH', 'XLM', 'ALGO', 'VET', 'FIL', 'TRX', 'ETC', 'HBAR', 'APT', 'ARB', 'OP', 'SUI', 'SEI', 'INJ', 'TIA', 'PEPE', 'WIF', 'BONK', 'SHIB']:
                popular.append(name)
        
        popular.sort()
        
        print("Popular Crypto Assets auf Hyperliquid:")
        print("=" * 50)
        for asset in popular:
            print(f"✅ {asset}")
        
        print(f"\nTotal: {len(popular)} major assets")

asyncio.run(main())
