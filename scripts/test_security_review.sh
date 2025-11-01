#!/bin/bash
# Test Security Review Setup
# This script helps verify that the security review workflow is configured correctly

set -e

echo "🔍 Testing Claude Code Security Review Setup"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${GREEN}ℹ️  $1${NC}"
}

# Check 1: Verify ANTHROPIC_API_KEY
echo "1. Checking ANTHROPIC_API_KEY..."
if [ -z "$ANTHROPIC_API_KEY" ]; then
    print_status 1 "ANTHROPIC_API_KEY environment variable not set"
    print_warning "Please set your API key: export ANTHROPIC_API_KEY='your-key'"
    echo ""
else
    KEY_PREFIX=$(echo $ANTHROPIC_API_KEY | cut -c1-10)
    print_status 0 "ANTHROPIC_API_KEY is set (${KEY_PREFIX}...)"
    echo ""
fi

# Check 2: Verify workflow file exists
echo "2. Checking security review workflow file..."
if [ -f ".github/workflows/security-review.yml" ]; then
    print_status 0 "Workflow file exists: .github/workflows/security-review.yml"
    echo ""
else
    print_status 1 "Workflow file not found: .github/workflows/security-review.yml"
    echo ""
fi

# Check 3: Verify configuration file exists
echo "3. Checking security review configuration..."
if [ -f ".github/security-review-config.yml" ]; then
    print_status 0 "Configuration file exists: .github/security-review-config.yml"
    echo ""
else
    print_status 1 "Configuration file not found: .github/security-review-config.yml"
    echo ""
fi

# Check 4: Verify Python dependencies
echo "4. Checking security scanning tools..."

# Check for bandit
if command -v bandit &> /dev/null; then
    BANDIT_VERSION=$(bandit --version 2>&1 | head -n1)
    print_status 0 "Bandit is installed: $BANDIT_VERSION"
else
    print_status 1 "Bandit is not installed"
    print_warning "Install with: pip install bandit"
fi

# Check for safety
if command -v safety &> /dev/null; then
    SAFETY_VERSION=$(safety --version 2>&1)
    print_status 0 "Safety is installed: $SAFETY_VERSION"
else
    print_status 1 "Safety is not installed"
    print_warning "Install with: pip install safety"
fi

echo ""

# Check 5: Test Bandit on current code
echo "5. Running local Bandit scan..."
if command -v bandit &> /dev/null; then
    echo "Scanning Python files..."
    bandit -r . -f txt -x ./venv,./node_modules,./.venv 2>&1 | head -n 20
    print_info "Run 'bandit -r . -f screen' for full report"
    echo ""
else
    print_warning "Bandit not available - skipping local scan"
    echo ""
fi

# Check 6: Test Safety on dependencies
echo "6. Checking dependency vulnerabilities..."
if command -v safety &> /dev/null && [ -f "requirements.txt" ]; then
    echo "Scanning dependencies..."
    safety check -r requirements.txt --short 2>&1 || true
    echo ""
else
    print_warning "Safety not available or requirements.txt not found - skipping"
    echo ""
fi

# Check 7: Scan for hardcoded secrets
echo "7. Scanning for hardcoded secrets..."
SECRET_COUNT=0

# Check for potential secrets
if grep -rn --include="*.py" --include="*.js" \
    -e "password\s*=\s*['\"][^'\"]\+" \
    -e "api_key\s*=\s*['\"][^'\"]\+" \
    -e "secret\s*=\s*['\"][^'\"]\+" \
    -e "token\s*=\s*['\"]sk-" \
    . 2>/dev/null | grep -v "\.git" | grep -v "test_security"; then
    SECRET_COUNT=$?
fi

if [ $SECRET_COUNT -eq 0 ]; then
    print_warning "Potential hardcoded secrets found (see above)"
    print_info "Review these findings and ensure they're not real secrets"
else
    print_status 0 "No obvious hardcoded secrets found"
fi
echo ""

# Check 8: Scan for dangerous functions
echo "8. Scanning for dangerous function usage..."
DANGER_COUNT=0

if grep -rn --include="*.py" \
    -e "\beval(" \
    -e "\bexec(" \
    -e "os\.system(" \
    -e "pickle\.loads(" \
    . 2>/dev/null | grep -v "\.git" | grep -v "test_" | grep -v "#"; then
    DANGER_COUNT=$?
fi

if [ $DANGER_COUNT -eq 0 ]; then
    print_warning "Dangerous functions found (see above)"
    print_info "Review these usages for security implications"
else
    print_status 0 "No dangerous function usage found"
fi
echo ""

# Check 9: Verify .gitignore for sensitive files
echo "9. Checking .gitignore for sensitive files..."
if [ -f ".gitignore" ]; then
    IGNORED_SECRETS=0

    if grep -q "token.json" .gitignore; then
        ((IGNORED_SECRETS++))
    fi

    if grep -q "credentials.json" .gitignore; then
        ((IGNORED_SECRETS++))
    fi

    if grep -q ".env" .gitignore; then
        ((IGNORED_SECRETS++))
    fi

    if [ $IGNORED_SECRETS -eq 3 ]; then
        print_status 0 ".gitignore contains essential security exclusions"
    else
        print_warning ".gitignore may be missing security exclusions"
        print_info "Ensure these are in .gitignore: token.json, credentials.json, .env"
    fi
else
    print_status 1 ".gitignore file not found"
fi
echo ""

# Check 10: GitHub Actions permissions
echo "10. Checking GitHub Actions workflow permissions..."
if grep -q "permissions:" .github/workflows/security-review.yml; then
    print_status 0 "Workflow has permission declarations"
else
    print_warning "Workflow may need permission declarations"
fi
echo ""

# Summary
echo "=============================================="
echo "📊 Security Review Setup Summary"
echo "=============================================="
echo ""
print_info "Next Steps:"
echo ""
echo "1. If ANTHROPIC_API_KEY is not set locally:"
echo "   export ANTHROPIC_API_KEY='your-api-key'"
echo ""
echo "2. Add ANTHROPIC_API_KEY to GitHub Secrets:"
echo "   GitHub Repo → Settings → Secrets → Actions → New secret"
echo ""
echo "3. Install missing security tools:"
echo "   pip install bandit safety"
echo ""
echo "4. Address any warnings shown above"
echo ""
echo "5. Create a test PR to verify the workflow runs correctly"
echo ""
echo "6. Review the setup guide: SECURITY_REVIEW_SETUP.md"
echo ""
echo "=============================================="
print_status 0 "Security review setup test complete!"
echo "=============================================="
