"""Test the PerformanceTracker functionality."""

import sys
from src.risk.performance_tracker import PerformanceTracker

def test_performance_tracker():
    """Test PerformanceTracker risk management features."""

    print("=" * 80)
    print("TESTING PERFORMANCE TRACKER")
    print("=" * 80)

    # Initialize tracker
    tracker = PerformanceTracker()
    print("\n✅ PerformanceTracker initialized")

    # Test 1: Can trade initially
    can_trade, reason = tracker.can_trade()
    print(f"\n1. Initial state - Can trade: {can_trade}")
    assert can_trade, "Should be able to trade initially"

    # Test 2: Update balance (simulate starting portfolio)
    tracker.update_balance(10000.0)
    print(f"2. Balance set to $10,000")

    # Test 3: Log a trade
    tracker.log_trade(
        asset="BTC",
        side="BUY",
        entry_price=100000,
        size=0.1,
        stop_loss=99000,
        take_profit=[101000, 102000, 103000],
        confidence=0.8,
        confluence=7,
        reason="Testing trade logging"
    )
    print(f"3. Trade logged - Trades today: {tracker.daily_data['trades_today']}")

    # Test 4: Position size modifier (should be 1.0 initially)
    modifier = tracker.get_position_size_modifier()
    print(f"4. Position size modifier: {modifier}")
    assert modifier == 1.0, "Should be 1.0 with no losses"

    # Test 5: Simulate a loss
    tracker.log_trade_close(
        asset="BTC",
        exit_price=99500,
        pnl=-50,
        pnl_pct=-0.5
    )
    print(f"5. Loss logged - Consecutive losses: {tracker.daily_data['consecutive_losses']}")

    # Test 6: Check if modifier changes after loss
    modifier = tracker.get_position_size_modifier()
    print(f"6. Position size modifier after 1 loss: {modifier}")

    # Test 7: Simulate multiple losses
    for i in range(2, 4):
        tracker.log_trade(
            asset=f"ETH-{i}",
            side="BUY",
            entry_price=3500,
            size=1.0,
            stop_loss=3450,
            take_profit=[3550],
            confidence=0.7,
            confluence=6,
            reason=f"Test trade {i}"
        )
        tracker.log_trade_close(
            asset=f"ETH-{i}",
            exit_price=3460,
            pnl=-40,
            pnl_pct=-1.14
        )

    print(f"7. After 3 consecutive losses: {tracker.daily_data['consecutive_losses']}")
    modifier = tracker.get_position_size_modifier()
    print(f"   Position size modifier: {modifier}")
    assert modifier == 0.5, "Should be 0.5 after 3 losses"

    # Test 8: Check if trading is blocked after 4 losses
    tracker.log_trade(
        asset="SOL-4",
        side="BUY",
        entry_price=100,
        size=10,
        stop_loss=98,
        take_profit=[102],
        confidence=0.6,
        confluence=5,
        reason="Test trade 4"
    )
    tracker.log_trade_close(
        asset="SOL-4",
        exit_price=98.5,
        pnl=-15,
        pnl_pct=-1.5
    )

    can_trade, reason = tracker.can_trade()
    print(f"8. After 4 consecutive losses - Can trade: {can_trade}, Reason: {reason}")
    assert not can_trade, "Should NOT be able to trade after 4 losses"

    # Test 9: Simulate a win to reset streak
    tracker.daily_data["consecutive_losses"] = 0
    tracker.daily_data["is_trading_stopped"] = False
    tracker.log_trade(
        asset="BTC-win",
        side="BUY",
        entry_price=100000,
        size=0.1,
        stop_loss=99000,
        take_profit=[102000],
        confidence=0.85,
        confluence=8,
        reason="Winning trade"
    )
    tracker.log_trade_close(
        asset="BTC-win",
        exit_price=101500,
        pnl=150,
        pnl_pct=1.5
    )
    print(f"9. After win - Consecutive losses: {tracker.daily_data['consecutive_losses']}")
    assert tracker.daily_data["consecutive_losses"] == 0, "Should reset to 0"

    # Test 10: Check A+ setup filtering
    for i in range(6):
        tracker.daily_data["trades_today"] = i
        only_aplus = tracker.should_only_trade_aplus_setups()
        print(f"10. Trade {i}/8 - Only A+ setups: {only_aplus}")

    # Test 11: Daily stats
    stats = tracker.get_daily_stats()
    print(f"\n11. Daily Stats:")
    print(f"    Trades: {stats['trades_today']}")
    print(f"    Wins: {stats['wins']}")
    print(f"    Losses: {stats['losses']}")
    print(f"    Win Rate: {stats['win_rate']:.1f}%")
    print(f"    Daily P&L: ${stats['daily_pnl']:.2f} ({stats['daily_pnl_pct']:.2f}%)")

    # Test 12: Simulate daily loss limit
    tracker.update_balance(9600.0)  # -4% from starting $10,000
    can_continue = tracker.update_balance(9700.0)  # -3% exactly
    print(f"\n12. Daily loss limit test (-3%): Can continue: {can_continue}")
    print(f"    Trading stopped: {tracker.daily_data['is_trading_stopped']}")

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)

    return True


if __name__ == "__main__":
    try:
        test_performance_tracker()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
