# Kubernetes Transfer Configuration

### Generate secret that holds configuration tokens for JFrog CLI

`jfrog-secrets` kubernetes secret is used to configure `jf cli` with the coordinates of source and target servers.
Config Tokens are provided by secrets that populate SOURCE_SERVER_CONFIG and TARGET_SERVER_CONFIG environment variables of the deployment

**Generate secret.yaml**

1. Set required environment variables:
```bash
export SOURCE_URL="http://artifactory.artifactory.svc.cluster.local:8082" \
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

Data Transfer and optionally, Config Import plugins must be configured in values.yaml files of the Helm Charts of source Artifactory, and target, if not transfering to SaaS. (SaaS will have Config Import Plugin enabled using UI toggle).

Plugin dependencies files are provided as secret values to Artifactory Kubernetes resources.

1. Download plugin files

```sh
curl -k -O -g "https://releases.jfrog.io/artifactory/jfrog-releases/data-transfer/[RELEASE]/lib/data-transfer.jar"
curl -k -O -g "https://releases.jfrog.io/artifactory/jfrog-releases/data-transfer/[RELEASE]/dataTransfer.groovy"
curl -k -O -g "https://releases.jfrog.io/artifactory/jfrog-releases/config-import/[RELEASE]/lib/config-import.jar"
curl -k -O -g "https://releases.jfrog.io/artifactory/jfrog-releases/config-import/[RELEASE]/configImport.groovy"     
```

2. Create plugin secret

**On Source kubernetes cluster**

```sh
kubectl create secret generic data-transfer-plugin --from-file=dataTransfer.groovy --from-file=data-transfer.jar --namespace=artifactory
```

3. Modify `values.yaml` of source Artifactory Helm Chart

```yaml
artifactory:
  userPluginSecrets:
    - data-transfer-plugin

  preStartCommand: "mkdir -p {{ .Values.artifactory.persistence.mountPath }}/etc/artifactory/plugins/lib && cp -Lrf /artifactory_bootstrap/plugins/*.groovy {{ .Values.artifactory.persistence.mountPath }}/etc/artifactory/plugins/ && cp -Lrf /artifactory_bootstrap/plugins/*.jar {{ .Values.artifactory.persistence.mountPath }}/etc/artifactory/plugins/lib"

```

4. Create Secret for Import Plugin - **On Target kubernetes cluster (if not transferring to SaaS)**

```sh
kubectl create secret generic config-import-plugin --from-file=configImport.groovy --from-file=config-import.jar --namespace=jfrog-platform
```

5. Modify `values.yaml` of source Artifactory Helm Chart - **On Target kubernetes cluster (if not transferring to SaaS)**

```yaml
artifactory:
  artifactory:
    userPluginSecrets:
    - config-import-plugin

    preStartCommand: "mkdir -p {{ .Values.artifactory.persistence.mountPath }}/etc/artifactory/plugins/lib && cp -Lrf /artifactory_bootstrap/plugins/*.groovy {{ .Values.artifactory.persistence.mountPath }}/etc/artifactory/plugins/ && cp -Lrf /artifactory_bootstrap/plugins/*.jar {{ .Values.artifactory.persistence.mountPath }}/etc/artifactory/plugins/lib"
```

6. Kubernetes Deployment must have PVC that has /opt/jfrog directory that is used by Artifactory pod
Modify deployment yaml `persistentVolumeClaim:` to point to PVC used by Artifactory

```yaml
volumes:
- name: jfrog-data
  persistentVolumeClaim:
    claimName: artifactory-volume-artifactory-0 <---
```

```ssh
kubectl apply -f deployment.yaml --namespace artifactory
```

7. Run pre-flight checks from from pod shell of jfrog-transfer deploymewnt

```sh
kubectl exec -it <pod-name> -- jf rt transfer-config source-server target-server --prechecks --target-working-dir /tmp
```

Sample output

```sh
15:26:45 [🔵Info] Verifying minimum version of the source server...
15:26:45 [🔵Info] Verifying source and target servers are different...
15:26:45 [🔵Info] Verifying config-import plugin is installed in the target server...
15:26:45 [🔵Info] config-import plugin version: 1.3.1
15:26:45 [🔵Info] Verifying target server is empty...
15:26:46 [🔵Info] Getting all repositories ...
15:26:46 [🔵Info] Getting all repositories ...
15:26:46 [🔵Info] Repository 'example-repo-local' already exists in the target Artifactory server. Skipping.
15:26:46 [🔵Info] Deactivating key encryption in Artifactory...
15:26:46 [🔵Info] Artifactory key encryption deactivated
15:26:46 [🔵Info] Fetching config descriptor from Artifactory...
15:26:46 [🔵Info] Activating key encryption in Artifactory...
15:26:47 [🔵Info] Artifactory key encryption activated
15:26:47 [🔵Info] Running 2 checks.
15:26:47 [🔵Info] == Running check (1) 'Repositories naming' ======
15:26:47 [🔵Info] Check 'Repositories naming' is done with status Success
15:26:47 [🔵Info] == Running check (2) 'Remote repositories URL connectivity' ======
15:26:47 [🔵Info] Check 'Remote repositories URL connectivity' is done with status Success
15:26:47 [🔵Info] All the checks passed 🐸 (elapsed time 141.780916ms).
```

- Use `releases-docker.jfrog.io/jfrog/jfrog-cli-full-v2-jf` as an image for container


- Configure transfer-plugin
    - Download plugin files
        curl -k -O -g https://releases.jfrog.io/artifactory/jfrog-releases/data-transfer/\[RELEASE\]/lib/data-transfer.jar
        curl -k -O -g https://releases.jfrog.io/artifactory/jfrog-releases/data-transfer/\[RELEASE\]/dataTransfer.groovy

- Kubernetes Deployment must have PVC that has /opt/jfrog directory

- Add postStart should execute following command 
    jf rt transfer-plugin-install source-server
