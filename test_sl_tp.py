"""Test script to place a trade with Stop Loss and Take Profit on Hyperliquid."""
import asyncio
from src.config import Config
from src.hyperliquid.client import HyperliquidClient


async def test_trade_with_sl_tp():
    """Place a small test trade with SL and TP."""
    config = Config()

    async with HyperliquidClient(config.hyperliquid) as client:
        asset = "BTC"

        # Place a VERY small BUY order (minimum size)
        size = 0.001  # Very small test size
        print(f"1. Placing MARKET BUY: {size} {asset}")

        try:
            order_result = await client.place_order(
                asset=asset,
                side="BUY",
                size=size,
                order_type="MARKET"
            )
            print(f"✅ Entry order filled: {order_result}")

            # Extract actual fill price and size
            fill_price = float(order_result.get('price', 0))
            fill_size = float(order_result.get('size', size))

            print(f"\nFilled: {fill_size} {asset} @ ${fill_price:,.2f}")

        except Exception as e:
            print(f"❌ Failed to place entry order: {e}")
            return

        # Calculate SL and TP prices
        sl_price = fill_price * 0.98  # 2% stop loss
        tp_price = fill_price * 1.04  # 4% take profit

        print(f"\n2. Placing Stop Loss @ ${sl_price:,.2f} (2% below entry)")

        try:
            sl_result = await client.place_trigger_order(
                asset=asset,
                side="SELL",  # Opposite of entry
                size=fill_size,
                trigger_price=sl_price,
                trigger_type="sl",
                is_market=True
            )
            print(f"✅ Stop Loss placed: {sl_result}")
        except Exception as e:
            print(f"❌ Failed to place Stop Loss: {e}")

        print(f"\n3. Placing Take Profit @ ${tp_price:,.2f} (4% above entry)")

        try:
            tp_result = await client.place_trigger_order(
                asset=asset,
                side="SELL",  # Opposite of entry
                size=fill_size,
                trigger_price=tp_price,
                trigger_type="tp",
                is_market=True
            )
            print(f"✅ Take Profit placed: {tp_result}")
        except Exception as e:
            print(f"❌ Failed to place Take Profit: {e}")

        print("\n" + "="*80)
        print("Test completed! Check Hyperliquid UI to verify:")
        print(f"- Entry: LONG {fill_size} {asset} @ ${fill_price:,.2f}")
        print(f"- Stop Loss: @ ${sl_price:,.2f}")
        print(f"- Take Profit: @ ${tp_price:,.2f}")
        print("="*80)


if __name__ == "__main__":
    asyncio.run(test_trade_with_sl_tp())
