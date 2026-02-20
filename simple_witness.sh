#!/bin/bash
#
# simple_witness.sh - Witness a BECOMINGONE instance using curl
#
# Usage:
#   ./simple_witness.sh http://localhost:8000 witness-seed
#
# Environment variables:
#   TARGET_URL - Target URL (default: http://localhost:8000)
#   WITNESS_NAME - Name of witness (default: witness)
#

set -e

# Default values
TARGET_URL="${1:-${TARGET_URL:-http://localhost:8000}}"
WITNESS_NAME="${2:-${WITNESS_NAME:-witness}}"

# Get timestamp
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S")

echo "🔍 Witnessing: $TARGET_URL (witness: $WITNESS_NAME) at $TIMESTAMP"

# Health check
HEALTH=$(curl -s --max-time 5 "$TARGET_URL/health" 2>/dev/null || echo '{"error": "timeout"}')
HEALTH_UP=$(echo "$HEALTH" | grep -o '"status":"ready"' || echo "")

if [ -n "$HEALTH_UP" ]; then
    echo "✅ Target is UP"
    
    # Get coherence
    COHERENCE=$(curl -s --max-time 5 "$TARGET_URL/coherence" 2>/dev/null || echo '{}')
    
    MASTER_C=$(echo "$COHERENCE" | grep -o '"master_coherence":[^,}]*' | cut -d: -f2 || echo "N/A")
    EMISSARY_C=$(echo "$COHERENCE" | grep -o '"emissary_coherence":[^,}]*' | cut -d: -f2 || echo "N/A")
    SYNC_ALIGNED=$(echo "$COHERENCE" | grep -o '"sync_aligned":[^,}]*' | cut -d: -f2 || echo "N/A")
    
    echo "   Master coherence:   $MASTER_C"
    echo "   Emissary coherence: $EMISSARY_C"
    echo "   Sync aligned:       $SYNC_ALIGNED"
    
    # Build observation JSON
    OBSERVATION=$(cat <<EOF
{
    "timestamp": "$TIMESTAMP",
    "witness": "$WITNESS_NAME",
    "target": "$TARGET_URL",
    "target_up": true,
    "master_coherence": $MASTER_C,
    "emissary_coherence": $EMISSARY_C,
    "sync_aligned": $SYNC_ALIGNED
}
EOF
)
    
else
    echo "❌ Target is DOWN"
    
    ERROR_MSG=$(echo "$HEALTH" | grep -o '"message":"[^"]*"' | cut -d'"' -f4 || echo "Unknown error")
    echo "   Error: $ERROR_MSG"
    
    OBSERVATION=$(cat <<EOF
{
    "timestamp": "$TIMESTAMP",
    "witness": "$WITNESS_NAME",
    "target": "$TARGET_URL",
    "target_up": false,
    "error": "$ERROR_MSG"
}
EOF
)
fi

# Save observation
FILENAME="witness_${WITNESS_NAME// /-}.json"
echo "$OBSERVATION" > "$FILENAME"
echo ""
echo "📝 Saved observation to $FILENAME"
