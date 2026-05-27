#!/bin/bash
set -e

echo "Archiving BecomingONE and Fieldprint to IPFS..."

BECOMINGONE_DIR="${BECOMINGONE_DIR:-/home/gemini/becomingone}"
FIELDPRINT_DIR="${FIELDPRINT_DIR:-/home/gemini/master-fieldprint_repo}"
TMP_DIR="/tmp/ipfs_archive_$$"
ARCHIVES_JSON="${BECOMINGONE_DIR}/scripts/archives.json"
GENERATE_SCRIPT="${BECOMINGONE_DIR}/scripts/generate_index.py"

mkdir -p $TMP_DIR

echo "Exporting repositories..."
git -C $BECOMINGONE_DIR archive HEAD | tar -x -C $TMP_DIR/becomingone 2>/dev/null || { mkdir -p $TMP_DIR/becomingone && rsync -a --exclude=.git $BECOMINGONE_DIR/ $TMP_DIR/becomingone/; }
git -C $FIELDPRINT_DIR archive HEAD | tar -x -C $TMP_DIR/fieldprint 2>/dev/null || { mkdir -p $TMP_DIR/fieldprint && rsync -a --exclude=.git $FIELDPRINT_DIR/ $TMP_DIR/fieldprint/; }

echo "Copying archives into IPFS pod..."
POD_NAME=$(kubectl get pods -l app=ipfs-node -o jsonpath="{.items[0].metadata.name}")

kubectl exec $POD_NAME -- mkdir -p /tmp/archives
kubectl cp $TMP_DIR/becomingone $POD_NAME:/tmp/archives/becomingone
kubectl cp $TMP_DIR/fieldprint $POD_NAME:/tmp/archives/fieldprint

echo "Pinning to IPFS..."
BECOMINGONE_CID=$(kubectl exec $POD_NAME -- ipfs add -r -Q /tmp/archives/becomingone)
FIELDPRINT_CID=$(kubectl exec $POD_NAME -- ipfs add -r -Q /tmp/archives/fieldprint)

echo "Generating frontend index..."
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Update archives.json
if [ ! -f $ARCHIVES_JSON ]; then
  echo "[]" > $ARCHIVES_JSON
fi

# Use python to append to JSON safely
python3 -c "
import json, sys
data = []
try:
    with open('$ARCHIVES_JSON', 'r') as f:
        data = json.load(f)
except:
    pass
data.append({'repo': 'becomingone', 'cid': '$BECOMINGONE_CID', 'timestamp': '$TIMESTAMP'})
data.append({'repo': 'master-fieldprint', 'cid': '$FIELDPRINT_CID', 'timestamp': '$TIMESTAMP'})
with open('$ARCHIVES_JSON', 'w') as f:
    json.dump(data, f, indent=2)
"

# Run HTML generator
export ARCHIVES_FILE="$ARCHIVES_JSON"
python3 $GENERATE_SCRIPT

# Deploy to Nginx Pod
NGINX_POD=$(kubectl get pods -l app=ipfs-index -o jsonpath="{.items[0].metadata.name}")
kubectl cp /tmp/index.html $NGINX_POD:/usr/share/nginx/html/index.html

echo "========================================="
echo "IPFS Archival & Index Update Complete!"
echo "BecomingONE CID: $BECOMINGONE_CID"
echo "Fieldprint CID:  $FIELDPRINT_CID"
echo "========================================="

# Clean up
rm -rf $TMP_DIR
kubectl exec $POD_NAME -- rm -rf /tmp/archives
