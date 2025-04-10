#!/bin/bash

# Check if required environment variables are set
if [ -z "$SOURCE_URL" ] || [ -z "$SOURCE_ACCESS_TOKEN" ] || [ -z "$TARGET_URL" ] || [ -z "$TARGET_ACCESS_TOKEN" ]; then
    echo "Error: Required environment variables not set"
    echo "Please set SOURCE_URL, SOURCE_ACCESS_TOKEN, TARGET_URL, and TARGET_ACCESS_TOKEN"
    exit 1
fi

# Read the template
TEMPLATE=$(cat k8s/config-token-template.json)

# Generate source server config
SOURCE_CONFIG=$(echo "$TEMPLATE" | \
    sed "s|SOURCE_URL|$SOURCE_URL|g" | \
    sed "s|SOURCE_ACCESS_TOKEN|$SOURCE_ACCESS_TOKEN|g" | \
    sed 's|"serverId":"source-server"|"serverId":"source-server"|')

# Generate target server config
TARGET_CONFIG=$(echo "$TEMPLATE" | \
    sed "s|SOURCE_URL|$TARGET_URL|g" | \
    sed "s|SOURCE_ACCESS_TOKEN|$TARGET_ACCESS_TOKEN|g" | \
    sed 's|"serverId":"source-server"|"serverId":"target-server"|')

# Base64 encode the configurations
SOURCE_CONFIG_B64=$(echo -n "$SOURCE_CONFIG" | base64)
TARGET_CONFIG_B64=$(echo -n "$TARGET_CONFIG" | base64)

# Create secrets.yaml with the encoded values
cat > k8s/secrets.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: jfrog-secrets
type: Opaque
data:
  source-server-config: $SOURCE_CONFIG_B64
  target-server-config: $TARGET_CONFIG_B64
EOF

echo "Configuration tokens generated and saved to k8s/secrets.yaml"
echo "You can now apply the secrets using: kubectl apply -f k8s/secrets.yaml" 