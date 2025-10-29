"""Test trade on Hyperliquid Testnet to verify API works."""
import asyncio
import sys
sys.path.insert(0, '/Users/benjaminjeschke/Documents/apps/hyper-bot/hyper-bot')

from src.hyperliquid.client import HyperliquidClient
from src.config import config
from loguru import logger

async def main():
    logger.info("=" * 80)
    logger.info("TESTNET TRADE TEST")
    logger.info("=" * 80)
    
    client = HyperliquidClient(config.hyperliquid)
    
    async with client:
        # 1. Check current balance
        logger.info("\n1. Checking portfolio...")
        portfolio = await client.get_account_state()
        logger.info(f"   Balance: ${portfolio.total_value:,.2f}")
        logger.info(f"   Available: ${portfolio.available_balance:,.2f}")
        
        # 2. Get BTC price
        logger.info("\n2. Getting BTC price...")
        ticker = await client.get_ticker("BTC")
        btc_price = float(ticker.get('lastPx', 0))
        logger.info(f"   BTC Price: ${btc_price:,.2f}")
        
        # 3. Place small LONG order (very small for safety)
        # Let's buy ~$10 worth of BTC
        quantity = 10 / btc_price  # ~$10 worth
        
        logger.info(f"\n3. Placing TEST LONG order...")
        logger.info(f"   Asset: BTC")
        logger.info(f"   Side: BUY (LONG)")
        logger.info(f"   Quantity: {quantity:.6f} BTC (~$10)")
        logger.info(f"   Type: MARKET")
        
        try:
            result = await client.place_order(
                asset="BTC",
                side="BUY",
                size=quantity,
                order_type="MARKET"
            )
            
            logger.success(f"\n✅ ORDER PLACED SUCCESSFULLY!")
            logger.info(f"   Result: {result}")
            
        except Exception as e:
            logger.error(f"\n❌ ORDER FAILED: {e}")
            return
        
        # 4. Wait a moment for order to fill
        await asyncio.sleep(2)
        
        # 5. Check positions
        logger.info("\n4. Checking positions...")
        portfolio = await client.get_account_state()
        
        if portfolio.positions:
            logger.success(f"   Found {len(portfolio.positions)} position(s):")
            for pos in portfolio.positions:
                logger.info(f"   - {pos.side} {pos.size} {pos.asset} @ ${pos.entry_price:,.2f}")
                logger.info(f"     P&L: ${pos.unrealized_pnl:,.2f} ({pos.unrealized_pnl_percent:+.2f}%)")
        else:
            logger.warning("   No positions found (order may be pending)")
        
        logger.info(f"\n   New Balance: ${portfolio.total_value:,.2f}")
        
        # 6. Ask if user wants to close
        logger.info("\n" + "=" * 80)
        logger.info("TEST TRADE COMPLETED!")
        logger.info("=" * 80)
        logger.info("\nPosition is now open on Testnet.")
        logger.info("The main bot will monitor and manage it.")
        logger.info("\nTo close manually, run: python test_close_position.py")

asyncio.run(main())
