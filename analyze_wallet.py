"""Analyze trading activity of a Hyperliquid wallet."""

import asyncio
import aiohttp
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict
import json


class WalletAnalyzer:
    """Analyze trading activity of a Hyperliquid wallet."""

    def __init__(self, wallet_address: str, testnet: bool = False):
        self.wallet_address = wallet_address
        self.base_url = "https://api.hyperliquid-testnet.xyz" if testnet else "https://api.hyperliquid.xyz"
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _request(self, endpoint: str, data: Dict[str, Any]) -> Any:
        """Make API request."""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}

        async with self.session.post(url, json=data, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

    async def get_user_fills(self) -> List[Dict[str, Any]]:
        """Get all user fills (executed trades)."""
        data = {
            "type": "userFills",
            "user": self.wallet_address
        }

        try:
            response = await self._request("/info", data)
            print(f"DEBUG: User fills response type: {type(response)}, length: {len(response) if isinstance(response, list) else 'N/A'}")
            if isinstance(response, list) and len(response) > 0:
                print(f"DEBUG: First fill: {response[0]}")
            return response if response else []
        except Exception as e:
            print(f"Error fetching user fills: {e}")
            return []

    async def get_user_funding(self) -> List[Dict[str, Any]]:
        """Get user funding payments."""
        data = {
            "type": "userFunding",
            "user": self.wallet_address
        }

        try:
            response = await self._request("/info", data)
            return response if response else []
        except Exception as e:
            print(f"Error fetching user funding: {e}")
            return []

    async def get_account_state(self) -> Dict[str, Any]:
        """Get current account state."""
        data = {
            "type": "clearinghouseState",
            "user": self.wallet_address
        }

        try:
            response = await self._request("/info", data)
            return response
        except Exception as e:
            print(f"Error fetching account state: {e}")
            return {}

    async def get_user_non_funding_ledger(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get user ledger updates (deposits, withdrawals, PnL)."""
        data = {
            "type": "userNonFundingLedgerUpdates",
            "user": self.wallet_address,
            "startTime": 0  # Get all history
        }

        try:
            response = await self._request("/info", data)
            print(f"DEBUG: Ledger response length: {len(response) if isinstance(response, list) else 'N/A'}")
            if isinstance(response, list) and len(response) > 0:
                print(f"DEBUG: Recent ledger entries: {response[:3]}")
            return response[:limit] if response else []
        except Exception as e:
            print(f"Error fetching ledger: {e}")
            return []

    async def get_spot_clearinghouse_state(self) -> Dict[str, Any]:
        """Get spot account state."""
        data = {
            "type": "spotClearinghouseState",
            "user": self.wallet_address
        }

        try:
            response = await self._request("/info", data)
            return response
        except Exception as e:
            print(f"Error fetching spot state: {e}")
            return {}

    async def get_spot_user_fills(self) -> List[Dict[str, Any]]:
        """Get spot trading fills."""
        data = {
            "type": "spotUserFills",
            "user": self.wallet_address
        }

        try:
            response = await self._request("/info", data)
            print(f"DEBUG: Spot fills response length: {len(response) if isinstance(response, list) else 'N/A'}")
            if isinstance(response, list) and len(response) > 0:
                print(f"DEBUG: First spot fill: {response[0]}")
            return response if response else []
        except Exception as e:
            print(f"Error fetching spot fills: {e}")
            return []

    def analyze_fills(self, fills: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trading fills."""
        if not fills:
            return {
                "total_trades": 0,
                "message": "No trades found"
            }

        # Group trades by asset
        trades_by_asset = defaultdict(list)
        total_volume = 0.0
        total_fee = 0.0

        for fill in fills:
            coin = fill.get('coin', 'UNKNOWN')
            trades_by_asset[coin].append(fill)

            # Calculate volume
            px = float(fill.get('px', 0))
            sz = abs(float(fill.get('sz', 0)))
            volume = px * sz
            total_volume += volume

            # Sum fees
            fee = abs(float(fill.get('fee', 0)))
            total_fee += fee

        # Calculate statistics per asset
        asset_stats = {}
        for coin, coin_fills in trades_by_asset.items():
            total_trades = len(coin_fills)
            buys = sum(1 for f in coin_fills if float(f.get('sz', 0)) > 0)
            sells = total_trades - buys

            coin_volume = sum(
                float(f.get('px', 0)) * abs(float(f.get('sz', 0)))
                for f in coin_fills
            )

            coin_fees = sum(abs(float(f.get('fee', 0))) for f in coin_fills)

            # Get first and last trade times
            timestamps = [f.get('time', 0) for f in coin_fills if f.get('time')]
            first_trade = min(timestamps) if timestamps else 0
            last_trade = max(timestamps) if timestamps else 0

            asset_stats[coin] = {
                "total_trades": total_trades,
                "buys": buys,
                "sells": sells,
                "volume_usd": coin_volume,
                "fees_paid": coin_fees,
                "first_trade": datetime.fromtimestamp(first_trade / 1000).strftime('%Y-%m-%d %H:%M:%S') if first_trade else "N/A",
                "last_trade": datetime.fromtimestamp(last_trade / 1000).strftime('%Y-%m-%d %H:%M:%S') if last_trade else "N/A",
            }

        # Sort assets by volume
        sorted_assets = sorted(
            asset_stats.items(),
            key=lambda x: x[1]['volume_usd'],
            reverse=True
        )

        return {
            "total_trades": len(fills),
            "total_volume_usd": total_volume,
            "total_fees_paid": total_fee,
            "unique_assets": len(trades_by_asset),
            "assets": dict(sorted_assets)
        }

    def analyze_funding(self, funding: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze funding payments."""
        if not funding:
            return {
                "total_payments": 0,
                "net_funding": 0.0,
                "message": "No funding data found"
            }

        total_funding = 0.0
        funding_by_asset = defaultdict(float)

        for payment in funding:
            coin = payment.get('coin', 'UNKNOWN')
            usdc = float(payment.get('usdc', 0))
            total_funding += usdc
            funding_by_asset[coin] += usdc

        return {
            "total_payments": len(funding),
            "net_funding_usd": total_funding,
            "net_funding_received" if total_funding > 0 else "net_funding_paid": abs(total_funding),
            "funding_by_asset": dict(funding_by_asset)
        }

    def print_analysis(self, fills_analysis: Dict, funding_analysis: Dict, account_state: Dict,
                       ledger: List[Dict], spot_state: Dict):
        """Print formatted analysis."""
        print("=" * 80)
        print(f"HYPERLIQUID WALLET ANALYSIS")
        print(f"Wallet: {self.wallet_address}")
        print("=" * 80)
        print()

        # Account State
        perp_account_value = 0.0
        if account_state:
            margin_summary = account_state.get('marginSummary', {})
            perp_account_value = float(margin_summary.get('accountValue', 0))
            total_margin_used = float(margin_summary.get('totalMarginUsed', 0))

            print("📊 PERPETUAL ACCOUNT STATE")
            print("-" * 80)
            print(f"Account Value:        ${perp_account_value:,.2f}")
            print(f"Margin Used:          ${total_margin_used:,.2f}")
            print(f"Available Balance:    ${perp_account_value - total_margin_used:,.2f}")

            # Positions
            positions = account_state.get('assetPositions', [])
            if positions:
                active_positions = [p for p in positions if float(p.get('position', {}).get('szi', 0)) != 0]
                print(f"\nOpen Positions:       {len(active_positions)}")
                for pos in active_positions:
                    coin = pos.get('position', {}).get('coin', 'UNKNOWN')
                    szi = float(pos.get('position', {}).get('szi', 0))
                    entry_px = float(pos.get('position', {}).get('entryPx', 0))
                    unrealized_pnl = float(pos.get('position', {}).get('unrealizedPnl', 0))
                    side = "LONG" if szi > 0 else "SHORT"
                    print(f"  - {coin}: {side} {abs(szi):.4f} @ ${entry_px:,.2f} (P&L: ${unrealized_pnl:+,.2f})")
            else:
                print(f"Open Positions:       0")

            print()

        # Spot Account
        if spot_state:
            spot_balances = spot_state.get('balances', [])
            total_spot_value = 0.0

            print("💵 SPOT ACCOUNT STATE")
            print("-" * 80)

            if spot_balances:
                active_balances = [b for b in spot_balances if float(b.get('total', 0)) > 0.001]
                if active_balances:
                    print("Balances:")
                    for balance in active_balances:
                        coin = balance.get('coin', 'UNKNOWN')
                        total = float(balance.get('total', 0))
                        hold = float(balance.get('hold', 0))
                        print(f"  - {coin}: {total:.6f} (Hold: {hold:.6f})")
                else:
                    print("No spot balances")
            else:
                print("No spot balances")

            print()

        # Ledger Analysis (Deposits/Withdrawals/PnL/Transfers)
        if ledger:
            print("💰 ACCOUNT ACTIVITY")
            print("-" * 80)

            deposits = []
            withdrawals = []
            liquidations = []
            spot_transfers_in = []
            spot_transfers_out = []

            for entry in ledger:
                delta = entry.get('delta', {})
                ledger_type = delta.get('type', '')

                if ledger_type == 'deposit':
                    deposits.append(float(delta.get('usdc', 0)))
                elif ledger_type == 'withdraw':
                    withdrawals.append(float(delta.get('usdc', 0)))
                elif ledger_type == 'liquidation':
                    liquidations.append(entry)
                elif ledger_type == 'spotTransfer':
                    # Check if this wallet is the destination (receiving) or user (sending)
                    destination = delta.get('destination', '').lower()
                    user = delta.get('user', '').lower()
                    is_receiver = destination == self.wallet_address.lower()

                    transfer_info = {
                        'time': datetime.fromtimestamp(entry.get('time', 0) / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                        'token': delta.get('token', ''),
                        'amount': float(delta.get('amount', 0)),
                        'usdcValue': float(delta.get('usdcValue', 0)),
                        'from': user,
                        'to': destination
                    }

                    if is_receiver:
                        spot_transfers_in.append(transfer_info)
                    else:
                        spot_transfers_out.append(transfer_info)

            total_deposited = sum(deposits)
            total_withdrawn = sum(abs(w) for w in withdrawals)
            net_deposits = total_deposited - total_withdrawn

            print(f"Total Deposits:       ${total_deposited:,.2f}")
            print(f"Total Withdrawals:    ${total_withdrawn:,.2f}")
            print(f"Net Deposits:         ${net_deposits:+,.2f}")

            # Show spot transfers
            if spot_transfers_in:
                print(f"\n📥 Spot Transfers IN:  {len(spot_transfers_in)}")
                for transfer in spot_transfers_in:
                    print(f"  {transfer['time']}: Received {transfer['amount']:,.2f} {transfer['token']} "
                          f"(~${transfer['usdcValue']:,.2f})")

            if spot_transfers_out:
                print(f"\n📤 Spot Transfers OUT: {len(spot_transfers_out)}")
                for transfer in spot_transfers_out:
                    print(f"  {transfer['time']}: Sent {transfer['amount']:,.2f} {transfer['token']} "
                          f"(~${transfer['usdcValue']:,.2f})")

            if liquidations:
                print(f"\n⚠️  Liquidations:      {len(liquidations)}")

            # Calculate overall P&L
            if net_deposits != 0:
                current_value = perp_account_value
                realized_pnl = current_value - net_deposits
                realized_pnl_pct = (realized_pnl / abs(net_deposits)) * 100 if net_deposits != 0 else 0

                print(f"\nRealized P&L:         ${realized_pnl:+,.2f} ({realized_pnl_pct:+.2f}%)")

            print()

        # Trading Activity
        print("📈 TRADING ACTIVITY")
        print("-" * 80)
        print(f"Total Trades:         {fills_analysis.get('total_trades', 0):,}")
        print(f"Total Volume:         ${fills_analysis.get('total_volume_usd', 0):,.2f}")
        print(f"Total Fees Paid:      ${fills_analysis.get('total_fees_paid', 0):,.2f}")
        print(f"Unique Assets:        {fills_analysis.get('unique_assets', 0)}")
        print()

        # Asset breakdown
        if 'assets' in fills_analysis and fills_analysis['assets']:
            print("💰 TRADING BY ASSET")
            print("-" * 80)
            print(f"{'Asset':<10} {'Trades':<10} {'Buys':<8} {'Sells':<8} {'Volume (USD)':<18} {'Fees':<12}")
            print("-" * 80)

            for coin, stats in list(fills_analysis['assets'].items())[:15]:  # Top 15 assets
                print(
                    f"{coin:<10} {stats['total_trades']:<10} {stats['buys']:<8} {stats['sells']:<8} "
                    f"${stats['volume_usd']:>15,.2f}  ${stats['fees_paid']:>9,.2f}"
                )

            if len(fills_analysis['assets']) > 15:
                print(f"\n... and {len(fills_analysis['assets']) - 15} more assets")

            print()

        # Funding Analysis
        print("💸 FUNDING PAYMENTS")
        print("-" * 80)
        net_funding = funding_analysis.get('net_funding_usd', 0)
        if net_funding > 0:
            print(f"Net Funding Received: ${net_funding:,.2f}")
            print("Status:               ✅ Earned from shorts (or paid longs)")
        elif net_funding < 0:
            print(f"Net Funding Paid:     ${abs(net_funding):,.2f}")
            print("Status:               ❌ Paid from longs (or received from shorts)")
        else:
            print("Net Funding:          $0.00")
            print("Status:               No funding payments")

        print(f"Total Payments:       {funding_analysis.get('total_payments', 0):,}")
        print()

        # Most Traded Assets (top 5)
        if 'assets' in fills_analysis and fills_analysis['assets']:
            print("🔥 TOP 5 MOST TRADED ASSETS")
            print("-" * 80)
            for i, (coin, stats) in enumerate(list(fills_analysis['assets'].items())[:5], 1):
                print(f"{i}. {coin}")
                print(f"   Trades: {stats['total_trades']} ({stats['buys']} buys, {stats['sells']} sells)")
                print(f"   Volume: ${stats['volume_usd']:,.2f}")
                print(f"   First:  {stats['first_trade']}")
                print(f"   Last:   {stats['last_trade']}")
                print()

        print("=" * 80)


async def main():
    """Main entry point."""
    # Wallet to analyze
    wallet_address = "0x9eac4fd49cfef8710b34ec3b924280cf4737e29c"

    # Check testnet only
    for testnet in [True]:
        network_name = 'Testnet' if testnet else 'Mainnet'
        print(f"\nAnalyzing Hyperliquid wallet: {wallet_address}")
        print(f"Network: {network_name}")
        print()

        async with WalletAnalyzer(wallet_address, testnet) as analyzer:
            # Fetch data
            print("Fetching trade history...")
            fills = await analyzer.get_user_fills()

            print("Fetching funding payments...")
            funding = await analyzer.get_user_funding()

            print("Fetching account state...")
            account_state = await analyzer.get_account_state()

            print("Fetching ledger updates...")
            ledger = await analyzer.get_user_non_funding_ledger(limit=1000)

            print("Fetching spot account state...")
            spot_state = await analyzer.get_spot_clearinghouse_state()

            print("Fetching spot trades...")
            spot_fills = await analyzer.get_spot_user_fills()

            print()

            # Check if wallet has any activity
            has_perp_value = account_state and account_state.get('marginSummary', {}).get('accountValue', 0) != 0
            has_spot_value = spot_state and any(float(b.get('total', 0)) > 0 for b in spot_state.get('balances', []))

            if fills or funding or ledger or has_perp_value or has_spot_value or spot_fills:
                # Analyze
                fills_analysis = analyzer.analyze_fills(fills)
                spot_fills_analysis = analyzer.analyze_fills(spot_fills) if spot_fills else {"total_trades": 0}
                funding_analysis = analyzer.analyze_funding(funding)

                # Print results - pass both perp and spot fills
                print(f"DEBUG: Perp trades: {len(fills)}, Spot trades: {len(spot_fills)}")
                analyzer.print_analysis(fills_analysis, funding_analysis, account_state, ledger, spot_state)

                # Add spot trading summary
                if spot_fills:
                    print("\n🔄 SPOT TRADING ACTIVITY")
                    print("-" * 80)
                    print(f"Total Spot Trades:    {spot_fills_analysis.get('total_trades', 0):,}")
                    print(f"Total Spot Volume:    ${spot_fills_analysis.get('total_volume_usd', 0):,.2f}")
                    print(f"Total Spot Fees:      ${spot_fills_analysis.get('total_fees_paid', 0):,.2f}")

                    if 'assets' in spot_fills_analysis and spot_fills_analysis['assets']:
                        print(f"\nSpot Assets Traded:   {spot_fills_analysis.get('unique_assets', 0)}")
                        print("-" * 80)
                        print(f"{'Asset':<10} {'Trades':<10} {'Volume (USD)':<18} {'Fees'}")
                        print("-" * 80)
                        for coin, stats in list(spot_fills_analysis['assets'].items())[:10]:
                            print(
                                f"{coin:<10} {stats['total_trades']:<10} "
                                f"${stats['volume_usd']:>15,.2f}  ${stats['fees_paid']:>9,.2f}"
                            )
                    print()

                break  # Found activity, no need to check other network
            else:
                print(f"No activity found on {network_name}")

        if testnet:
            print("\nNo trading activity found on either Mainnet or Testnet.")


if __name__ == "__main__":
    asyncio.run(main())
