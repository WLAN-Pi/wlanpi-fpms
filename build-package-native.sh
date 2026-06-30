#!/bin/bash
#
# Build wlanpi-fpms Debian package in a container (podman or docker)
#
# Usage: ./build-package-native.sh [SUITE]
#   SUITE   Debian release to build for: bullseye | bookworm | trixie (default: trixie)
#
# The container engine is auto-detected (podman preferred, then docker).
# Override it explicitly with CONTAINER_ENGINE, e.g.:
#   CONTAINER_ENGINE=docker ./build-package-native.sh trixie
#
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Debian release to build for
SUITE="${1:-trixie}"

# Detect container engine (override with CONTAINER_ENGINE)
if [ -n "$CONTAINER_ENGINE" ]; then
    ENGINE="$CONTAINER_ENGINE"
elif command -v podman &> /dev/null; then
    ENGINE="podman"
elif command -v docker &> /dev/null; then
    ENGINE="docker"
else
    echo "ERROR: no container engine found!"
    echo "Please install podman or docker (or set CONTAINER_ENGINE)."
    exit 1
fi

if ! command -v "$ENGINE" &> /dev/null; then
    echo "ERROR: container engine '$ENGINE' not found!"
    exit 1
fi

IMAGE="wlanpi-fpms-builder:${SUITE}"

# Clean up old build manifest
rm -f .build-manifest.txt

echo "========================================="
echo "Building wlanpi-fpms Debian Package"
echo "  engine: $ENGINE"
echo "  suite:  $SUITE"
echo "========================================="

echo "Step 1: Building container image..."
"$ENGINE" build -f Dockerfile.build --build-arg SUITE="$SUITE" -t "$IMAGE" .

echo ""
echo "Step 2: Building Debian package in container..."
echo "(This may take several minutes...)"
echo ""

# Run the build in container
"$ENGINE" run --rm \
    -v "$(pwd)":/work:Z \
    -w /work \
    "$IMAGE" \
    bash -c '
set -e

echo "Refreshing package lists..."
apt-get update

echo "Installing package build dependencies..."
mk-build-deps --install --remove --tool "apt-get -y --no-install-recommends" debian/control

echo ""
echo "Building package..."
dpkg-buildpackage -us -uc -b

echo ""
echo "Copying packages from container to host..."
cp -v /*.deb /work/ 2>/dev/null || echo "No .deb files found in container root"

echo ""
echo "Creating build manifest..."
cd /work && ls -1 wlanpi-fpms*.deb 2>/dev/null | grep -v dbgsym > .build-manifest.txt || true

echo ""
echo "Build complete!"
'

echo ""
echo "========================================="
echo "Package Build Complete!"
echo "========================================="
echo ""
echo "Generated packages:"
ls -lh wlanpi-fpms*.deb 2>/dev/null || echo "No wlanpi-fpms .deb files found"
echo ""
echo "To install the package:"
echo "  sudo dpkg -i wlanpi-fpms*.deb"
echo "  sudo apt-get install -f  # if there are dependency issues"
echo ""
