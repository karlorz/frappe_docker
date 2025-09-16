#!/bin/bash

# macOS Build Script for Frappe Docker Production Images
# Optimized for Apple Silicon (ARM64) and Intel Macs

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
PLATFORM="linux/arm64"
TARGET=""
FRAPPE_VERSION="version-15-dev"
ERPNEXT_VERSION="version-15-dev"
REGISTRY_USER="ghcr.io/karlorz"
BUILD_ARGS=""
PUSH=false

# Help function
show_help() {
    cat << EOF
macOS Build Script for Frappe Docker Production Images

Usage: $0 [OPTIONS] [TARGET]

TARGETS:
    all, default    Build all targets (base, build, erpnext)
    base           Build base Frappe image only  
    build          Build development image with build tools
    erpnext        Build ERPNext production image
    bench          Build bench tools image

OPTIONS:
    -p, --platform PLATFORM    Target platform (default: linux/arm64)
                               Options: linux/arm64, linux/amd64, linux/arm64,linux/amd64
    -f, --frappe VERSION       Frappe version/branch (default: version-15-dev)
    -e, --erpnext VERSION      ERPNext version/branch (default: version-15-dev)
    -r, --registry USER        Registry user (default: ghcr.io/karlorz)
    --push                     Push images to registry after build
    --no-cache                 Build without cache
    --load                     Load images to local Docker (single platform only)
    --progress TYPE            Progress output type (auto, plain, tty, rawjson)
    -h, --help                 Show this help message

EXAMPLES:
    # Build all targets for ARM64 (Apple Silicon)
    $0 all

    # Build specific target for both ARM64 and AMD64
    $0 -p linux/arm64,linux/amd64 erpnext

    # Build with specific versions
    $0 -f v15.0.0 -e v15.0.0 erpnext

    # Build and push to registry
    $0 --push erpnext

    # Build for Intel Mac
    $0 -p linux/amd64 all
EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--platform)
            PLATFORM="$2"
            shift 2
            ;;
        -f|--frappe)
            FRAPPE_VERSION="$2" 
            shift 2
            ;;
        -e|--erpnext)
            ERPNEXT_VERSION="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY_USER="$2"
            shift 2
            ;;
        --push)
            PUSH=true
            BUILD_ARGS="$BUILD_ARGS --push"
            shift
            ;;
        --no-cache)
            BUILD_ARGS="$BUILD_ARGS --no-cache"
            shift
            ;;
        --load)
            BUILD_ARGS="$BUILD_ARGS --load"
            shift
            ;;
        --progress)
            BUILD_ARGS="$BUILD_ARGS --progress=$2"
            shift 2
            ;;
        --progress=*)
            BUILD_ARGS="$BUILD_ARGS --progress=${1#*=}"
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        all|default|base|build|erpnext|bench)
            TARGET="$1"
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Default target if none specified
if [[ -z "$TARGET" ]]; then
    TARGET="all"
fi

# Validate platform
if [[ "$BUILD_ARGS" == *"--load"* ]] && [[ "$PLATFORM" == *","* ]]; then
    echo -e "${RED}Error: --load cannot be used with multi-platform builds${NC}"
    echo "Use single platform (e.g., linux/arm64) or remove --load flag"
    exit 1
fi

# Display build configuration
echo -e "${GREEN}=== macOS Frappe Docker Build Configuration ===${NC}"
echo "Platform: $PLATFORM"
echo "Target: $TARGET"
echo "Frappe Version: $FRAPPE_VERSION"
echo "ERPNext Version: $ERPNEXT_VERSION" 
echo "Registry: $REGISTRY_USER"
if [[ "$PUSH" == "true" ]]; then
    echo -e "${YELLOW}Will push to registry after build${NC}"
fi
echo

# Export environment variables for docker-bake.hcl
export REGISTRY_USER="$REGISTRY_USER"
export FRAPPE_VERSION="$FRAPPE_VERSION"
export ERPNEXT_VERSION="$ERPNEXT_VERSION"

# Build command based on target
build_target() {
    local target=$1
    local platform_arg="--set *.platform=$PLATFORM"
    
    echo -e "${GREEN}Building $target for $PLATFORM...${NC}"
    
    if [[ "$target" == "all" || "$target" == "default" ]]; then
        # Build all default targets
        docker buildx bake $platform_arg $BUILD_ARGS
    else
        # Build specific target
        docker buildx bake $platform_arg $BUILD_ARGS "$target"
    fi
}

# Check if buildx is available and initialized
if ! docker buildx version &> /dev/null; then
    echo -e "${RED}Error: Docker Buildx is not available${NC}"
    exit 1
fi

# Check if multibuilder exists, create if not
if ! docker buildx inspect multibuilder &> /dev/null; then
    echo -e "${YELLOW}Creating multibuilder buildx instance...${NC}"
    docker buildx create --name multibuilder --driver docker-container --bootstrap
    docker buildx use multibuilder
fi

# Ensure we're using the right builder
docker buildx use multibuilder

# Perform the build
echo -e "${GREEN}Starting build process...${NC}"
build_target "$TARGET"

if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✅ Build completed successfully!${NC}"
    
    if [[ "$PUSH" == "false" && "$BUILD_ARGS" != *"--load"* ]]; then
        echo -e "${YELLOW}💡 Images built but not loaded to local Docker${NC}"
        echo "To load images locally, add --load flag (single platform only)"
        echo "To push to registry, add --push flag"
    fi
else
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi