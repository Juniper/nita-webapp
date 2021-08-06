#!/bin/bash

# stop the script if a command fails
set -e
set +x

PACKAGE=nita-cmd
VERSION=21.7
RELEASE=1

# cleanup version if the directory name is used
VTMP="${VERSION#$PACKAGE-}"
VERSION=${VTMP%/}


if [[ "x$VERSION" == "x" ]]; then
    echo "Must provide package version"
    exit 1
fi

if [ ! -d ${PACKAGE}-${VERSION}-${RELEASE} ]; then
    echo "Directory ${PACKAGE}-${VERSION}-${RELEASE} does not exist"
fi

export SOURCE_DIR=${PACKAGE}-${VERSION}-${RELEASE}/SOURCES

# clear the source dir
rm -rf ${SOURCE_DIR}/${PACKAGE}-${VERSION}*

# make the dest directories
mkdir -p ${SOURCE_DIR}/${PACKAGE}-${VERSION}/usr/local/bin
mkdir -p ${SOURCE_DIR}/${PACKAGE}-${VERSION}/etc/bash_completion.d

# install the scripts
(
    cd ..
    export INSTALLDIR=packaging_redhat/${SOURCE_DIR}/${PACKAGE}-${VERSION}/usr/local/bin
    export BASH_COMPLETION=packaging_redhat/${SOURCE_DIR}/${PACKAGE}-${VERSION}/etc/bash_completion.d
    bash install.sh
)

# Create a tarball of with source
(
    cd ${SOURCE_DIR}
    tar czf ${PACKAGE}-${VERSION}.tar.gz ${PACKAGE}-${VERSION}
)

# Build rpm file
export RPM_BUILD_DIR="${PWD}/${PACKAGE}-${VERSION}-${RELEASE}"
cp .rpmmacros ~
rpmbuild -ba ${PACKAGE}-${VERSION}-${RELEASE}/SPECS/${PACKAGE}.spec
