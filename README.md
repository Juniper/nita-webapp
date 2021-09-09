# NITA Web Application 21.7

Welcome to NITA 21.7.

Packages built from this branch will be nita-*-21.7-x where x is the packaging release.
This branch also contains patches from other branches or minor modifications as required to support the stability and usability of the release.
There are also some backwards compatibility packages here for ansible and robot that allow projects written for NITA 3.0.7 to work without having to make any changes.

Note that NITA 21.7 backward compatible with NITA 20.10 projects, provided the correct ansible and robot containers are installed.

# Copyright

Copyright 2021, Juniper Networks, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# Training

If you are planning on using NITA or any of the technologies related to NITA then please consider going on the Juniper JAUT and AJAUT courses.  These will give you the essential knowledge you need to do successful network automation!

https://learningportal.juniper.net/juniper/user_activity_info.aspx?id=10840

# Stable releases

The idea here is to provide multiple NITA based projects with a firm foundation that they can use to focus on solving customer problems rather than continually tweaking the underlying software.

It allows NITA projects to declare exactly which version of NITA they are compatible with.

Projects must explicitly use the versions of the containers provided by this package in order to avoid docker attempting to download from the registry.
No containers tagged as "latest" are provided by the package.

## Current Version

The release has been broken up into multiple packages, see the list bellow:

* Ubuntu 18.04
  * nita-jenkins-21.7-1
  * nita-webapp-21.7-1
  * nita-ansible-2.9.18-21.7-1
  * nita-robot-4.1-21.7-1
  * yaml-to-excel-21.7.0-1

* Centos 7
  * nita-jenkins-21.7-1
  * nita-webapp-21.7-1
  * nita-ansible-2.9.18-21.7-1
  * nita-robot-4.1-21.7-1
  * yaml-to-excel-21.7.0-1

## 21.7 New Features and Bug Fixes

* Loads of security advisories, please use this version to avoid security problems in 20.10.
* Upgraded django and openpyxl.
* Removed dependency on xlrd.
* Made it possible to configure the Jenkins password more easily.

## 20.10 New Features and Bug Fixes

* The NITA webapp is now much more forgiving about the format of project zip files.  The location of the project.yaml file now determines the root of the project and directory names or even a lack of a directory inside a zip file is irrelevant.
* Jenkins credentials can now be customized during the installation process by providing an environment variable to the docker container.
* Webapp credentials can now be customized during the installation process by providing an environment variable to the docker container.
* Fixed a bug in the NITA webapp where after a certain number of spreadsheet uploads the interface would become unusable.

## 20.7 New Features

* NITA no longer checks for a hosts file or insists on the existaence of group_vars/ or host_vars/ directories
* There is new version of the ansible container with Ansible 2.9.9 and support for pyez and Netbox libraries
* NITA 20.5-1 failed to delete Jenkins jobs when a Network was deleted, fixed in 20.5-2 and included in this release
* NITA now sets the build_dir variable for jenkins jobs in the "Test" category

## 20.5 New Features

* Jenkins is now supplied as an independent package
* The Webapp and its key components are now supplied as an addon package
* Removed Webapp operational scripts from the Jenkins container
* No dependencies between packages allowing custom installations
* Cli scripts now bundled in their respective packages

## 20.4 New Features

* Changed database to MariaDB, previously MySQL
*	Internal connection with Jenkins is now authenticated
*	Default connection to Webapp and Jenkins now set to HTTPS
*	Ansible and Robot containers are now separately packaged becoming optional addons
*	Ansible and Robot updated to support python3, previous version can still be installed to ensure backwards compatibility with older projects
*	Supported installation packages for Ubuntu 18.04 LTS and CentOS 7/8

# Architecture

It consists of 4 running containers (running under docker compose) and 2 ephemeral containers that are run as sidecars by the Jenkins container as required.
The only containers that bind to the host file system are jenkins and the ephemeral containers of robot and ansible.

The containers per package are:

1. NITA webapp
2. Jenkins server
3. MariaDB database
4. NGINX web server to enable HTTPS for the webapp
5. Ansible executable and libraries
6. Robot executable and libraries

Additionally there are two host utilities that can be installed:

1. nita-cli
2. yaml-to-excel
3. nita-cmd (installed on the host along with the nita-webapp)

NITA cli provides an command line interface to do common operations required during project development in NITA and can be accessed by typing `nita help`.  nita-cli is based on python.

NITA cmd provides an alternative command line interface to do common operations required during project development in NITA and can be accessed by typing `nita-cmd help`. nita-cmd is based on bash.

The utility for converting files from yaml to excel spreadsheet format and back again provided inside of the webapp container (yaml-to-excel) is also provided on the host.  It is possible to use the webapp to achieve the same effect as yaml-to-excel although that is less convenient.

# Installing

## Dependencies

NITA depends on docker-ce and docker-compose.

* For the **docker-ce** instalation the instructions found here: https://docs.docker.com/engine/install/
* It is recomended to follow this steps after installing docker-ce: https://docs.docker.com/engine/install/linux-postinstall/
* To install **docker-compose** follow the instructions found here: https://docs.docker.com/compose/install/
* (Optional) NITA-CLI requires **jq** for some of its features. For the instalation of this library refer to: https://stedolan.github.io/jq/download/

## Installation

If you do not have the the required package files for your system, .deb for Ubuntu or .rpm for Centos refer to [BUILD.md](./BUILD.md) file for instructions on how to generate these files.

### Docker compose
The easiest way to install the NITA webapp is to use docker compose, however currently the command line tools only work properly with the packages.  That hopefully will be resolved in future releases.

See https://github.com/Juniper/nita-webapp/blob/main/docker-compose.yaml for the docker compose file.

Once you have docker-ce and docker-compose installed do the following steps as **root**:

```bash
git clone https://github.com/Juniper/nita-webapp
cd nita-webapp
git checkout 21.7
mkdir nginx/certificates
openssl req -batch -x509 -nodes -days 365 -newkey rsa:2048 -keyout nginx/certificates/nginx-certificate-key.key -out nginx/certificates/nginx-certificate.crt
docker network create nita-network
docker-compose up -d
```

In order for NITA to work you also need to run jenkins:
```bash
# install openjdk to get "keytool"
apt-get install -y openjdk-11-jre-headless
git clone https://github.com/Juniper/nita-jenkins
cd nita-jenkins
git checkout 21.7
mkdir certificates
keytool -genkey -keyalg RSA -alias selfsigned -keystore certificates/jenkins_keystore.jks -keypass nita123 -storepass nita123 -keysize 4096 -dname "cn=, ou=, o=, l=, st=, c="
docker-compose up -d
```

In order to get nita-cmd scripts working on a docker-compose based installation (do this in the same directory where you cloned jenkins and the webapp):
```bash
# become root but stay in the installation directory
sudo bash
cd nita-webapp
( cd nita-cmd && bash install.sh )
( cd cli_scripts && install -m 0755 * /usr/local/bin )
cd ..
cd nita-jenkins
( cd cli_scripts && install -m 0755 * /usr/local/bin )
cd ..
git clone https://github.com/Juniper/nita-ansible
cd nita-ansible
git checkout 21.7
( cd cli_scripts && install -m 0755 * /usr/local/bin )
cd ..
git clone https://github.com/Juniper/nita-robot
cd nita-robot
git checkout 21.7
( cd cli_scripts && install -m 0755 * /usr/local/bin )
cd ..
exec bash
```

Installing nita-yaml-to-excel without using the .rpm or .deb package:
```bash
git clone https://github.com/Juniper/nita-yaml-to-excel
pip3 install ./nita-yaml-to-excel
```

Finally you *must* set the group on the project directory to be 1000 (for jenkins inside the container):
```bash
chgrp 1000 /var/nita_project
```

### Ubuntu packages
If you have been provided with or built the .deb package files, then follow the instructions provided in the [Dependencies](##Dependencies) section above and then run the following command:

```bash
sudo apt-get install <path-to-deb-file>
```

Example:
```bash
sudo apt-get install ./nita-jenkins-21.7-1.deb ./nita-webapp-21.7-1.deb ./yaml-to-excel-21.7.0-1.deb
```

### Centos packages
If you have been provided with or built the .rpm package files, then follow the instructions provided in the [Dependencies](##Dependencies) section above and then run the following command:

```bash
sudo yum install <patch-to-rpm-file>
```

Example:
```bash
sudo yum install ./nita-jenkins-21.7-1.noarch.rpm ./nita-webapp-21.7-1.noarch.rpm ./yaml-to-excel-21.7.0-1.noarch.rpm
```

NOTE: make sure you disable SELinux during the instalation process. Refer to  [`Known Bugs and irritations`](#Known-Bugs-and-irritations) for more details.

## Vagrant

For users of vagrant, here is a handy "Vagrantfile" that will get you a working ubuntu 18.04 box quickly and forward the relevant ports:

```ruby
PORTS = {
  jenkins:  [ 8443, 8443 ],
  webapp:   [ 443, 443 ]
}

Vagrant.configure("2") do |config|
  config.vm.define :nita, primary: true, autostart: true do |nita|
    nita.vm.box = "ubuntu/bionic64"

    nita.vm.hostname = "nita"
    PORTS.map do |app,port|
      nita.vm.network :forwarded_port, guest: port[0], host: port[1]
    end

    nita.vm.provider :virtualbox do |vb|
      vb.name = "nita"
      vb.gui = false
      vb.memory = 4096
      vb.cpus = 2
      # comment out this line to enable console debug log
      vb.customize [ "modifyvm", :id, "--uartmode1", "disconnected" ]
    end
  end
end
```

## Troubleshooting

``/var/run/docker.sock``

The group owner of the docker socket is incorrectly allocated on vagrant boxes.  The reason for this is that vagrant allocates GID 999 for its own purposes and docker then allocates an alternative numeric GID (usually 998). The jenkins container expects GID 999. In order to work around this type the following command:

```bash
sudo chmod 0.999 /var/run/docker.sock
```

Additionally in order to avoid having to type this command every time you reboot add it to the ``/etc/rc.local`` startup script(this is a hacky workaround):

```bash
#!/bin/sh -e
#
# rc.local
#
# This script is executed at the end of each multiuser runlevel.
# Make sure that the script will "exit 0" on success or any other
# value on error.
#
# In order to enable or disable this script just change the execution
# bits.
#
# By default this script does nothing.

chown 0.999 /var/run/docker.sock

exit 0
```

``/etc/nita-webapp/docker-compose.yaml``
``/etc/nita-jenkins/docker-compose.yaml``

When using packaged versions of nita, these files control the containers started automatically and what ports they are accessible on. Only modify this if you understand what you are doing.

# User Interface

The "nita" package runs two web applications listening on two ports for https:
1. NITA webapp on port 443 (using NGINX)
2. Jenkins on port 8443

## Default User Credentials

The default user credentials for the NITA webapp and Jenkins are listed below:

| | Username | Password |
|---|---|---|
| Webapp| vagrant | vagrant123 |
| Jenkins | admin | admin|

## Set Custom Credentials

The process to set a custom set of credentials for the webapp and the jenkins interfaces is the same regardless of the instalation type used, packaged version or docker-compose deployment.

To use a set custom credentials set the apropriate enviromental variables **before** installing a package or deploying via docker-compose.

Recognized Environment Variables:
  - WEBAPP_USER
  - WEBAPP_PASS
  - JENKINS_USER
  - JENKINS_PASS

Example: ``export WEBAPP_USER='CustomUser'``

For any unset variable NITA will use the default credentials.

To change the credentials of a running instance reset the relevant enviromental variables and then reload all both webapp and jenkins deployments.

## Set Jenkins URL

By default the Webapp assumes a local installation. If this is not the case and you have Nita running on a remote machine you can configure the Webapp to properly riderect the user to the Jenkins UI.

You only need to set the environment variable ``JENKINS_URL`` with the address of the remote machine and the variable ``JENKINS_PORT`` with the port that Jenkins is listening on.

Example:
```
export JENKINS_URL=remoteserver.com
export JENKINS_PORT=8443
```

## Command Line Interface

If you installed NITA using one of the webapp packages then "nita-cmd" command is installed, it is possible to run the following commands:

* ``nita-cmd webapp up`` -- reloads the containers from ``/usr/share/nita-webapp/images`` and starts the docker service
* ``nita-cmd webapp down`` -- stops the docker service and removes the container images
* ``nita-cmd webapp status`` -- gives the status of the containers
* ``nita-cmd webapp logs`` -- tails the log of the webapp container

For more commands run ``nita-cmd help``.

For more information on Jenkins refer to https://github.com/Juniper/nita-jenkins/

# Known Bugs and Irritations

* When installing the packages with root on a debian based system this warning may surface ``N: Download is performed unsandboxed as root as file '/root/nita-webapp-20.7-1.deb' couldn't be accessed by user '_apt'. - pkgAcquire::Run (13: Permission denied)`` and can be ignored.
* When removing the webapp the process may leave webapp specific jobs still installed on the runnning Jenkins instance, use ``nita jenkins jobs delete`` to remove them.
* On reinstalling the nita-jenkins it is necessary to reload the webapp instance to guarantee that the correct jobs are installed, simply run ``nita-cmd webapp restart`` after nita-jenkins reinstallation.
* On CentOS systems if SELinux is enabled it is necessary to manually start the services after the installation, this can be avoided by disabling SELinux during the installation (with ``setenforce 0`` beforehand and ``setenforce 1`` afterwards).
*	No method to automatically change SSL certificates for the Webapp and Jenkins (can be done manually).
*	No method to reset Jenkins access password (can be done manually).
* The command line (cli) tools don't fully support installations based on the docker-compose file only, only packaged versions are supported.  Use the docker-compose version for development and testing.
