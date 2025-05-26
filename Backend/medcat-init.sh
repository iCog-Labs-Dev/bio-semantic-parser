#!/bin/bash
set -e
# Ensure curl is installed
if ! command -v curl &> /dev/null; then
    echo "curl not found, installing..."
    apt-get update && apt-get install -y curl
fi
MODEL_DIR="/cat/models"
CDB="$MODEL_DIR/medmen.cdb"
VOCAB="$MODEL_DIR/vocab.dat"
META_DIR="$MODEL_DIR/mc_status"

# Download medmen.cdb
if [ ! -f "$CDB" ]; then
    echo "Downloading medmen.cdb..."
    curl -L -o "$CDB.tmp" https://cogstack-medcat-example-models.s3.eu-west-2.amazonaws.com/medcat-example-models/cdb-medmen-v1.dat
    mv "$CDB.tmp" "$CDB"
else
    echo "medmen.cdb already exists -- skipping"
fi

# Download vocab.dat
if [ ! -f "$VOCAB" ]; then
    echo "Downloading vocab.dat..."
    curl -L -o "$VOCAB.tmp" https://cogstack-medcat-example-models.s3.eu-west-2.amazonaws.com/medcat-example-models/vocab.dat
    mv "$VOCAB.tmp" "$VOCAB"
else
    echo "vocab.dat already exists -- skipping"
fi

# Download and unzip meta model if needed
if [ ! -d "$META_DIR" ]; then
    echo "Downloading and extracting MetaCAT model (mc_status)..."
    mkdir -p "$META_DIR"
    curl -L -o "$META_DIR/mc_status.zip" https://cogstack-medcat-example-models.s3.eu-west-2.amazonaws.com/medcat-example-models/mc_status.zip
    unzip "$META_DIR/mc_status.zip" -d "$META_DIR"
    rm "$META_DIR/mc_status.zip"
else
    echo "Meta model already exists -- skipping"
fi

# Start MedCAT
chmod +x ./start-service-prod.sh
exec ./start-service-prod.sh