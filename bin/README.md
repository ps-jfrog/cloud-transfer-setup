# Kubernetes Transfer Configuration

This version does not use helm charts to configure plugins.  It downloads and installs plugins using shell commands executed by k8s deployment upon startup.  This version only configures source server.  It needs to be run on all Artifactory instances.

### Generate secret that holds configuration tokens for JFrog CLI

`jfrog-secrets` kubernetes secret is used to configure `jf cli` with the coordinates of source and target servers.
Config Tokens are provided by secrets that populate SOURCE_SERVER_CONFIG and TARGET_SERVER_CONFIG environment variables of the deployment

**Generate secret.yaml**

1. Set required environment variables:
```bash
export SOURCE_URL="export SOURCE_URL="http://artifactory.artifactory.svc.cluster.local:8082" \
export SOURCE_ACCESS_TOKEN="your-source-access-token" \
export TARGET_URL="http://jfrog-platform-artifactory.jfrog-platform.svc.cluster.local:8082" \
export TARGET_ACCESS_TOKEN="your-target-access-token" 
```
2. Make the script executable:
```bash
chmod +x k8s/generate-config-tokens.sh
```
3. Run the script:
```bash
./k8s/generate-config-tokens.sh
```
4. Apply the generated secrets:
```bash
kubectl apply -f k8s/secrets.yaml
```

### Plugins dependencies configurations

Plugins dependencies a downloaded and installed by applying bin/kubernetes-script.yaml

```sh
kubectl apply -f bin/deployment-no-helm.yaml

- Run prechecks

```sh
jf rt transfer-config source-server target-server --target-working-dir /tmp --prechecks
```
