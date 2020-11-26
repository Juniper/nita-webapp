#!/bin/bash

set -e

INSTALLDIR=${INSTALLDIR:-"/usr/local/bin"}
BASH_COMPLETION=${BASH_COMPLETION:-"/etc/bash_completion.d"}

install -m 755 cli_runner $INSTALLDIR/cli_runner
install -m 644 bash_completion.d/cli_runner_completions $BASH_COMPLETION/cli_runner_completions
install -m 644 bash_completion.d/nita-cmd $BASH_COMPLETION/nita-cmd

install -m 755 scripts/* $INSTALLDIR
(cd $INSTALLDIR; ln -s cli_runner nita-cmd)

