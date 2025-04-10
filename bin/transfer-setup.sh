#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Function to print error message and exit
function error_exit {
    echo "$1" >&2
    exit 1
}

# Load environment variables from .env file
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs) || error_exit "Error: Failed to load .env file!"
else
    error_exit "Error: .env file not found!"
fi

# Check and export environment variables
export JFROG_CLI_WORK_DIR=${JFROG_CLI_WORK_DIR:?Need to set JFROG_CLI_WORK_DIR}
export JFROG_HOME=${JFROG_HOME:?Need to set JFROG_HOME}
export JFROG_CLI_HOME_DIR=${JFROG_CLI_HOME_DIR:?Need to set JFROG_CLI_HOME_DIR}
export SOURCE_SERVER_URL=${SOURCE_SERVER_URL:?Need to set SOURCE_SERVER_URL}
export SOURCE_ACCESS_TOKEN=${SOURCE_ACCESS_TOKEN:?Need to set SOURCE_ACCESS_TOKEN}
export TARGET_SERVER_URL=${TARGET_SERVER_URL:?Need to set TARGET_SERVER_URL}
export TARGET_ACCESS_TOKEN=${TARGET_ACCESS_TOKEN:?Need to set TARGET_ACCESS_TOKEN}

# Create temp directory
echo "Creating temp directory: $JFROG_CLI_TEMP_DIR"
mkdir -p "$JFROG_CLI_TEMP_DIR" || error_exit "Error: Failed to create temp directory!"

# Change to working directory
cd "$JFROG_CLI_WORK_DIR" || error_exit "Error: Failed to change to working directory!"

# Download JFrog cli
echo "Downloading JFrog cli..."
curl -fkL https://getcli.jfrog.io/v2-jf | sh || error_exit "Error: Failed to download JFrog cli!"

# Install JFrog cli dependencies
chmod +x jf


# export JFROG_CLI_HOME_DIR=/Users/alexsh/projects/customers/Xcel/cloud-transfer-setup/var/.jfrog
# Configure source server for cloud transfer
echo "Configuring source server..."
./jf config add --access-token="$SOURCE_ACCESS_TOKEN" --url="$SOURCE_SERVER_URL" --interactive=false source-server || error_exit "Error: Failed to configure source server!"

# Configure target server
echo "Configuring target server..."
./jf config add --access-token="$TARGET_ACCESS_TOKEN" --url="$TARGET_SERVER_URL" --interactive=false target-server || error_exit "Error: Failed to configure target server!"

# Preview the configuration
echo "Previewing the configuration..."
./jf c s || error_exit "Error: Failed to preview the configuration!"

# Download plugin dependencies
echo "Downloading Cloud Transfer plugin dependencies..."
curl -k -O -g https://releases.jfrog.io/artifactory/jfrog-releases/data-transfer/\[RELEASE\]/lib/data-transfer.jar || error_exit "Error: Failed to download data-transfer.jar!"
curl -k -O -g https://releases.jfrog.io/artifactory/jfrog-releases/data-transfer/\[RELEASE\]/dataTransfer.groovy || error_exit "Error: Failed to download dataTransfer.groovy!"

# Install the plugin
echo "Installing the Cloud Transfer plugin..."
./jf rt transfer-plugin-install source-server --dir "$JFROG_CLI_WORK_DIR" --home-dir "$JFROG_HOME" || error_exit "Error: Failed to install the Cloud Transfer plugin!"

# Verify connectivity
echo "Verifying connectivity..."
./jf rt ping --server-id source-server || error_exit "Error: Source server is not reachable!"
./jf rt ping --server-id target-server || error_exit "Error: Target server is not reachable!"

# Run prechecks
echo "Running prechecks..."
./jf rt transfer-config source-server target-server --prechecks || error_exit "Error: Prechecks failed!"

echo "Script executed successfully!"