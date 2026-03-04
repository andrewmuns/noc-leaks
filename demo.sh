#!/bin/bash

# Demo Script for Telephony Mastery Content Processing System
# This script demonstrates the full capabilities of the system

set -e

echo "📚 Telephony Mastery Content Processing System Demo"
echo "==================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎯 What this demo will show:${NC}"
echo "1. Basic content processing (truncation to 300 words)"
echo "2. Public vs private content separation"
echo "3. Safe deployment package creation"
echo "4. Validation of deployment safety"
echo ""

echo -e "${YELLOW}Note: AI summary generation requires an Anthropic API key${NC}"
echo "To test with AI summaries, run:"
echo "  ./process_content.sh --anthropic-key 'sk-ant-your-key'"
echo ""

read -p "Press Enter to start the demo..."

echo ""
echo -e "${BLUE}🚀 Running Content Processing Pipeline...${NC}"
echo ""

./process_content.sh --skip-summaries

echo ""
echo -e "${BLUE}📊 Demo Results Summary:${NC}"
echo ""

# Show directory structure
echo "📁 Generated Directory Structure:"
tree content-processing/ -L 2 2>/dev/null || find content-processing/ -type d | head -10

echo ""
echo "📄 Sample Files Created:"
echo "Public content samples:"
ls content-processing/public/ | head -3
echo ""
echo "Private content samples:"
ls content-processing/private/ | head -3

echo ""
echo "🔍 Content Analysis:"

# Count files
PUBLIC_COUNT=$(find content-processing/public -name "*.md" | wc -l)
PRIVATE_COUNT=$(find content-processing/private -name "*.md" | wc -l)
DEPLOY_COUNT=$(find content-processing/deploy/content -name "*.md" | wc -l)

echo "  • Public files: $PUBLIC_COUNT"
echo "  • Private files: $PRIVATE_COUNT"
echo "  • Deploy-ready files: $DEPLOY_COUNT"

echo ""
echo -e "${GREEN}✅ Demo Complete!${NC}"
echo ""

echo "🔍 To explore the results:"
echo "  • View public content: ls content-processing/public/"
echo "  • Check deployment package: ls content-processing/deploy/"
echo "  • Read processing report: cat scripts/processing_report.json"
echo ""

echo "🚀 To deploy (example):"
echo "  • Copy deployment package: rsync -av content-processing/deploy/ your-site/"
echo "  • Or upload to cloud: aws s3 sync content-processing/deploy/ s3://your-bucket/"
echo ""

echo "🤖 To add AI summaries:"
echo "  • Get Anthropic API key from https://console.anthropic.com/"
echo "  • Run: ./process_content.sh --anthropic-key 'sk-ant-your-key'"
echo ""

echo "📚 Full documentation available in CONTENT_PROCESSING_README.md"