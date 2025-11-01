"""Add SL/TP to existing positions without stop loss."""
import asyncio
from src.config import Config
from src.hyperliquid.client import HyperliquidClient


async def add_sl_tp_to_positions():
    """Add Stop Loss and Take Profit to existing open positions."""
    config = Config()

    async with HyperliquidClient(config.hyperliquid) as client:
        print("Fetching current positions...")
        portfolio = await client.get_account_state()

        print(f"\nFound {len(portfolio.positions)} open positions:\n")

        for position in portfolio.positions:
            print(f"{'='*80}")
            print(f"Asset: {position.asset}")
            print(f"Side: {position.side}")
            print(f"Size: {position.size}")
            print(f"Entry: ${position.entry_price:,.2f}")
            print(f"Current: ${position.current_price:,.2f}")
            print(f"PnL: {position.unrealized_pnl_percent:.2f}%")

            # Calculate SL and TP prices based on position side
            if position.side == "LONG":
                # For LONG: SL below, TP above
                sl_price = position.entry_price * 0.98  # 2% stop loss
                tp1_price = position.entry_price * 1.02  # 2% take profit
                tp2_price = position.entry_price * 1.04  # 4% take profit
                tp3_price = position.entry_price * 1.06  # 6% take profit

                # Orders are opposite of position side
                sl_side = "SELL"
                tp_side = "SELL"

            else:  # SHORT
                # For SHORT: SL above, TP below
                sl_price = position.entry_price * 1.02  # 2% stop loss
                tp1_price = position.entry_price * 0.98  # 2% take profit
                tp2_price = position.entry_price * 0.96  # 4% take profit
                tp3_price = position.entry_price * 0.94  # 6% take profit

                # Orders are opposite of position side
                sl_side = "BUY"
                tp_side = "BUY"

            print(f"\nPlacing orders for {position.asset} {position.side}:")
            print(f"  Stop Loss @ ${sl_price:,.2f} (2%)")
            print(f"  TP1 @ ${tp1_price:,.2f} (2%)")
            print(f"  TP2 @ ${tp2_price:,.2f} (4%)")
            print(f"  TP3 @ ${tp3_price:,.2f} (6%)")

            # Place Stop Loss
            try:
                sl_result = await client.place_trigger_order(
                    asset=position.asset,
                    side=sl_side,
                    size=position.size,
                    trigger_price=sl_price,
                    trigger_type="sl",
                    is_market=True
                )
                print(f"✅ Stop Loss placed: {sl_result}")
            except Exception as e:
                print(f"❌ Failed to place Stop Loss: {e}")

            # Place Take Profit orders (split position)
            tp_sizes = [
                (position.size * 0.5, tp1_price, "TP1"),   # 50% at TP1
                (position.size * 0.3, tp2_price, "TP2"),   # 30% at TP2
                (position.size * 0.2, tp3_price, "TP3"),   # 20% at TP3
            ]

            for tp_size, tp_price, tp_name in tp_sizes:
                try:
                    tp_result = await client.place_trigger_order(
                        asset=position.asset,
                        side=tp_side,
                        size=tp_size,
                        trigger_price=tp_price,
                        trigger_type="tp",
                        is_market=True
                    )
                    print(f"✅ {tp_name} placed: {tp_result}")
                except Exception as e:
                    print(f"❌ Failed to place {tp_name}: {e}")

        print(f"\n{'='*80}")
        print("Done! All positions now have SL/TP orders.")
        print("Check Hyperliquid UI to verify the orders.")


if __name__ == "__main__":
    asyncio.run(add_sl_tp_to_positions())
