#!/bin/bash
#
# CORS Testing Script
# Tests all common scenarios to verify CORS headers are present
#

BACKEND_URL="http://localhost:8000"
ORIGIN="http://localhost:5173"

echo "=================================="
echo "CORS Testing Script"
echo "=================================="
echo "Backend: $BACKEND_URL"
echo "Origin: $ORIGIN"
echo ""

# Test 1: Health endpoint (public, should work without auth)
echo "Test 1: Health endpoint (GET)"
curl -s -X GET "$BACKEND_URL/health" \
  -H "Origin: $ORIGIN" \
  -i 2>&1 | grep -E "HTTP/|access-control" | head -5
echo ""

# Test 2: Root endpoint
echo "Test 2: Root endpoint (GET)"
curl -s -X GET "$BACKEND_URL/" \
  -H "Origin: $ORIGIN" \
  -i 2>&1 | grep -E "HTTP/|access-control" | head -5
echo ""

# Test 3: Budget versions endpoint (requires auth)
echo "Test 3: Budget versions endpoint without auth (expect 401 with CORS headers)"
curl -s -X GET "$BACKEND_URL/api/v1/consolidation/budget-versions?page=1&page_size=50" \
  -H "Origin: $ORIGIN" \
  -i 2>&1 | grep -E "HTTP/|access-control" | head -5
echo ""

# Test 4: Activity endpoint (requires auth)
echo "Test 4: Activity endpoint without auth (expect 401 with CORS headers)"
curl -s -X GET "$BACKEND_URL/api/v1/analysis/activity?limit=10" \
  -H "Origin: $ORIGIN" \
  -i 2>&1 | grep -E "HTTP/|access-control" | head -5
echo ""

# Test 5: OPTIONS preflight request for budget-versions
echo "Test 5: OPTIONS preflight request for budget-versions"
curl -s -X OPTIONS "$BACKEND_URL/api/v1/consolidation/budget-versions" \
  -H "Origin: $ORIGIN" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: authorization,content-type" \
  -i 2>&1 | grep -E "HTTP/|access-control|allow-" | head -10
echo ""

# Test 6: Invalid endpoint (404)
echo "Test 6: Invalid endpoint (expect 404 with CORS headers)"
curl -s -X GET "$BACKEND_URL/api/v1/nonexistent" \
  -H "Origin: $ORIGIN" \
  -i 2>&1 | grep -E "HTTP/|access-control" | head -5
echo ""

echo "=================================="
echo "Test complete!"
echo "=================================="
echo ""
echo "Expected Results:"
echo "- All responses should include 'access-control-allow-origin: $ORIGIN'"
echo "- All responses should include 'access-control-allow-credentials: true'"
echo "- OPTIONS requests should include 'access-control-allow-methods' and 'access-control-allow-headers'"
echo ""
echo "If any test is missing CORS headers, there may be an issue with the backend configuration."
