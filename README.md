[branch]: https://github.com/Juniper/nita/tree/tt888
[readme]: https://github.com/Juniper/nita/blob/tt888/README.md

# NITA Web Application tt888

Welcome to NITA, an open source platform for automating the building and testing of complex networks.

# Release Notes
The major change in this version is that all components now run within pods under the control of Kubernetes, rather than as Docker containers. Consequently we have updated the way that the webapp runs because it is now controlled by Kubernetes instead of Docker. 

Please refer to the [README][readme] for more details.

# Installing

The simplest way to install the nita-webapp is by installing nita, which can be done by running the ``install.sh`` script located and in the parent [nita repo][branch] as described [here][readme].

# User Interface

NITA exposes two web applications, listening on two different ports for https:
1. NITA webapp on port 443 (using NGINX)
2. Jenkins on port 8443

## Default User Credentials

The default user credentials for the NITA webapp and Jenkins are listed below:

| | Username | Password |
|---|---|---|
| Webapp| vagrant | vagrant123 |
| Jenkins | admin | admin|

## NITA Command Line Interface

A number of CLI scripts are installed with NITA which you can use to manage the Webapp:

```
user@host:$ nita-cmd webapp help
    nita-cmd webapp cli => Create an interactive session in the webapp container by executing a bash shell and using stdin as a tty.
    nita-cmd webapp db cli => Create an interactive session in the db pod by executing a bash shell.
    nita-cmd webapp up => Stops and removes the running NITA Webapp service, according to the configuration file in
    nita-cmd webapp ips => Returns IPs information on webapp container.
    nita-cmd webapp labels => Returns labels information on webapp container.
    nita-cmd webapp logs => Follows log output of webapp container.
    nita-cmd webapp db cli => Create an interactive session in the proxy pod by executing a bash shell.
    nita-cmd webapp restart => Restart the NITA Webapp with zero downtime by starting a new pod before terminating the old one.
    nita-cmd webapp start => Starts the NITA Webapp pod.
    nita-cmd webapp status => Shows the status of every NITA Webapp containers.
    nita-cmd webapp stop => Terminate the NITA Webapp pod.
    nita-cmd webapp up => Creates and starts NITA Webapp service according to the configuration file in
user@host:$
```

## Accessing the container

You can access the shell of the webapp container simply be running the following command:

```
user@host$ nita-cmd webapp cli
If you don't see a command prompt, try pressing enter.
root@webapp-748668765-m286j:/app# exit
exit
user@host$
```

# Copyright

Copyright 2024, Juniper Networks,Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# Training

If you are planning on using NITA or any of the technologies related to NITA then please consider going on the Juniper JAUT and AJAUT courses.  These will give you the essential knowledge you need to do successful network automation!

https://learningportal.juniper.net/juniper/user_activity_info.aspx?id=10840

# Previous releases

The idea here is to provide multiple NITA based projects with a firm foundation that they can use to focus on solving customer problems rather than continually tweaking the underlying software.

It allows NITA projects to declare exactly which version of NITA they are compatible with.

Projects must explicitly use the versions of the containers provided by this package in order to avoid docker attempting to download from the registry.
No containers tagged as "latest" are provided by the package.

## 22.8 New Features and Bug Fixes

* Loads of security advisories, please use this version to avoid security problems in 21.7.
* AI integration between Robot, Jenkins and ChatGPT
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

# Known Bugs and Irritations

* When installing the packages with root on a debian based system this warning may surface ``N: Download is performed unsandboxed as root as file '/root/nita-webapp-20.7-1.deb' couldn't be accessed by user '_apt'. - pkgAcquire::Run (13: Permission denied)`` and can be ignored.
* When removing the webapp the process may leave webapp specific jobs still installed on the runnning Jenkins instance, use ``nita jenkins jobs delete`` to remove them.
* On reinstalling the nita-jenkins it is necessary to reload the webapp instance to guarantee that the correct jobs are installed, simply run ``nita-cmd webapp restart`` after nita-jenkins reinstallation.
* On CentOS systems if SELinux is enabled it is necessary to manually start the services after the installation, this can be avoided by disabling SELinux during the installation (with ``setenforce 0`` beforehand and ``setenforce 1`` afterwards).
*	No method to automatically change SSL certificates for the Webapp and Jenkins (can be done manually).
*	No method to reset Jenkins access password (can be done manually).
*	In recent versions of Ubuntu 20.04, there is an incompatiability with openjdk. It may be necessary to install a previous version using ``apt install openjdk-11-jre-headless=11.0.7+10-3ubuntu1`` or similar (you can find which versions are available with ``apt-cache policy openjdk-11-jre-headless``
