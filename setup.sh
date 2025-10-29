#!/bin/bash

echo "=========================================="
echo "Hyperliquid Trading Bot - Setup"
echo "=========================================="
echo ""

# Check Python version
echo "1. Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

echo "✅ Python found"
echo ""

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "2. Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "2. Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "3. Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Install dependencies
echo "4. Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"
echo ""

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "5. Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created"
else
    echo "5. .env file already exists"
fi
echo ""

echo "=========================================="
echo "Setup Complete! ✅"
echo "=========================================="
echo ""
echo "⚠️  NEXT STEPS - IMPORTANT!"
echo ""
echo "1. GET API KEYS:"
echo "   📍 Hyperliquid Testnet: https://app.hyperliquid-testnet.xyz/"
echo "      - Create account"
echo "      - Go to API settings"
echo "      - Create API key"
echo ""
echo "   📍 DeepSeek API: https://platform.deepseek.com/"
echo "      - Sign up"
echo "      - Get API key from dashboard"
echo ""
echo "2. CONFIGURE .env FILE:"
echo "   Open .env and add your API keys:"
echo "   $ nano .env"
echo "   or"
echo "   $ code .env"
echo ""
echo "   Required fields:"
echo "   - HYPERLIQUID_API_KEY=your_key_here"
echo "   - HYPERLIQUID_SECRET=your_secret_here"
echo "   - DEEPSEEK_API_KEY=your_key_here"
echo ""
echo "3. START THE BOT (TESTNET):"
echo "   Make sure HYPERLIQUID_TESTNET=true in .env"
echo "   Then run:"
echo "   $ source venv/bin/activate"
echo "   $ python run_bot.py"
echo ""
echo "📚 For detailed instructions, see QUICKSTART.md"
echo ""
