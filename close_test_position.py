"""Close the test BTC position."""
import sys
sys.path.insert(0, '/Users/benjaminjeschke/Documents/apps/hyper-bot/hyper-bot')

from eth_account import Account
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
from src.config import config

def main():
    print("=" * 80)
    print("CLOSING TEST POSITION")
    print("=" * 80)

    # Setup
    base_url = constants.TESTNET_API_URL
    account = Account.from_key(config.hyperliquid.private_key)
    info = Info(base_url, skip_ws=True)
    exchange = Exchange(account, base_url)

    # Check current positions
    print("\n1. Checking positions...")
    user_state = info.user_state(account.address)
    positions = user_state.get("assetPositions", [])

    if not positions:
        print("   No positions found!")
        return

    print(f"   Found {len(positions)} position(s)")

    # Close all positions
    for pos in positions:
        position_data = pos["position"]
        coin = position_data["coin"]
        size = abs(float(position_data["szi"]))

        print(f"\n2. Closing {coin} position...")
        print(f"   Size: {size}")

        # Get current price
        all_mids = info.all_mids()
        current_price = float(all_mids[coin])

        # Close with market order (sell if long, buy if short)
        is_long = float(position_data["szi"]) > 0
        is_buy = not is_long  # Buy to close short, sell to close long

        # Use slippage buffer - reversed logic (sell needs lower price, buy needs higher)
        close_price = round(current_price * 1.05) if is_buy else round(current_price * 0.95)

        try:
            result = exchange.order(
                name=coin,
                is_buy=is_buy,
                sz=size,
                limit_px=close_price,
                order_type={"limit": {"tif": "Ioc"}},
                reduce_only=True  # Important: only close, don't flip
            )

            print(f"   ✅ Close order sent: {result['status']}")

            if result["status"] == "ok":
                statuses = result["response"]["data"].get("statuses", [])
                if statuses and "filled" in statuses[0]:
                    filled = statuses[0]["filled"]
                    print(f"   Closed: {filled['totalSz']} at ${filled['avgPx']}")

        except Exception as e:
            print(f"   ❌ Error closing position: {e}")

    # Check final state
    import time
    time.sleep(2)

    print("\n3. Final state...")
    user_state = info.user_state(account.address)
    final_balance = float(user_state["marginSummary"]["accountValue"])
    positions = user_state.get("assetPositions", [])

    print(f"   Balance: ${final_balance:,.2f}")
    print(f"   Open Positions: {len(positions)}")

    print("\n" + "=" * 80)
    print("✅ DONE!")
    print("=" * 80)

if __name__ == "__main__":
    main()
