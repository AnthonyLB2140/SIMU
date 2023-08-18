# -----------------------------------------------------------------------------
# JSatOrb project: Dockerization of the JSatOrb backend/REST API server
# -----------------------------------------------------------------------------
# This Dockerfile builds the JSatOrb backend server.
# It depends on external files which have to be prepared.
# See jsatorb-docker/README.md documentation file for details.
# -----------------------------------------------------------------------------
# Open JDK 8
# Anaconda (conda) 4.5.12
# Python 3.7.6
# Significant Python dependencies:
#   - numpy 1.18.1
#   - matplotlib 3.2.1
#   - bottle    0.12.17
#   - jinja2    2.11.1
#   - orekit python wrapper v10.2 SNAPSHOT
# -----------------------------------------------------------------------------

# Use miniconda 3 v4.5.12 base image 
FROM continuumio/miniconda3:4.5.12

# -----------------------------------------------------------------------------
# Install JDK 8
# -----------------------------------------------------------------------------

# This is in accordance to : https://www.digitalocean.com/community/tutorials/how-to-install-java-with-apt-get-on-ubuntu-16-04
RUN apt-get update && \
        apt-get install -y openjdk-8-jdk && \
        apt-get install -y ant && \
        apt-get clean && \
        rm -rf /var/lib/apt/lists/* && \
        rm -rf /var/cache/oracle-jdk8-installer;

# Fix certificate issues, found as of # https://bugs.launchpad.net/ubuntu/+source/ca-certificates-java/+bug/983302
RUN apt-get update && \
        apt-get install -y ca-certificates-java && \
        apt-get clean && \
        update-ca-certificates -f && \
        rm -rf /var/lib/apt/lists/* && \
        rm -rf /var/cache/oracle-jdk8-installer;
# Setup JAVA_HOME, this is useful for docker commandline
ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64/RUN export JAVA_HOME

# Update the library path to give access to core Java libraries
ENV LD_LIBRARY_PATH /usr/lib/jvm/java-8-openjdk-amd64/jre/lib/amd64:/usr/lib/jvm/java-8-openjdk-amd64/jre/lib/amd64/server

# Create the REST API and the different backend parts folders.
RUN mkdir -p /app/jsatorb-visibility-service/src \
        &&  mkdir -p /app/jsatorb-eclipse-service/src \
        &&  mkdir -p /app/jsatorb-date-conversion/src \
        &&  mkdir -p /app/jsatorb-common/src \
        &&  mkdir -p /app/jsatorb-coverage-service/src \
        &&  mkdir -p /app/jsatorb-rest-api/src

# Set working dir
WORKDIR /app

# -----------------------------------------------------------------------------
# Install the Python environment
# -----------------------------------------------------------------------------

# Copy the altered JSatOrbEnv environment file in the container
COPY jsatorb-docker/backend/jsatorbenv.yml /tmp/jsatorbenv.yml

# Create the JSatOrb virtual environment
RUN conda create -n JSatOrbEnv python=3.7

# Add the environment activation into the user's bash script
RUN echo "source activate JSatOrbEnv" > ~/.bashrc

# Add the JSatOrb's Anaconda environment binary folder into the PATH
ENV PATH /opt/conda/envs/JSatOrbEnv/bin:$PATH
ENV CONDA_DEFAULT_ENV JSatOrbEnv

# -----------------------------------------------------------------------------
# Download and install manually the dependencies causing a FileNotFound error 
# (see https://github.com/conda/conda/issues/9761).
# -----------------------------------------------------------------------------
RUN curl -o /tmp/pyparsing-2.4.7-pyh9f0ad1d_0.tar.bz2 -L https://anaconda.org/conda-forge/pyparsing/2.4.7/download/noarch/pyparsing-2.4.7-pyh9f0ad1d_0.tar.bz2
RUN curl -o /tmp/bottle-0.12.17-py_0.tar.bz2 -L https://anaconda.org/conda-forge/bottle/0.12.17/download/noarch/bottle-0.12.17-py_0.tar.bz2

# -----------------------------------------------------------------------------
# [OREKIT_10.2_SNAPSHOT_ONLY] Activate the line below if the official Orekit 
# v10.2 is still not released yet.
COPY jsatorb-docker/backend/orekit-10.2-py37he1b5a44_0.tar.bz2 /tmp/orekit-10.2-py37he1b5a44_0.tar.bz2
# -----------------------------------------------------------------------------

# DEBUG STEP: can be removed
RUN ls -al /tmp

# Installing manually all downloaded bz2 packages
RUN /bin/bash -c "source activate JSatOrbEnv \
&& conda install -n JSatOrbEnv /tmp/*.bz2"

# DEBUG STEP: can be removed
RUN conda list

# Update the environment with the remaining dependencies
RUN conda env update --name JSatOrbEnv --file /tmp/jsatorbenv.yml

# -----------------------------------------------------------------------------
# Copy the different backend parts contents into the container.
# -----------------------------------------------------------------------------

# jsatorb-visibility-service
COPY jsatorb-visibility-service/src jsatorb-visibility-service/src
COPY jsatorb-rest-api/orekit-data.zip jsatorb-visibility-service
COPY jsatorb-visibility-service/templates jsatorb-visibility-service/templates

# jsatorb-eclipse-service
COPY jsatorb-eclipse-service/src jsatorb-eclipse-service/src
COPY jsatorb-rest-api/orekit-data.zip jsatorb-eclipse-service

# jsatorb-date-conversion
COPY jsatorb-date-conversion/src jsatorb-date-conversion/src
COPY jsatorb-rest-api/orekit-data.zip jsatorb-date-conversion

# jsatorb-common
COPY jsatorb-common/src jsatorb-common/src
COPY jsatorb-rest-api/orekit-data.zip jsatorb-common
COPY jsatorb-common/templates jsatorb-common/templates

# jsatorb-coverage-service
COPY jsatorb-coverage-service/src jsatorb-coverage-service/src
COPY jsatorb-rest-api/orekit-data.zip jsatorb-coverage-service

# JSatOrb's REST API
COPY jsatorb-rest-api/src jsatorb-rest-api/src
COPY jsatorb-rest-api/orekit-data.zip jsatorb-rest-api
COPY jsatorb-rest-api/files/Models jsatorb-rest-api/files/Models
COPY jsatorb-rest-api/templates jsatorb-rest-api/templates

# Update the files subfolders write permissions
RUN find /app -mindepth 1 -maxdepth 3 -name "files" -type d -exec chmod -R o+w {} \;

# -----------------------------------------------------------------------------
# Launch the application
# -----------------------------------------------------------------------------

# Set the working dir to the REST API root folder
WORKDIR /app/jsatorb-rest-api

# Expose the server project
EXPOSE 8000

# Start the JSatOrb REST API
# -u: unbufferized option enables to gain access to the server logs in Docker detached mode.
# see: https://stackoverflow.com/questions/29663459/python-app-does-not-print-anything-when-running-detached-in-docker
CMD [ "python", "-u", "src/JSatOrbREST.py" ]
