README.md
# Setup and configure JFrog cli and Cloud Transfer Plugin for Kubernetes installations

This project 

## Install JFrog cli

Expands value of working directory from .env
    - JFROG_CLI_WORK_DIR=/opt/jfrog/artifactory/var/tmp

```sh
mkdir -p $JFROG_CLI_WORK_DIR
cd $JFROG_CLI_WORK_DIR
```

- Download JFrog cli

```sh
curl -fkL https://getcli.jfrog.io/v2-jf | sh
```

- Expands values of JFrog cli environment variables from .env and adds execute permission
    - JFROG_HOME=/opt/jfrog \
    - JFROG_CLI_HOME_DIR=/opt/jfrog/artifactory/var/tmp/.jfrog
    - JFROG_CLI_TEMP_DIR=/opt/jfrog/artifactory/var/tmp/.jfrog/tmp     

- Expands values from .env into SOURCE_SERVER_URL, SOURCE_ACCESS_TOKEN, TARGET_SERVER_URL, TARGET_ACCESS_TOKEN environment variables
    - SOURCE_SERVER_URL=http://localhost:8082
    - SOURCE_ACCESS_TOKEN=ey...
    - TARGET_SERVER_URL=http://jfrog-platform-artifactory.jfrog-platform.svc.cluster.local:8082
    - TARGET_ACCESS_TOKEN=ey...

## Configure source and destination servers

- Configure source server for cloud transfer

```sh
./jf config add --access-token=$SOURCE_ACCESS_TOKEN --url=$SOURCE_SERVER_URL --interactive=false source-server
```

- Confgigure target server 

```sh
./jf config add --access-token=$TARGET_ACCESS_TOKEN --url=$TARGET_SERVER_URL --interactive=false target-server
```

- Preview the configuration

```sh
./jf c s
```

## Configure Cloud Transfer Plugin

- Download plugin dependencies

```sh
curl -k -O -g https://releases.jfrog.io/artifactory/jfrog-releases/data-transfer/\[RELEASE\]/lib/data-transfer.jar
curl -k -O -g https://releases.jfrog.io/artifactory/jfrog-releases/data-transfer/\[RELEASE\]/dataTransfer.groovy
```

- Install the plugin

```sh
./jf rt transfer-plugin-install source-server --dir /opt/jfrog/artifactory/var/tmp --home-dir $JFROG_HOME
```

- Verify connectivity

```sh
./jf rt ping --server-id source-server
./jf rt ping --server-id target-server
```

- Run prechecks

```sh
./jf rt transfer-config source-server target-server --prechecks
```

## Copy files to container

- Create .env using .env.template
Set access tokens as needed

```sh
kubectl cp .env artifactory-0:/opt/jfrog/artifactory/var/ -c artifactory -n artifactory
kubectl cp transfer-setup.sh artifactory-0:/opt/jfrog/artifactory/var/ -c artifactory -n artifactory
```