#!/bin/bash

# -----------------------------------------------------------------------------
# Script to get Docker children images of a given image id as parameter.
# Usage: docker-children.bash <Image_id>
# -----------------------------------------------------------------------------
# SOURCE: 
# https://stackoverflow.com/questions/36584122/how-to-get-the-list-of-dependent-child-images-in-docker
# -----------------------------------------------------------------------------


parent_short_id=$1
parent_id=`docker inspect --format '{{.Id}}' $1`

get_kids() {
    local parent_id=$1
    docker inspect --format='ID {{.Id}} PAR {{.Parent}}' $(docker images -a -q) | grep "PAR ${parent_id}" | sed -E "s/ID ([^ ]*) PAR ([^ ]*)/\1/g"
}

print_kids() {
    local parent_id=$1
    local prefix=$2
    local tags=`docker inspect --format='{{.RepoTags}}' ${parent_id}`
    echo "${prefix}${parent_id} ${tags}"

    local children=`get_kids "${parent_id}"`

    for c in $children;
    do
        print_kids "$c" "$prefix  "
    done
}

print_kids "$parent_id" ""