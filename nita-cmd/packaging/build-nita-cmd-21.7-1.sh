#!/bin/bash

# stop the script if a command fails
set -e

PACKAGE=nita-cmd
VERSION=21.7-1

# cleanup version if the directory name is used
VTMP="${VERSION#$PACKAGE-}"
VERSION=${VTMP%/}


if [ -z "$VERSION" ]; then
    echo "Must provide package version"
    exit 1
fi

if [ ! -d ${PACKAGE}-${VERSION} ]; then
    echo "Directory ${PACKAGE}-${VERSION} does not exist"
    exit 1
fi

rm -rf ${PACKAGE}-${VERSION}/usr
rm -rf ${PACKAGE}-${VERSION}/etc
mkdir -p ${PACKAGE}-${VERSION}/usr/local/bin
mkdir -p ${PACKAGE}-${VERSION}/etc/bash_completion.d

(
	cd ..
	INSTALLDIR=packaging/${PACKAGE}-${VERSION}/usr/local/bin \
	BASH_COMPLETION=packaging/${PACKAGE}-${VERSION}/etc/bash_completion.d \
		bash install.sh
)

dpkg-deb --build ${PACKAGE}-${VERSION}

