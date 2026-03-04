#!/bin/bash

# Telephony Mastery Content Processing Pipeline
# Automated processing system for content truncation, AI summarization, and deployment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORD_LIMIT=300
ANTHROPIC_KEY=""
SKIP_SUMMARIES=false
VALIDATE_ONLY=false

# Functions
print_header() {
    echo -e "${BLUE}$1${NC}"
    echo "=========================================="
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

show_help() {
    cat << EOF
Telephony Mastery Content Processing Pipeline

USAGE:
    ./process_content.sh [OPTIONS]

OPTIONS:
    -h, --help              Show this help message
    -w, --word-limit NUM    Word limit for public content (default: 300)
    -k, --anthropic-key KEY Anthropic API key for AI summaries
    --skip-summaries        Process content but skip AI summary generation
    --validate-only         Only validate existing deployment
    --clean                 Clean all processed content and start fresh

EXAMPLES:
    # Full processing with AI summaries
    ./process_content.sh --anthropic-key "sk-ant-..."
    
    # Process content without AI summaries
    ./process_content.sh --skip-summaries
    
    # Use custom word limit
    ./process_content.sh --word-limit 500 --anthropic-key "sk-ant-..."
    
    # Validate existing deployment
    ./process_content.sh --validate-only

WORKFLOW:
    1. Extract first N words from markdown files in /content/
    2. Create public (truncated) and private (complete) versions
    3. Generate AI summaries of remaining content (if API key provided)
    4. Prepare deployment package with only public content
    5. Validate deployment safety

OUTPUT DIRECTORIES:
    content-processing/public/    - Truncated public content
    content-processing/private/   - Complete private content  
    content-processing/summaries/ - AI-generated summaries
    content-processing/deploy/    - Safe deployment package

SAFETY FEATURES:
    - Full content never leaves private directory
    - Deployment package includes only truncated content
    - Automatic validation prevents private content leakage
    - Comprehensive .gitignore protection
EOF
}

clean_processed_content() {
    print_header "Cleaning Processed Content"
    
    if [ -d "content-processing" ]; then
        rm -rf content-processing
        print_success "Cleaned content-processing directory"
    else
        print_warning "No processed content to clean"
    fi
    
    if [ -f "scripts/processing_report.json" ]; then
        rm scripts/processing_report.json
        print_success "Cleaned processing report"
    fi
    
    if [ -f "scripts/summary_report.json" ]; then
        rm scripts/summary_report.json
        print_success "Cleaned summary report"
    fi
}

check_dependencies() {
    print_header "Checking Dependencies"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    print_success "Python 3 found"
    
    # Setup virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        print_warning "Creating virtual environment..."
        python3 -m venv .venv
        print_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    print_success "Virtual environment activated"
    
    # Check required Python packages
    python3 -c "import yaml, anthropic" 2>/dev/null || {
        print_warning "Required Python packages not found. Installing..."
        pip install pyyaml anthropic
        print_success "Python packages installed"
    }
    
    # Check content directory
    if [ ! -d "content" ]; then
        print_error "Content directory not found. Make sure you're in the correct directory."
        exit 1
    fi
    print_success "Content directory found"
    
    # Count markdown files
    md_count=$(find content -name "*.md" | wc -l)
    print_success "Found $md_count markdown files to process"
}

process_content() {
    print_header "Processing Content Files"
    
    echo "📝 Extracting first $WORD_LIMIT words from each file..."
    echo "🔄 Creating public and private versions..."
    
    source .venv/bin/activate
    python3 scripts/content_processor.py --word-limit "$WORD_LIMIT"
    
    if [ $? -eq 0 ]; then
        print_success "Content processing completed"
        
        # Show processing summary
        if [ -f "scripts/processing_report.json" ]; then
            echo ""
            echo "📊 Processing Summary:"
            source .venv/bin/activate
            python3 -c "
import json
with open('scripts/processing_report.json') as f:
    data = json.load(f)
    summary = data['processing_summary']
    stats = data['word_statistics']
    print(f\"Files processed: {summary['successful']}/{summary['total_files']}\")
    print(f\"Total words: {stats['total_words_across_all_files']:,}\")
    print(f\"Public words: {stats['public_words_across_all_files']:,}\")
    print(f\"Compression: {stats['compression_ratio']}\")
    print(f\"Truncated files: {summary['files_with_truncated_content']}\")
"
        fi
    else
        print_error "Content processing failed"
        exit 1
    fi
}

generate_summaries() {
    if [ "$SKIP_SUMMARIES" = true ]; then
        print_warning "Skipping AI summary generation"
        return 0
    fi
    
    if [ -z "$ANTHROPIC_KEY" ]; then
        print_warning "No Anthropic API key provided. Skipping AI summary generation."
        print_warning "Use --anthropic-key to enable AI summaries."
        return 0
    fi
    
    print_header "Generating AI Summaries"
    
    echo "🤖 Generating 5-bullet summaries of truncated content..."
    
    source .venv/bin/activate
    python3 scripts/summary_generator.py --anthropic-key "$ANTHROPIC_KEY"
    
    if [ $? -eq 0 ]; then
        print_success "AI summary generation completed"
        
        # Show summary statistics
        if [ -f "scripts/summary_report.json" ]; then
            echo ""
            echo "📋 Summary Generation Results:"
            source .venv/bin/activate
            python3 -c "
import json
with open('scripts/summary_report.json') as f:
    data = json.load(f)
    report = data['summary_generation_report']
    print(f\"Summaries generated: {report['summaries_generated']}/{report['total_files']}\")
    print(f\"Success rate: {report['success_rate']}\")
    print(f\"Files skipped: {report['files_skipped']}\")
"
        fi
    else
        print_error "AI summary generation failed"
        exit 1
    fi
}

prepare_deployment() {
    print_header "Preparing Deployment Package"
    
    echo "📦 Creating safe deployment package..."
    
    source .venv/bin/activate
    python3 scripts/deployment_manager.py prepare
    
    if [ $? -eq 0 ]; then
        print_success "Deployment package prepared"
    else
        print_error "Deployment preparation failed"
        exit 1
    fi
}

validate_deployment() {
    print_header "Validating Deployment Safety"
    
    echo "🔍 Checking for private content leakage..."
    
    source .venv/bin/activate
    python3 scripts/deployment_manager.py validate
    
    local validation_result=$?
    
    if [ $validation_result -eq 0 ]; then
        print_success "Deployment validation passed - safe for public release"
    else
        print_error "Deployment validation failed - UNSAFE for public release"
        exit 1
    fi
}

show_results() {
    print_header "Processing Complete"
    
    echo "📁 Output Directories:"
    echo "  • content-processing/public/    - Public content (truncated)"
    echo "  • content-processing/private/   - Private content (complete)"
    echo "  • content-processing/summaries/ - AI summaries"
    echo "  • content-processing/deploy/    - Deployment package"
    echo ""
    echo "📋 Reports:"
    [ -f "scripts/processing_report.json" ] && echo "  • scripts/processing_report.json - Content processing report"
    [ -f "scripts/summary_report.json" ] && echo "  • scripts/summary_report.json - AI summary report"
    echo ""
    
    # Show deployment status
    source .venv/bin/activate
    python3 scripts/deployment_manager.py status
    
    echo ""
    print_success "Content processing pipeline completed successfully!"
    
    echo ""
    echo "🚀 Next Steps:"
    echo "  • Review the deployment package in content-processing/deploy/"
    echo "  • Deploy the contents of deploy/ directory to your public site"
    echo "  • Keep content-processing/private/ secure and local"
    echo "  • Use AI summaries to provide value previews of advanced content"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -w|--word-limit)
            WORD_LIMIT="$2"
            shift 2
            ;;
        -k|--anthropic-key)
            ANTHROPIC_KEY="$2"
            shift 2
            ;;
        --skip-summaries)
            SKIP_SUMMARIES=true
            shift
            ;;
        --validate-only)
            VALIDATE_ONLY=true
            shift
            ;;
        --clean)
            clean_processed_content
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main execution
cd "$SCRIPT_DIR"

echo "🚀 Telephony Mastery Content Processing Pipeline"
echo "================================================"
echo ""

if [ "$VALIDATE_ONLY" = true ]; then
    validate_deployment
    exit 0
fi

# Run the pipeline
check_dependencies
process_content
generate_summaries
prepare_deployment
validate_deployment
show_results