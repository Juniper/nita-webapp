#!/bin/bash

VERSION=${GITHUB_HEAD_REF:-${GITHUB_REF#refs/heads/}}
echo $VERSION > VERSION.txt
echo "running 'cat VERSION.txt'"
cat VERSION.txt