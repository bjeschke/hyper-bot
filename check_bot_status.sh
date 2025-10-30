#!/bin/bash
# Bot Health Check Script
# Run this on the DigitalOcean Droplet

echo "========================================="
echo "🤖 TRADING BOT HEALTH CHECK"
echo "========================================="
echo ""

# Check if bot process is running
echo "1️⃣  Checking if bot is running..."
if ps aux | grep -v grep | grep "run_bot.py" > /dev/null; then
    echo "   ✅ Bot process is RUNNING"
    ps aux | grep -v grep | grep "run_bot.py" | awk '{print "   PID:", $2, "| CPU:", $3"%", "| RAM:", $4"%"}'
else
    echo "   ❌ Bot is NOT running!"
fi
echo ""

# Check log file
echo "2️⃣  Checking log file..."
if [ -f "logs/trading_bot.log" ]; then
    echo "   ✅ Log file exists"
    LOG_SIZE=$(du -h logs/trading_bot.log | awk '{print $1}')
    LOG_LINES=$(wc -l logs/trading_bot.log | awk '{print $1}')
    echo "   Size: $LOG_SIZE | Lines: $LOG_LINES"

    # Show last activity
    echo ""
    echo "   📝 Last 5 log entries:"
    tail -5 logs/trading_bot.log | sed 's/^/      /'
else
    echo "   ❌ Log file not found!"
fi
echo ""

# Check screen sessions
echo "3️⃣  Checking screen sessions..."
if command -v screen &> /dev/null; then
    if screen -ls | grep -q "trading-bot"; then
        echo "   ✅ Screen session 'trading-bot' found"
    else
        echo "   ⚠️  No screen session found"
    fi
else
    echo "   ⚠️  Screen not installed"
fi
echo ""

# Check disk space
echo "4️⃣  Checking disk space..."
df -h / | awk 'NR==2 {print "   Used:", $3, "/", $2, "("$5")"}'
echo ""

# Check memory
echo "5️⃣  Checking memory..."
free -h | awk 'NR==2 {print "   Used:", $3, "/", $2}'
echo ""

# Check if APIs are configured
echo "6️⃣  Checking configuration..."
if [ -f ".env" ]; then
    echo "   ✅ .env file exists"

    if grep -q "HYPERLIQUID_PRIVATE_KEY=.\+" .env; then
        echo "   ✅ Hyperliquid private key configured"
    else
        echo "   ❌ Hyperliquid private key missing!"
    fi

    if grep -q "DEEPSEEK_API_KEY=.\+" .env; then
        echo "   ✅ DeepSeek API key configured"
    else
        echo "   ❌ DeepSeek API key missing!"
    fi
else
    echo "   ❌ .env file not found!"
fi
echo ""

echo "========================================="
echo "✅ Health check complete!"
echo "========================================="
