#!/usr/bin/env python3
"""
Wallet Setup Verification Script for Hyperliquid

This script helps you:
1. Verify your private key is valid
2. Check that wallet address matches the private key
3. Test connectivity with Hyperliquid
"""

import asyncio
import os
import sys
from eth_account import Account
from dotenv import load_dotenv
import aiohttp

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}\n")


def print_success(text: str):
    """Print success message."""
    print(f"✅ {text}")


def print_error(text: str):
    """Print error message."""
    print(f"❌ {text}")


def print_info(text: str):
    """Print info message."""
    print(f"ℹ️  {text}")


def test_wallet_credentials():
    """Test 1: Verify wallet credentials from .env"""
    print_header("Test 1: Wallet Credentials")

    # Load environment variables
    load_dotenv()

    private_key = os.getenv("HYPERLIQUID_PRIVATE_KEY", "")
    wallet_address = os.getenv("HYPERLIQUID_WALLET_ADDRESS", "")
    testnet = os.getenv("HYPERLIQUID_TESTNET", "true").lower() == "true"

    errors = []

    # Check if credentials are set
    if not private_key or private_key == "0x...":
        errors.append("HYPERLIQUID_PRIVATE_KEY not set or still has placeholder value")

    if not wallet_address or wallet_address == "0x...":
        errors.append("HYPERLIQUID_WALLET_ADDRESS not set or still has placeholder value")

    if errors:
        for error in errors:
            print_error(error)
        print()
        print_info("Please update your .env file with your actual wallet credentials")
        print_info("See HYPERLIQUID_SETUP.md for instructions on how to get these")
        return False

    print_success("Private key found in .env")
    print_success("Wallet address found in .env")
    print_success(f"Network: {'Testnet' if testnet else 'Mainnet'}")

    return True, private_key, wallet_address, testnet


def test_private_key_valid(private_key: str, wallet_address: str):
    """Test 2: Verify private key is valid and matches address"""
    print_header("Test 2: Private Key Validation")

    try:
        # Ensure private key has 0x prefix
        if not private_key.startswith("0x"):
            private_key = f"0x{private_key}"

        # Try to create account from private key
        account = Account.from_key(private_key)

        print_success("Private key format is valid")
        print_info(f"Derived address from private key: {account.address}")
        print_info(f"Configured address in .env:      {wallet_address}")

        # Check if addresses match
        if account.address.lower() == wallet_address.lower():
            print_success("✓ Addresses match! Configuration is correct!")
            return True, account
        else:
            print_error("Addresses don't match!")
            print_error("Your HYPERLIQUID_WALLET_ADDRESS doesn't match your private key")
            print()
            print_info(f"Update your .env file with: HYPERLIQUID_WALLET_ADDRESS={account.address}")
            return False, None

    except Exception as e:
        print_error(f"Invalid private key: {e}")
        print_info("Make sure your private key is a valid Ethereum private key (64 hex characters)")
        return False, None


async def test_hyperliquid_connectivity(testnet: bool):
    """Test 3: Check Hyperliquid API connectivity"""
    print_header("Test 3: Hyperliquid API Connectivity")

    base_url = "https://api.hyperliquid-testnet.xyz" if testnet else "https://api.hyperliquid.xyz"
    endpoint = "/info"

    try:
        async with aiohttp.ClientSession() as session:
            # Try to get basic market info
            async with session.post(
                f"{base_url}{endpoint}",
                json={"type": "meta"},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print_success(f"Successfully connected to Hyperliquid {'Testnet' if testnet else 'Mainnet'}")
                    print_info(f"API URL: {base_url}")

                    # Show available assets
                    if isinstance(data, dict) and "universe" in data:
                        assets = [u["name"] for u in data["universe"][:10]]
                        print_info(f"Sample available assets: {', '.join(assets)}")

                    return True
                else:
                    print_error(f"API returned status code: {response.status}")
                    return False

    except asyncio.TimeoutError:
        print_error("Connection timeout - API is not responding")
        print_info("Check your internet connection")
        return False
    except Exception as e:
        print_error(f"Connection failed: {e}")
        return False


async def test_account_info(account: Account, testnet: bool):
    """Test 4: Try to get account information"""
    print_header("Test 4: Account Information")

    base_url = "https://api.hyperliquid-testnet.xyz" if testnet else "https://api.hyperliquid.xyz"
    endpoint = "/info"

    try:
        async with aiohttp.ClientSession() as session:
            # Request account state
            async with session.post(
                f"{base_url}{endpoint}",
                json={
                    "type": "clearinghouseState",
                    "user": account.address
                },
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    print_success("Successfully retrieved account information")
                    print_info(f"Wallet Address: {account.address}")

                    # Parse balance info
                    if isinstance(data, dict):
                        margin_summary = data.get("marginSummary", {})
                        account_value = float(margin_summary.get("accountValue", 0))

                        print_info(f"Account Value: ${account_value:,.2f}")

                        if account_value == 0:
                            print()
                            print_info("⚠️  Your account has no funds!")
                            if testnet:
                                print_info("Get testnet funds from:")
                                print_info("  • https://testnet.hyperliquid.xyz/faucet")
                                print_info("  • Discord: https://discord.gg/hyperliquid (#testnet-faucet)")
                        else:
                            print_success(f"Account has ${account_value:,.2f} USDC")

                    return True
                else:
                    print_error(f"Failed to retrieve account info: {response.status}")
                    text = await response.text()
                    print_error(f"Response: {text[:200]}")
                    return False

    except Exception as e:
        print_error(f"Failed to retrieve account info: {e}")
        return False


async def main():
    """Run all wallet verification tests"""
    print_header("Hyperliquid Wallet Setup Verification")
    print("This script will verify your wallet configuration")

    # Test 1: Check .env credentials
    result = test_wallet_credentials()
    if not result:
        print_header("Verification Failed")
        print_error("Please set up your .env file with valid credentials")
        print_info("See HYPERLIQUID_SETUP.md for detailed instructions")
        return

    success, private_key, wallet_address, testnet = result

    # Test 2: Validate private key
    success, account = test_private_key_valid(private_key, wallet_address)
    if not success:
        print_header("Verification Failed")
        return

    # Test 3: Check API connectivity
    success = await test_hyperliquid_connectivity(testnet)
    if not success:
        print_header("Verification Failed")
        print_error("Cannot connect to Hyperliquid API")
        return

    # Test 4: Get account info
    await test_account_info(account, testnet)

    # Final summary
    print_header("Verification Complete")
    print_success("All checks passed! ✓")
    print()
    print_info("Your wallet is properly configured and ready to use")
    print_info("Next steps:")
    if testnet:
        print("  1. Get testnet funds (see above)")
        print("  2. Run the bot: python run_bot.py")
        print("  3. Monitor logs: tail -f logs/trading_bot.log")
    else:
        print("  ⚠️  WARNING: You're using MAINNET with real money!")
        print("  1. Make sure you understand the risks")
        print("  2. Start with small position sizes")
        print("  3. Run the bot: python run_bot.py")
        print("  4. Monitor logs: tail -f logs/trading_bot.log")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nVerification cancelled by user")
        sys.exit(0)
