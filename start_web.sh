#!/bin/bash
# Start the Email Outreach Web Application

echo "🚀 Starting Email Outreach Web App..."
echo ""

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Warning: ANTHROPIC_API_KEY not set"
    echo "   Set it with: export ANTHROPIC_API_KEY='your-key'"
    echo "   Continuing with template fallback mode..."
    echo ""
fi

# Check for Gmail credentials
if [ ! -f "credentials.json" ]; then
    echo "⚠️  Warning: credentials.json not found"
    echo "   Gmail draft creation will not be available"
    echo "   Download it from Google Cloud Console"
    echo ""
fi

# Install dependencies if needed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Installing Flask..."
    pip3 install Flask Werkzeug
fi

echo "✅ Starting server at http://localhost:5000"
echo "   Press Ctrl+C to stop"
echo ""

# Start Flask app
python3 web_app.py