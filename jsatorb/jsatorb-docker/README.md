# JSatOrb project: Dockerisation module

This JSatOrb module is dedicated to the JSatOrb servers dockerisation.
It contains all the information needed to:
- install Docker and Docker compose, 
- produce the various Docker images and the Docker compose which runs them all.

All JSatOrb Docker images run in a Linux Ubuntu 18.04 LTS 64 bit environment, which is the JSatOrb target platform.

The Linux free edition of Docker is the Community Edition (CE).


## Docker Installation

All the information relative to the Docker engine and Docker compose installation in an Ubuntu 18.04 LTS 64 bit Linux version are gathered [in this file](./README-install.md).


## Preparing the JSatOrb Docker images

The JSatOrb Docker images preparation process presented below is assumed to be done in a JSatOrb development environment.  
Therefore, it assumes that all the JSatOrb git repositories are available in the `~/JSatOrb/repos/git` folder.  
It also assumes that the JSatOrb frontend and backend has been built at least once and successfully:
- The procedure to build the JSatOrb frontend can be found [in this documentation](../jsatorb-frontend/README.md).
The procedure to build the JSatOrb backend can be found [in this documentation](../jsatorb-rest-api/README.md).


### JSatOrb frontend image

Go into the JSatOrb frontend project folder:
```
>cd jsatorb-frontend
```

Build the JSatOrb image:
```
docker build -t jsatorb-frontend:prod .
```

Test it into a volatile container:
```
docker run -p 80:80 --rm jsatorb-frontend:prod
```

Connect to the JSatOrb GUI in a Web Browser (no connection port needed):
```
http://localhost
```

Stop the container by hitting Ctrl-C in the terminal you ran it from, or stop it smoothly in another terminal with:
```
docker stop <CONTAINER_ID>
```


### JSatOrb backend/REST API

The JSatOrb backend Docker image generation process needs two files external to the JSatOrb source code:
- __jsatorbenv.yml:__ contains a list of (almost) all the backend python dependencies. It is a file generated thanks to conda, but customized in purpose for reasons given in details below.
- __orekit-10.2-py37he1b5a44_0.tar.bz2:__ conda package containing the Orekit Python wrapper modified by by CS Group to add JSatOrb specific features and tagged v10.2 (snapshot).

___Remark:___ These two files are available in the __jsatorb-docker/backend__ folder.


#### Generating the conda environment file

The jsatorb-docker/backend folder already contains the final __jsatorbenv.yml__ file.
We still describe here how to re-generate it in the case this has to be done slightly differently in potential future JSatOrb releases.

1. Go into the JSatOrb root folder:
```
>cd repos/git
```

2. Activate the JSatOrb Python virtual environment
```
>conda activate JSatOrbEnv
```

3. Export the JSatOrb conda environment
```
>conda env export > jsatorbenv.yml
```

4. Edit the environment file

The following dependencies (the whole line of each) has to be removed from the environment file (explanations on why are below):

- __orekit=10.2=py37he1b5a44_0:__ because we have to install the modified Orekit python wrapper dependency locally instead of getting it from the Anaconda Web repository (channel conda-forge),
- __pyparsing=2.4.7=pyh9f0ad1d_0:__ because an issue appeared in March 2020 about the conda repository package storage format, we have to download and install manually some dependencies (see https://github.com/conda/conda/issues/9761).
- __bottle=0.12.17=py_0:__ For the same reason as the __pyparsing__ dependency, we also have to download and install manually this dependency and therefore have to remove it from the conda automatic download and installation process based on the environment file.

___Remark: Once the JSatOrb Orekit dependency has moved back to official releases, removing the Orekit dependency from the environment file is no more required. Beware that if doing so, the Dockerfile has to be updated accordingly to not install manually the Orekit dependency anymore.___


5. Update the reference file

If the environment file obtained is different from the reference one, don't forget to update and commit the new version.


#### Building the image

Copy the __Dockerfile__ and __.dockerignore__ files from __jsatorb-docker/backend__ folder into the JSatOrb git root folder.

From this git root folder, run the Docker build as follow:
```
>docker build -t jsatorb-backend:prod .
```

Test it in a detached (-d) volatile (--rm) container:
```
docker run -d -p 8000:8000 -v "/home/$USER/JSatOrb/mission-data:/root/JSatOrb/mission-data"  --rm jsatorb-backend:prod
```

___Note: The bind-mount parameters above are used to bind the current user's JSatOrb mission data set from the Docker host to the Docker backend container___


#### Testing the image

The __backend__ folder of the current project contains a __backend-test.bash__ script.
It can be used to test that the backend server is up and working.
See comments in the script for details.


#### Docker compose

Once the two images are built, you can stop all the containers used to test individual JSatOrb images and run the JSatOrb Docker compose as follow:
```
```


### JSatOrb Celestrak server image

#### Getting the image

The Celestrak server image is available on DockerHub.
This image can be downloaded with the following command:
```
>docker pull thib21/celestrak-json-proxy:dev
```

#### Running the image

This image can be run with the following command:
```
>docker run -d -p 7777:7777 --name celestrak-json-proxy-container thib21/celestrak-json-proxy
```


### Extracting the JSatOrb Docker images

In order to extract/save the JSatOrb Docker images, use the following command on each JSatOrb image:
```
>docker save [JSatOrb image name/ID:TAG] | gzip > ./docker_images/[jsatorb-image-exported-file.tgz]
```

Example:
```
>docker save jsatorb-frontend:prod | gzip > ./docker_images/jsatorb-frontend-docker-image.tgz
```

---

A script exists that does exactly this job for all the JSatOrb Docker images.
It can be found in the jsatorb-docker project. Its name is __jsatorb-save-docker-images.bash__.


**NOTE:**  

Extracting the JSatOrb Docker images is needed when building the JSatOrb user installation archive.  
___In this case, they have to be saved in the **jsatord-docker/docker_images** folder.___

The image names expected by the delivery preparation script are as follow:
- **backend:   jsatorb-backend-docker-image.tgz**
- **frontend:  jsatorb-frontend-docker-image.tgz**
- **celestrak: celestrak-json-proxy-docker-image.tgz**

---
