# Stealthy Cleaner
Service component of Stealthy application. Makes expired files
cleanup from backend database. Encapsulates service business logic
of Stealthy application:
 - provides service of automatic removing of sensitive data files
 - provides service of automatic removing of files metadata

### Technologies
Build with:
 - Python 3.11
 - Pymongo 4.6.1

### Requirements
Installed Docker and Docker-compose plugin

### How to up and run
#### Configure application
1. Copy file: 'config.yaml.example' to 'src/config.yaml'.
2. Make changes you need in configuration file.

#### Build docker images
Build docker images and start service
```bash
docker compose up
```

Stop and remove containers after application use
```bash
docker compose down
```
