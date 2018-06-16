## Welcome to Cabrita's documentation!

Cabrita is a Terminal Dashboard for docker services. You can easily follow the status for your docker containers:

* Which services are running
* The ports used by each one
* The number of instances
* The git status for the source code inside them
* The container healthcheck status, if available

Usage is simple: just change directory where's `docker-compose.yml` is located and run:

```bash
$ cd /path/to/docker/compose/file
$ cabrita
```

