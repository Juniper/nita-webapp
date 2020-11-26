# NITA CLI
<!-- 
[![build status](https://git.juniper.net/NITA/nita-cli/badges/master/build.svg)](https://git.juniper.net/NITA/nita-cli/commits/master) -->

NITA CLI project adds a command line interface to NITA. It is the way of interacting with NITA by using simple and intuitive commands. It focuses the user on getting a task done without having to learn the complex commands that run behind the scenes (related to docker, unix and some other tools). It is a move towards user-friendly, intuitive NetDevOps.

Juniper Networks focus is on `Engineering. Simplicity`. The NITA CLI is an example of this. It is creativity with an eye toward pragmatism. It is not just innovation, but innovation applied.

## Table of Contents

- [NITA CLI](#nita-cli)
    - [Goal](#goal)
    - [Reusability](#reusability)
    - [Autocompletion](#autocompletion)
    - [Usage](#usage)
    - [Suggestion](#suggestion)
    - [Prerequisites](#prerequisites)
        - [Basic](#basic)
        - [Autocomplete](#autocomplete)
    - [Installation](#installation)
    - [About NITA CLI](#about-nita-cli)
        - [`cli.py`](#clipy)
        - [`nita`](#nita)
        - [Documentation](#documentation)
    - [Customisation](#customisation)
    - [Continuos integration (CI)](#continuos-integration-ci)
    - [Troubleshooting](#troubleshooting)
    - [Demo](#demo)
    - [Contact](#contact)

## Goal

NITA CLI resolves the complexity of dealing with a lot of different technologies within the same framework by simplifying any command with its arguments, options, etc... into a single, customisable, intuitive and easy to remember command of your choice.

It is designed to help on:

- Support
- Operations/Engineering
- Development

so a lot of its commands come from the tasks carried out routinely on the following topics.

Imagine trying to type the following command to get jenkins container IPs:

    $ docker inspect --format='{{range .NetworkSettings.Networks}}   {{.IPAddress}}{{end}}' jenkins

    172.19.0.3   172.18.0.7

Is not easier and more intuitive to run the following command to get the same output? See below:

    $ nita jenkins ip

    172.19.0.3   172.18.0.7

Or this one to list all NITA containers:

    $ docker ps --filter "label=net.juniper.framework=NITA"

Compare it with this one in order to get the same output:

    $ nita containers ls
    CONTAINER ID        IMAGE                                      COMMAND                  CREATED             STATUS                       PORTS                                              NAMES
    5894c9c50d46        registry.juniper.net/nita/jenkins:latest   "/sbin/tini -- /usr/…"   About an hour ago   Up About an hour (healthy)   0.0.0.0:8443->8443/tcp, 0.0.0.0:50000->50000/tcp   jenkins
    5ed87b63500f        registry.juniper.net/nita/webapp:latest    "webapp-runner"          About an hour ago   Up About an hour             0.0.0.0:8090->8060/tcp                             webapp
    714107fad380        registry.juniper.net/nita/rsyslog:latest   "rsyslog-runner"         About an hour ago   Up About an hour             0.0.0.0:514->514/udp                               rsyslog
    effe8a4a7217        registry.juniper.net/nita/ntp:latest       "ntp-runner"             About an hour ago   Up About an hour             0.0.0.0:123->123/tcp                               ntp
    00e83ef33c4f        registry.juniper.net/nita/radius:latest    "radius-runner"          About an hour ago   Up About an hour             0.0.0.0:11812->1812/udp                            radius
    79ce0367ac8a        registry.juniper.net/nita/tacacs:latest    "tacacs-runner"          About an hour ago   Up About an hour             0.0.0.0:10049->49/tcp                              tacacs
    94c5e76fe470        registry.juniper.net/nita/dns:latest       "dns-runner"             About an hour ago   Up About an hour             0.0.0.0:53->53/udp                                 dns

## Reusability

These scripts are basically a wrapper to almost any command you could imagine. Not only that, it is also designed in a way that if any new commands are needed, it is so _easy_ to add them that anybody will be able to play with it and get it customised for their own purposes.

Furthermore, the way it is designed allows a user to reuse it in a different platforms. Let's say J-EDI for example. The only modification needed is to rename the `nita` script to `j-edi` and create a new list of scripts. After that, add `+x` permissions and move them to /usr/local/bin/ directory. 

That's all folks!!!

## Autocompletion

Another cool feature it has is `autocompletion`. So far, it has been tested in the following Operating Systems:

 - `Linux` (Ubuntu 16 LTS and Ubuntu 18 LTS) 

It makes use of the following links:

- https://debian-administration.org/article/316/An_introduction_to_bash_completion_part_1
- https://debian-administration.org/article/317/An_introduction_to_bash_completion_part_2

## Usage

### Help
NITA CLI comes with a bunch of pre-installed commands and a description of help features. Just by typing the root of your CLI command (e.g. `nita`) and ask for help, (e.g. `help`) it will list you all with a brief description of what each of them does.

NITA CLI help is context sensitive. So it matters where you use the help. You can get a list of all available commands at certain level of the commands tree, which would be a different set than from other part of the command tree. See below:

    $ nita jenkins help 

    nita jenkins cli jenkins => Attaches local standard input, output, and error streams to jenkins running container with "jenkins" user.
    nita jenkins cli root => Attaches local standard input, output, and error streams to jenkins running container with "root" user.
    nita jenkins ip => Returns IPs information on jenkins container.
    nita jenkins jobs export => Exports an existing job matched by --job <JOB> into XML format from Jenkins server.
    nita jenkins jobs import => Imports a job from XML config file by --file <FILE> (e.g. file.xml) into Jenkins server.
    nita jenkins jobs ls => Lists all Jenkins jobs.
    nita jenkins jobs remove => Removes Jenkins jobs matched by --regex <REGEX>. Assume "yes" as answer to all prompts and run non-interactively.
    nita jenkins labels => Returns labels information on jenkins container.
    nita jenkins logs => Fetches the logs of jenkins container.
    nita jenkins ports => Returns mapped ports information on jenkins container.
    nita jenkins volumes => Returns shared volumes information on jenkins container.

    $ nita rsyslog help 

    nita rsyslog cli => Attaches local standard input, output, and error streams to rsyslog running container.
    nita rsyslog ip => Returns IPs information on rsyslog container.
    nita rsyslog labels => Returns labels information on rsyslog container.
    nita rsyslog logs => Fetches the logs of rsyslog container.
    nita rsyslog ports => Returns mapped ports information on rsyslog container.
    nita rsyslog volumes => Returns shared volumes information on rsyslog container.

### Autocompletion

NITA CLI autocompletion is also context sensitive. Just by pressing `TAB` key twice at any level of the command tree, it will show you the different options you might have to autocomplete your command. For example:

    $ nita (TAB TAB)
    ansible     containers  demo        up      down ....
    ...

    $ nita tacacs (TAB TAB)
    cli      ip       labels   logs     ports    volumes

You should not worry about how it has been implemented, but as it is something integrated/reusable into any forked/branched repository, here it is a brief explanation.

The autocompletion script (`cli_runner_completions`) is then copied into the `/etc/bash_completion.d/` folder on the host server (See below where depending on OSs). 

_NOTE_: If you running NITA CLI from a container, this step needs to be done manually by the user!

In order to __load autocompletion__ it is needed to type following commmands into your shell (It is automatically done by the script, but if you want to test it in your terminal without the need to restart it (so changes take effect right after command execution!)):

- Linux

        $ . /etc/bash_completion.d/nita

- OS X (XXX - TODO)

        $ . $(brew --prefix)/etc/bash_completion.d/nita

- Windows (Cygwin) (XXX - TODO)

        . /etc/bash_completion.d/nita

How do you know it works? If you type complete command grepping by your script, it should appear as below.

    $ complete -p | grep nita
    complete -F bash_completion.d/_cli_runner_completions nita

Also, type `nita` and then `TAB` twice and it should give you some options to autocomplete. See below:

    $ nita (TAB TAB)
    ansible     containers  demo        up      down ....
    ...


## Prerequisites

### Basic
`jq` is a lightweight and flexible command-line JSON processor.

It is not really a prerequisite since NITA CLI runs without `jq`, but it really improves readability when using it! Here is the evidence:

It is not the same this:

    $ docker inspect --format '{{json .Mounts}}' webapp
    [{"Type":"bind","Source":"/Users/jizquierdo/Documents/Juniper/Projects/NITA/webapp_and_jenkins_shared","Destination":"/project","Mode":"rw","RW":true,"Propagation":"rprivate"}]

than this:

    $ docker inspect --format '{{json .Mounts}}' webapp | jq
    [
    {
    "Type": "bind",
    "Source": "/Users/jizquierdo/Documents/Juniper/Projects/NITA/webapp_and_jenkins_shared",
    "Destination": "/project",
    "Mode": "rw",
    "RW": true,
    "Propagation": "rprivate"
    }
    ]

It can be installed from:
- [github](https://stedolan.github.io/jq/)
- running `brew install jq` on OS X.
- running `apt-get install jq` on Linux.

### Autocomplete

Autocompletion provides \<TAB\> completion of command arguments. It provides users with the following functionalities:

- Saving them from typing text when it can be autocompleted.
- Letting them know available commands options.
- Preventing errors.
- Improving their experience by hiding/showing options based on user context.

If in `OS X`:

Install [brew](https://brew.sh/) to be able to install `bash-completion` package:

    brew install bash-completion

and before you run your first NITA CLI command, add the following tidbit to your `~/.bash_profile`:

    if [ -f $(brew --prefix)/etc/bash_completion ]; then
    . $(brew --prefix)/etc/bash_completion
    fi

If in `Windows` ([Cygwin](https://www.cygwin.com/)), install `bash-autocomplete` package as well. Edit your `~/.bashrc` file to turn on autocompletion as below:

    # Uncomment to turn on programmable completion enhancements.
    # Any completions you add in ~/.bash_completion are sourced last.
    [[ -f /etc/bash_completion ]] && . /etc/bash_completion

## Installation

### Ubuntu, OS X or Windows (Cygwin)

In order to install NITA CLI, use pip command and specifiy nita_cli repository with `sudo` (if needed).

`bash install.sh`

### Docker

To run NITA CLI as a Docker container simply pull it from the JNPR Docker registry, add the following [alias](alias) to your bash profile (`~/.profile`) and add the autocomplete part.

    docker pull ps-docker.artifactory.aslab.juniper.net/nita/cli:20.4

If you want to customise your commands, you can build your own docker image by the following command:

    docker build -t ps-docker.artifactory.aslab.juniper.net/nita/cli:${YOUR_TAG} .

### Demo

[TODO]

## About NITA CLI 

NITA cli is based on shell script call `cli_runner` and `cli_runner_completions`

### Documentation

See nita help 

## Customisation

Just create an executable program (can be a shell script) in the same directory as the `nita` command (which is asymlink to `cli_runner`).  Name the file `nita_COMMANDNAME` where COMMANDNAME is the thing you want to create.  More underscores mean more sub levels. If you want to add help text just add a trailing "help" to the file name (proceeded by an underscore. So `nita_test` would have a help script called `nita_test_help`.   Look in the existing scripts, there are plenty of examples.

### Known issues


