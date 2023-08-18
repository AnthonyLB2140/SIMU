# JSatOrb project: Dockerisation module : installing Docker

This document explains in details how to install Docker in a JSatOrb environment or in a generic Ubuntu 18.04 LTS 64 bit environment, which is the JSatOrb target platform.

The Linux free edition of Docker is the Community Edition (CE).

Installing Docker compose is also covered.

The proxy configuration is also covered, in case you have to operate behind a corporate proxy.

## Prerequisites

- Ubuntu 18.04 LTS,
- Internet connection,
- Admin rights (jsatorb user account).


## Docker versions used to produce the delivered JSatOrb server images

The following versions of docker modules have been installed and used in the development environment in order to produce the deliverables (extract from the installation logs):

Docker engine
```
Get:1 http://archive.ubuntu.com/ubuntu bionic/universe amd64 pigz amd64 2.4-1 [57.4 kB]
Get:2 https://download.docker.com/linux/ubuntu bionic/stable amd64 containerd.io amd64 1.2.13-2 [21.4 MB]
Get:3 http://archive.ubuntu.com/ubuntu bionic/universe amd64 aufs-tools amd64 1:4.9+20170918-1ubuntu1 [104 kB]
Get:4 http://archive.ubuntu.com/ubuntu bionic/universe amd64 cgroupfs-mount all 1.4 [6,320 B]
Get:5 https://download.docker.com/linux/ubuntu bionic/stable amd64 docker-ce-cli amd64 5:19.03.11~3-0~ubuntu-bionic [41.2 MB]
Get:6 https://download.docker.com/linux/ubuntu bionic/stable amd64 docker-ce amd64 5:19.03.11~3-0~ubuntu-bionic [22.5 MB]  
```

Docker compose:
```
docker-compose version 1.26.0, build d4451659
```


## Uninstalling old Docker versions

To uninstall a possible previous Docker installation, run the command:
```
>sudo apt-get remove docker docker-engine docker.io containerd runc
```


## Installing Docker

---

**NOTE**

___This whole paragraph ("Installing Docker"), except the last part ("Post-installation steps")  is an extract of the repository setup section from [this Docker documentation webpage.](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository#install-using-the-repository)___

___Remark: The test image run (hello-world) may not download and run successfully until you follow the Docker post-installation paragraph instructions.___

---

### Set up the repository

1. Update the `apt` package index and install packages to allow apt to use a repository over HTTPS:

```
>sudo apt-get update

>sudo apt-get install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common
```

2. Add Docker’s official GPG key:

```
>curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
```

Verify that you now have the key with the fingerprint `9DC8 5822 9FC7 DD38 854A  E2D8 8D81 803C 0EBF CD88`, by searching for the last 8 characters of the fingerprint.

```
>sudo apt-key fingerprint 0EBFCD88

pub   rsa4096 2017-02-22 [SCEA]
        9DC8 5822 9FC7 DD38 854A  E2D8 8D81 803C 0EBF CD88
uid           [ unknown] Docker Release (CE deb) <docker@docker.com>
sub   rsa4096 2017-02-22 [S]
```

3. Use the following command to set up the stable repository. To add the nightly or test repository, add the word nightly or test (or both) after the word stable in the commands below. Learn about nightly and test channels.

---

**NOTE**

The lsb_release -cs sub-command below returns the name of your Ubuntu distribution, such as xenial. Sometimes, in a distribution like Linux Mint, you might need to change $(lsb_release -cs) to your parent Ubuntu distribution. For example, if you are using Linux Mint Tessa, you could use bionic. Docker does not offer any guarantees on untested and unsupported Ubuntu distributions.

---

```
>sudo add-apt-repository \
    "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) \
    stable"
```    

#### Install Docker Engine

1. Update the `apt` package index, and install the _latest version_ of Docker Engine and containerd, or go to the next step to install a specific version:

```
>sudo apt-get update
>sudo apt-get install docker-ce docker-ce-cli containerd.io
```

---

**Got multiple Docker repositories ?**

If you have multiple Docker repositories enabled, installing or updating without specifying a version in the apt-get install or apt-get update command always installs the highest possible version, which may not be appropriate for your stability needs.

---

2. To install a specific version of Docker Engine, list the available versions in the repo, then select and install:

    a. List the versions available in your repo:

```
>apt-cache madison docker-ce

    docker-ce | 5:18.09.1~3-0~ubuntu-xenial | https://download.docker.com/linux/ubuntu  xenial/stable amd64 Packages
    docker-ce | 5:18.09.0~3-0~ubuntu-xenial | https://download.docker.com/linux/ubuntu  xenial/stable amd64 Packages
    docker-ce | 18.06.1~ce~3-0~ubuntu       | https://download.docker.com/linux/ubuntu  xenial/stable amd64 Packages
    docker-ce | 18.06.0~ce~3-0~ubuntu       | https://download.docker.com/linux/ubuntu  xenial/stable amd64 Packages

```

   b. Install a specific version using the version string from the second column, for example, `5:18.09.1~3-0~ubuntu-xenial`.

```
>sudo apt-get install docker-ce=<VERSION_STRING> docker-ce-cli=<VERSION_STRING> containerd.io
```

3. Verify that Docker Engine is installed correctly by running the hello-world image.

```
>sudo docker run hello-world
```

This command downloads a test image and runs it in a container. When the container runs, it prints an informational message and exits.

Docker Engine is installed and running. The `docker` group is created but no users are added to it. You need to use `sudo` to run Docker commands. Continue to `Linux postinstall` to allow non-privileged users to run Docker commands and for other optional configuration steps.

#### Upgrade Docker Engine

To upgrade Docker Engine, first run `sudo apt-get update`, then follow the installation instructions, choosing the new version you want to install.


#### Post-installation steps

If the previous Docker successfull installation step above failed (with the running of the Hello-world image), you may configure your user permissions and your proxy access.
To do so, follow the steps below.

##### Add user to docker group

---

**NOTE**

The information given in this paragraph is an adaptation fom [this Docker documentation webpage](https://docs.docker.com/engine/install/linux-postinstall/).

---

Create the docker group if it's not already existing:
```
>sudo groupadd docker
```

Add your user to the docker group:
```
>sudo usermod -aG docker $USER
```

Log out and log back in so that your group membership is re-evaluated.

On Linux, you can also run the following command to activate the changes to groups:
```
>newgrp docker
```

Verify that you can run docker commands without sudo.
```
>docker info
```


##### Proxy setup

---

**NOTE**

The information given in this paragraph is an adaptation from [this Docker documentation webpage](https://docs.docker.com/config/daemon/systemd/#httphttps-proxy).

---

This example overrides the default docker.service file.

If you are behind an HTTP or HTTPS proxy server, for example in corporate settings, you need to add this configuration in the Docker systemd service file.

Create a systemd drop-in directory for the docker service:
```
>sudo mkdir -p /etc/systemd/system/docker.service.d
```

Create a file called /etc/systemd/system/docker.service.d/http-proxy.conf that adds the HTTP_PROXY environment variable:

```
[Service]    
Environment="HTTP_PROXY=http://proxy.example.com:80/" "NO_PROXY=localhost,127.0.0.1,docker-registry.example.com,.corp"
```

Or, if you are behind an HTTPS proxy server, create a file called /etc/systemd/system/docker.service.d/https-proxy.conf that adds the HTTPS_PROXY environment variable:

```
[Service]    
Environment="HTTPS_PROXY=https://proxy.example.com:443/" "NO_PROXY=localhost,127.0.0.1,docker-registry.example.com,.corp"
```

Flush changes: 
```
>sudo systemctl daemon-reload
```

Restart Docker: 
```
>sudo systemctl restart docker
```

Verify that the configuration has been loaded:
```
>systemctl show --property=Environment docker
Environment=HTTP_PROXY=http://proxy.example.com:80/
```

Or, if you are behind an HTTPS proxy server:

```
>systemctl show --property=Environment docker
Environment=HTTPS_PROXY=https://proxy.example.com:443/
```

You can now test again if your Docker installation is able to run the test image:
```
>docker run hello-world
```

## Configure proxy for the Docker client

Proxy configuration has also to be set for the Docker client by creating or editing an existing ~/.docker/config.json file.

Its content is given in the template below:

```
{
   "proxies": {
     "default": {
       "httpProxy": "http://proxy.url:port",
       "httpsProxy": "http://proxy.url:port",
       "noProxy": "localhost,127.0.0.1,[Complete_with_your_own_proxy_configuration]"
     }
   }
}
```

It avoids giving those parameters through the command line to the Docker client like in the example below:
```
docker build --build-arg http_proxy="http://proxy.url:port" --build-arg https_proxy="http://proxy.url:port" -build-arg no_proxy="localhost,127.0.0.1" -t [IMAGE_NAME] .
```


## Installing docker compose

To get the latest Docker compose version, get the command from [this page](https://docs.docker.com/compose/install/) or use the one below for the 1.26.0 version:

```
>sudo curl -L "https://github.com/docker/compose/releases/download/1.26.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
```

If your proxy is not configured in `curl`, you can (temporary solution) give its parameters to curl use the following command (_added curl parameter: -x proxy.url:port_):
```
>sudo curl -x proxy.url:port -L "https://github.com/docker/compose/releases/download/1.26.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
```

Add execution permission:
```
>sudo chmod +x /usr/local/bin/docker-compose
```

Check installation works:
```
>docker-compose --version
docker-compose version 1.26.0, build d4451659
```


## Starting Docker

__Remark:__ `systemd` is used and prefered to `service` in order to manage Docker in all the JSatOrb documentation.

Check that the docker daemon is started:
```
>sudo systemctl status docker
```

If needed, start the docker daemon with systemctl:
```
>sudo systemctl start docker
```


## Generic commands

Build an image and give it a name
```
>docker build -t [IMAGE_NAME] .
```

Run a Docker image (in detached mode), with optional port mapping
```
>docker run -d [-p HOST_PORT:CONTAINER_PORT] [IMAGE_NAME]
```


## Installation logs

The __logs__ folder of the current project contains logs of a successfull Docker installation.
It can be used as a reference in case a problem appears during your installation process.


## Scripts

The __scripts__ folder of the current project contains a utility script which shows Docker image dependencies (see comments in script for details).


## Usefull links

[Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
[Configure proxy for the Docker Daemon](https://docs.docker.com/config/daemon/systemd/#httphttps-proxy)
[Linux post-installation steps](https://docs.docker.com/engine/install/linux-postinstall/)
[Install Docker compose](https://docs.docker.com/compose/install/)
