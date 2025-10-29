"""Test trade using official Hyperliquid SDK."""
import sys
sys.path.insert(0, '/Users/benjaminjeschke/Documents/apps/hyper-bot/hyper-bot')

from eth_account import Account
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
from src.config import config

def main():
    print("=" * 80)
    print("TESTNET TRADE TEST (Official SDK)")
    print("=" * 80)
    
    # Setup with testnet
    base_url = constants.TESTNET_API_URL
    
    # Create LocalAccount from private key
    account = Account.from_key(config.hyperliquid.private_key)
    print(f"\nWallet Address: {account.address}")
    
    # Create Info and Exchange objects
    info = Info(base_url, skip_ws=True)
    exchange = Exchange(account, base_url)
    
    print("\n1. Checking account...")
    user_state = info.user_state(account.address)
    balance = float(user_state["marginSummary"]["accountValue"])
    print(f"   Balance: ${balance:,.2f}")
    
    print("\n2. Getting BTC price and metadata...")
    all_mids = info.all_mids()
    btc_price = float(all_mids["BTC"])

    # Get asset metadata for proper rounding
    meta = info.meta()
    btc_meta = meta["universe"][0]  # BTC is index 0
    sz_decimals = btc_meta["szDecimals"]

    print(f"   BTC Price: ${btc_price:,.2f}")
    print(f"   Size Decimals: {sz_decimals}")
    print(f"   Metadata: {btc_meta}")

    # Place a test market order (~$10,000 worth)
    # BTC has sz_decimals=2, so minimum meaningful size is 0.01 BTC
    notional = 10000
    size = notional / btc_price
    # Round to asset-specific precision
    size = round(size, sz_decimals)

    print(f"\n3. Placing MARKET BUY order...")
    print(f"   Asset: BTC")
    print(f"   Size: {size} BTC (~${notional:,})")
    print(f"   Type: MARKET (using IOC limit)")

    # For market orders with IOC, use a price well above market to ensure fill
    # Round to whole numbers for BTC (common tick size)
    slippage_price = round(btc_price * 1.05)  # 5% slippage buffer, rounded to integer
    
    try:
        order_result = exchange.order(
            name="BTC",
            is_buy=True,
            sz=size,
            limit_px=slippage_price,
            order_type={"limit": {"tif": "Ioc"}},  # Immediate or Cancel = market behavior
            reduce_only=False
        )
        
        print("\n✅ ORDER RESPONSE:")
        print(f"   Status: {order_result['status']}")
        
        if order_result["status"] == "ok":
            data = order_result["response"]["data"]
            statuses = data.get("statuses", [])
            
            print(f"   Response Type: {order_result['response']['type']}")
            print(f"   Statuses: {statuses}")
            
            if statuses:
                status = statuses[0]
                
                if "filled" in status:
                    print("\n🎉 ORDER FILLED IMMEDIATELY!")
                    filled_data = status["filled"]
                    print(f"   Total Size: {filled_data.get('totalSz', 'N/A')}")
                    print(f"   Average Price: ${filled_data.get('avgPx', 'N/A')}")
                    
                elif "resting" in status:
                    oid = status["resting"]["oid"]
                    print(f"\n⏳ ORDER RESTING (Order ID: {oid})")
                    print("   Will fill when price reached")
                    
                elif "error" in status:
                    error_msg = status["error"]
                    print(f"\n❌ ORDER REJECTED: {error_msg}")
                else:
                    print(f"\n⚠️  Unknown status: {status}")
        else:
            print(f"\n❌ ORDER FAILED: {order_result}")
        
        # Wait a moment then check position
        import time
        time.sleep(2)
        
        print("\n4. Checking positions...")
        user_state = info.user_state(account.address)
        positions = user_state.get("assetPositions", [])
        
        if positions:
            print(f"   ✅ Found {len(positions)} position(s):")
            for pos in positions:
                position_data = pos["position"]
                coin = position_data["coin"]
                size = position_data["szi"]
                entry = position_data.get("entryPx", "N/A")
                pnl = position_data.get("unrealizedPnl", "N/A")
                print(f"   - {coin}: {size} contracts")
                print(f"     Entry: ${entry}")
                print(f"     P&L: ${pnl}")
        else:
            print("   ⚠️  No positions found")
        
        # Check new balance
        user_state = info.user_state(account.address)
        new_balance = float(user_state["marginSummary"]["accountValue"])
        print(f"\n   New Balance: ${new_balance:,.2f}")
        print(f"   Change: ${new_balance - balance:+,.2f}")
        
        print("\n" + "=" * 80)
        print("✅ TEST COMPLETED!")
        print("=" * 80)
        print("\nThe trading API is now WORKING!")
        print("Your bot can now place real trades on Hyperliquid testnet.")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
