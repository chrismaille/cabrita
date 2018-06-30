## Welcome to Cabrita's documentation!

![PyPI](https://img.shields.io/pypi/v/cabrita.svg)
[![Build Status](https://travis-ci.org/chrismaille/cabrita.svg?branch=master)](https://travis-ci.org/chrismaille/cabrita)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/cabrita.svg)
[![Coverage Status](https://coveralls.io/repos/github/chrismaille/cabrita/badge.svg?branch=master)](https://coveralls.io/github/chrismaille/cabrita?branch=master)
[![Documentation Status](https://readthedocs.org/projects/cabrita/badge/?version=latest)](https://cabrita.readthedocs.io/en/latest/?badge=latest)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/ea94adacb6664984916474a909c4c4e4)](https://www.codacy.com/app/chrismaille/cabrita?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=chrismaille/cabrita&amp;utm_campaign=Badge_Grade)
[![Maintainability](https://api.codeclimate.com/v1/badges/3475b300e01e18d8c9e8/maintainability)](https://codeclimate.com/github/chrismaille/cabrita/maintainability)
[![Requirements Status](https://requires.io/github/chrismaille/cabrita/requirements.svg?branch=develop)](https://requires.io/github/chrismaille/cabrita/requirements/?branch=master)

Cabrita is a Terminal Dashboard for docker services. You can easily
follow the status for your docker containers:

* Which services are running
* The ports used by each one
* The number of instances
* The git status for the source code inside them
* The container healthcheck status, if available

### Index

- [Usage](#usage)
- [Customize](#customize)
- [More info](#more-info)

### Usage

Usage is very simple: just change directory where's your
`docker-compose.yml` is located and run:

```bash
$ cd /path/to/docker_compose/file
$ cabrita
```

[![asciicast](https://asciinema.org/a/Z31bttxgBe4JhuyBPvLYomoqc.png)](https://asciinema.org/a/Z31bttxgBe4JhuyBPvLYomoqc)

You can also pass the full path for the `docker-compose.yml` files on
command line:

```bash
$ cabrita /path/to/docker/compose/file1 /path/to/docker/compose/file2
```

### Customize Dashboard

To customize cabrita you can create a yaml file, to create and configure
_boxes_. You can select which docker containers will show in each box
and what info these boxes will show for each service inside them.

For example, copy and paste this yaml and save the `cabrita.yml` in the
same directory where your `docker-compose.yml` is located:

```yaml
version: 2
title: My Docker Project
background_color: grey # options: black, blue, cyan, grey, yellow, white
compose_files:
  - ./docker-compose.yml
  - ./docker-compose.override.yml
boxes:
  main_box:
    main: true
    name: My Services
    port_view: status # options: column, name, status
    port_detail: internal # options: internal, external or both
    show_revision: true # will show commit hash and git tag if available
    watch_branch: origin/staging # check how ahead or behind you are regard this branch
  django:
    name: Django Apps
    show_git: false
    includes:  # this box will show only services named in includes and categories options
      - django
    categories: # for each included service, add column for each category below
      - worker
      - redis
watchers:
  ping:  # ping watchers are using to ping informed address each n seconds.
    google:
      name: Check internet connectivity
      address: https://www.google.com
      message_on_success: UP
      message_on_error: DOWN
```

Let's use our docker project located in `/examples` folder. To start
cabrita with the new setup you can type:

```bash
# Start docker project services first
$ cd path/to/examples
$ TEST_PROJECT_PATH=$(pwd) docker-compose up -d

# Then, you can call directy the app passing the yaml path:
$ cabrita --path cabrita.yml

# Or you can use the CABRITA_PATH environment variable:
$ export CABRITA_PATH=/path/to/cabrita.yml
$ cabrita
```

The custom dashboard will show: ![Image](source/assets/c1.png)

### More Info

- For more advanced customization, please check the tutorial
- For the complete list of cabrita options, please check the Cabrita
  File Reference
