#!/bin/bash
set -euo pipefail

# The service image does not include all tools needed to download its models.
missing_packages=()
if ! command -v curl &> /dev/null; then
    missing_packages+=(curl ca-certificates)
fi
if ! command -v unzip &> /dev/null; then
    missing_packages+=(unzip)
fi
if [ ${#missing_packages[@]} -gt 0 ]; then
    apt-get update
    apt-get install -y --no-install-recommends "${missing_packages[@]}"
fi

MODEL_DIR="${MODEL_DIR:-/cat/models}"
mkdir -p "$MODEL_DIR"
CDB="$MODEL_DIR/medmen.cdb"
VOCAB="$MODEL_DIR/vocab.dat"
META_DIR="$MODEL_DIR/mc_status"

download_model() {
    local target="$1"
    local url="$2"
    if [ -s "$target" ]; then
        echo "$(basename "$target") already exists -- skipping"
        return
    fi
    echo "Downloading $(basename "$target")..."
    curl --fail --location --retry 3 --connect-timeout 30 \
        --output "$target.tmp" "$url"
    test -s "$target.tmp"
    mv "$target.tmp" "$target"
}

download_model "$CDB" \
    https://cogstack-medcat-example-models.s3.eu-west-2.amazonaws.com/medcat-example-models/cdb-medmen-v1.dat
download_model "$VOCAB" \
    https://cogstack-medcat-example-models.s3.eu-west-2.amazonaws.com/medcat-example-models/vocab.dat

# Download and unzip meta model if needed
if [ ! -d "$META_DIR" ]; then
    echo "Downloading and extracting MetaCAT model (mc_status)..."
    download_model "$MODEL_DIR/mc_status.zip" \
        https://cogstack-medcat-example-models.s3.eu-west-2.amazonaws.com/medcat-example-models/mc_status.zip
    mkdir -p "$META_DIR.tmp"
    if ! unzip -oq "$MODEL_DIR/mc_status.zip" -d "$META_DIR.tmp"; then
        echo "MetaCAT extraction failed; removing cached archive and staged files before retry." >&2
        rm -f -- "$MODEL_DIR/mc_status.zip"
        rm -rf -- "$META_DIR.tmp"
        exit 1
    fi
    mv "$META_DIR.tmp" "$META_DIR"
    rm "$MODEL_DIR/mc_status.zip"
else
    echo "Meta model already exists -- skipping"
fi

# Start MedCAT
exec bash ./start_service_production.sh
