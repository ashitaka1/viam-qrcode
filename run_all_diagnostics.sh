#!/bin/bash
# Master diagnostic script - runs all tests and generates a report

REPORT_FILE="diagnostic_report_$(date +%Y%m%d_%H%M%S).txt"

echo "==================================================================="
echo "PyInstaller OpenSSL Diagnostic Suite"
echo "==================================================================="
echo ""
echo "This will run all diagnostic tests and save to: $REPORT_FILE"
echo "Press Enter to continue..."
read

{
    echo "==================================================================="
    echo "DIAGNOSTIC REPORT"
    echo "Generated: $(date)"
    echo "Machine: $(hostname)"
    echo "==================================================================="
    echo ""

    echo "############################################################"
    echo "# 1. ENVIRONMENT INFORMATION"
    echo "############################################################"
    ./collect_env_info.sh
    echo ""
    echo ""

    if [ -f "dist/main" ]; then
        echo "############################################################"
        echo "# 2. BINARY INSPECTION"
        echo "############################################################"
        ./inspect_binary.sh
        echo ""
        echo ""
    else
        echo "############################################################"
        echo "# 2. BINARY INSPECTION"
        echo "############################################################"
        echo "dist/main not found - skipping binary inspection"
        echo "Run ./build.sh first to create the binary"
        echo ""
        echo ""
    fi

    echo "############################################################"
    echo "# 3. RUNTIME EXTRACTION TEST"
    echo "############################################################"
    ./test_extraction.sh
    TEST_RESULT=$?
    echo ""
    echo ""

    echo "############################################################"
    echo "# 4. BUILD LOG ANALYSIS"
    echo "############################################################"
    echo "Rebuilding to capture build log..."
    source .venv/bin/activate
    ./build.sh 2>&1 | tee /tmp/build_log.txt
    echo ""
    echo "Key sections from build log:"
    echo ""
    echo "--- OpenSSL Filtering ---"
    grep -A10 "Filtering opencv" /tmp/build_log.txt
    echo ""
    echo "--- hook-ssl execution ---"
    grep -A2 "hook-ssl" /tmp/build_log.txt
    echo ""
    echo ""

    echo "############################################################"
    echo "# 5. SUMMARY"
    echo "############################################################"
    echo "Test Results:"
    if [ $TEST_RESULT -eq 0 ]; then
        echo "  ✓ Runtime extraction test: PASSED"
        echo "  ✓ OpenSSL is working correctly on this machine"
    else
        echo "  ✗ Runtime extraction test: FAILED"
        echo "  ✗ OpenSSL import fails on this machine"
    fi
    echo ""
    echo "Next steps:"
    if [ $TEST_RESULT -eq 0 ]; then
        echo "  - This machine builds working binaries"
        echo "  - Compare this report with the failing machine"
        echo "  - Look for differences in:"
        echo "    * macOS version"
        echo "    * Python installation path"
        echo "    * OpenSSL location"
        echo "    * PyInstaller version"
    else
        echo "  - This machine has the OpenSSL issue"
        echo "  - Compare this report with a working machine"
        echo "  - Check if OpenSSL libraries are in the bundle"
        echo "  - Check if they're being extracted to _MEI directory"
    fi
    echo ""
    echo "==================================================================="
    echo "END OF REPORT"
    echo "==================================================================="

} 2>&1 | tee "$REPORT_FILE"

echo ""
echo "Report saved to: $REPORT_FILE"
echo ""
echo "To share this with Claude:"
echo "  1. Open Claude on the other machine"
echo "  2. Upload the $REPORT_FILE file"
echo "  3. Reference DEBUG_OPENSSL_ISSUE.md for context"
