## Welcome to Cabrita's documentation!

Cabrita is a Terminal Dashboard for docker services. You can easily
follow the status for your docker containers:

* Which services are running
* The ports used by each one
* The number of instances
* The git status for the source code inside them
* The container healthcheck status, if available

### Usage

Usage is very simple: just change directory where's `docker-compose.yml`
is located and run:

```bash
$ cd /path/to/docker/compose/file
$ cabrita
```

[![asciicast](https://asciinema.org/a/Z31bttxgBe4JhuyBPvLYomoqc.png)](https://asciinema.org/a/Z31bttxgBe4JhuyBPvLYomoqc)

You can also pass the full path for the `docker-compose.yml` files on
command line:

```bash
$ cabrita /path/to/docker/compose/file1 /path/to/docker/compose/file2
```

### Customize

To customize cabrita you will need to create a special file, called
`cabrita.yml` to create or config _boxes_. You can select which docker
containers will show in each box and what info these boxes will show for
each them.

For example, copy and paste this yaml and save the
`cabrita.yml` in the same directory where your `docker-compose.yml` is
located:

```yaml
version: 2
title: My Docker Project
compose_files:
  - ./docker-compose.yml
  - ./docker-compose.override.yml
boxes:
  main_box:
    main: true
    name: My Services
    port_detail: both
```

We are setup one one box, with all services inside. This is the main box (`main: true`), and all cabrita.yml file must have on main box.
The box title is now "My Services" and ports column show now both internal and external ports.


