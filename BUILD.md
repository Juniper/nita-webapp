For the building purpose of a **Package** or **Docker Image** it is recommended to first clone the repo:
```
git clone <repo_url>
```

# Package Build

## Debian/Ubuntu Package

To generate a .deb package file for the instalation of the NITA webapp on a Debian based system you can run the *build-nita-webapp-21.7-1.sh* script file found under the *packaging* folder:
```bash
cd packaging
./build-nita-webapp-21.7-1.sh
```

## Centos/RedHat Package
To generate a .rpm package file for the instalation of the NITA webapp on a Centos based system you can run the *build-webapp-21.7-1.sh* script file found under the *packaging_redhat* folder:
```bash
cd packaging_redhat
./build-webapp-21.7-1.sh
```

# Docker Image Build
To build the webapp docker image you can simply run the *build_container.sh* also found on the root folder of this repo:
```bash
./build_container.sh
```
## Installation requirements
If you're not using this aplication from a .deb/.rpm package installation please follow the next steps to ensure that you have a porper environment set up

### Generate selfsigned certificate for Nginx (https proxy)
```bash
mkdir -p nginx/certificates
openssl req -batch -x509 -nodes -days 365 -newkey rsa:2048 -keyout nginx/certificates/nginx-certificate-key.key -out nginx/certificates/nginx-certificate.crt
```

### Create NITA Docker Network
```bash
docker network create -d bridge nita-network
```

### Deploy NITA using Docker Compose
To launch this container you can use the supplied *docker_compose.yaml* file, simply run:
```bash
docker-compose -p nitawebapp up -d
```
