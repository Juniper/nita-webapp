# NITA Web Application 22.8

Welcome to NITA 22.8.

Packages built from this branch will be nita-*-22.8-x where x is the packaging release.
This branch also contains patches from other branches or minor modifications as required to support the stability and usability of the release.
There are also some backwards compatibility packages here for ansible and robot that allow projects written for NITA 3.0.7 to work without having to make any changes.

Note that NITA 22.8 backward compatible with NITA 20.10 projects, provided the correct ansible and robot containers are installed.

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

## 22.8 New Features and Bug Fixes

* Loads of security advisories, please use this version to avoid security problems in 21.7.
* Upgraded Jenkins

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

* NITA no longer checks for a hosts file or insists on the existence of group_vars/ or host_vars/ directories
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

It consists of 4 running containers (running under docker compose) and 2 ephemeral containers that are run by the Jenkins container as required.
The only containers that bind to the host file system are jenkins and the ephemeral containers of robot and ansible.

The containers per package are:

1. NITA webapp
2. Jenkins server
3. MariaDB database
4. NGINX web server to enable HTTPS for the webapp
5. Ansible executable and libraries
6. Robot executable and libraries

Additionally there are two host utilities that can be installed:

1. yaml-to-excel
2. nita-cmd (installed on the host along with the nita-webapp)

NITA cmd provides a command line interface to do common operations required during project development in NITA and can be accessed by typing `nita-cmd help`. nita-cmd is based on bash.

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
git checkout 22.8
mkdir nginx/certificates
openssl req -batch -x509 -nodes -days 365 -newkey rsa:2048 -keyout nginx/certificates/nginx-certificate-key.key -out nginx/certificates/nginx-certificate.crt
docker network create nita-network
docker compose up -d
```

In order for NITA to work you also need to run jenkins:
```bash
# install openjdk to get "keytool"
apt-get install -y openjdk-11-jre-headless
git clone https://github.com/Juniper/nita-jenkins
cd nita-jenkins
git checkout 22.8
mkdir certificates
keytool -genkey -keyalg RSA -alias selfsigned -keystore certificates/jenkins_keystore.jks -keypass nita123 -storepass nita123 -keysize 4096 -dname "cn=jenkins, ou=, o=, l=, st=, c="
docker compose up -d
```

In order for many of the nita-cmd jenkins commands to work you need to perform the following steps using the `certificates/jenkins_keystore.jks` created in the previous step.

Firstly, create a certificate file that can be loaded into the jenkins container's cacerts:
```bash
keytool -importkeystore -srckeystore certificates/jenkins_keystore.jks -destkeystore jenkins.p12 -deststoretype PKCS12
openssl pkcs12 -in jenkins.p12 -nokeys -out certificates/jenkins.crt
```

Secondly install the jenkins crt into the cacerts and copy the required jarfile into place:
```bash
docker exec -it -u root nitajenkins_jenkins_1 keytool -import -keystore /opt/java/openjdk/lib/security/cacerts -file /certificates/jenkins.crt -storepass changeit -noprompt && curl http://jenkins:8080/jnlpJars/jenkins-cli.jar -o /var/jenkins_home/war/WEB-INF/jenkins-cli.jar
```
Note: Every time you `docker-compose down` the Jenkins container, you will need to rerun the second step show above to add the certificate to jenkins container cacerts as the changes will be lost.

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
git checkout 22.8
( cd cli_scripts && install -m 0755 * /usr/local/bin )
cd ..
git clone https://github.com/Juniper/nita-robot
cd nita-robot
git checkout 22.8
( cd cli_scripts && install -m 0755 * /usr/local/bin )
cd ..
exec bash
```

Edit `$HOME/.profile` and add the following lines, then restart your shell to pick up the changes:
```
export NITAWEBAPPDIR=$HOME/nita-webapp
export NITAJENKINSDIR=$HOME/nita-jenkins
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

Note: Verify that the group section of the permissions is writable as well. In some instances the linux permissions 755 are seen after this step and need to modified by ```sudo chmod 775 /var/nita_project```

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

### Docker socket

``/var/run/docker.sock``

In some instances (vagrant installs in particular) the docker socket is incorrectly allocated. The jenkins container expects GID 999. In order to work around this type the following command:

```bash
sudo chgrp 999 /var/run/docker.sock
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

### Web App refuses to load network network packages

If the web app refuses to load network packages (and just hangs) this may be caused by incorrect permissions or group membership on /var/nita_project. Please review installation instructions for more information.

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

## Using an external Jenkins server

By default, the Webapp assumes a local installation of nita-jenkins container using the hostname "jenkins". If this is not the case and you have a separate Jenkins server running on a remote machine you can configure the Webapp to properly redirect the user to the Jenkins UI.

You only need to set the environment variable ``JENKINS_URL`` with the address of the remote machine and the variable ``JENKINS_PORT`` with the port that Jenkins is listening on.

Example:
```
export JENKINS_URL=remoteserver.com
export JENKINS_PORT=8443
```

Alternatively you can configure the docker-compose.yaml file to resolve the hostname "jenkins" to the correct IP address by adding the ``extra_hosts`` field:

```
services:
  webapp:
    [...]
    extra_hosts:
      - "jenkins:Jenkins-IP"
```
### Docker considerations with an external Jenkins server

Docker on Linux uses an IPC socket for communication (``/var/run/docker.sock``). To execute Jenkins jobs back to the Nita setup TCP connections will need to be enabled in the docker setup on the Nita server. On Ubuntu this can be done by editing docker.service file located at ``/usr/lib/systemd/system/docker.service`` by adding ``-H tcp://Docker-IP`` to the ``ExecStart`` parameter while keeping the existing -H parameters:
```
ExecStart=/usr/bin/dockerd -H tcp://192.168.49.2 -H fd:// --containerd=/run/containerd/containerd.sock
```
### Nita considerations with an external Jenkins server

The examples included with nita-webapp assume a local installation of Jenkins. The shell commands configured in the ``project.yaml`` file and loaded as Jenkins jobs to build the network environments are written for local installation. In order for the Jenkins to execute the jobs properly, the shell commands will need to be modified for remote execution. For example, in the DC build example, the file https://github.com/Juniper/nita/blob/main/examples/evpn_vxlan_erb_dc/project.yaml contains the following line:
```
    configuration:
      shell_command: 'write_yaml_files.py; docker run -u root -v "/var/nita_project:/project:rw" -v "/var/nita_configs:/var/tmp/build:rw" --rm --name ansible juniper/nita-ansible:22.8-1 /bin/bash -c "cd ${WORKSPACE}; bash build.sh ${build_dir}"'
```
This would be modified for remote execution via TCP (as configured in the previous section) by adding ``-H tcp://docker-IP`` to the ``docker run`` command:
```
    configuration:
      shell_command: 'write_yaml_files.py; docker run -H tcp://docker-IP -u root -v "/var/nita_project:/project:rw" -v "/var/nita_configs:/var/tmp/build:rw" --rm --name ansible juniper/nita-ansible:22.8-1 /bin/bash -c "cd ${WORKSPACE}; bash build.sh ${build_dir}"'
```
### nita-jenkins on a separate docker network

It is also possible to run nita-jenkins on its own docker network on the same host. However, Docker blocks traffic between container networks by default using the firewall system of the host operating system (iptables in the case of Ubuntu). This can by modified by making configuration to the firewall system. The TCP modifications above do not need to be implemented because the communication is still within a single docker instance. Be aware that Docker documentation recommends setting a second interface in the container connected to the second network versus this method as this breaks the security model.

If your setup requires this configuration, you will need to perform the following steps (Ubuntu version):

1. Modify the docker-compose.yml file in the nita-jenkins root directory to use the second Docker network (must be created separately):

```
services:
  jenkins:
[...]
networks:
  new-network-name:
    external: true
```

2. Determin bridge IDs of the nita-network and the network where Jenkins will reside with the ``ip show link`` command or the ``route`` command.
3. Add rules to iptables as follows:

```
sudo iptables -I DOCKER-USER -i br-<nita-network> -o br-<second-network> -j ACCEPT
sudo iptables -I DOCKER-USER -i br-<second-network> -o br-<nita-network> -j ACCEPT
```

4. Finally, make the firewall persistent across reboots: ``iptables-save > /etc/iptables/rules.v4``



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
*	In recent versions of Ubuntu 20.04, there is an incompatiability with openjdk. It may be necessary to install a previous version using ``apt install openjdk-11-jre-headless=11.0.7+10-3ubuntu1`` or similar (you can find which versions are available with ``apt-cache policy openjdk-11-jre-headless``
