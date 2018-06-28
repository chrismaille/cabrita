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

To customize cabrita you can create a special file, called `cabrita.yml`
to create or config _boxes_. You can select which docker containers will
show in each box and what info these boxes will show for each service
inside them.

For example, copy and paste this yaml and save the `cabrita.yml` in the
same directory where your `docker-compose.yml` is located:

```yaml
version: 2
title: My Docker Project
background_color: grey # options: black, blue, cyan, grey, yellow, white
compose_files:
  - ./docker-compose.yml
boxes:
  main_box:
    main: true
    name: My Services
```

This file will create a dashboard called *My Docker Project*, which will
read all services from the `docker-compose.yml` file and add them to the
box called *My Services*.

This is the main box (`main: true`), which means all docker services
which are not included in any other box, will be added here.

To use this file, use the `--path` option for cabrita command line. You
can also define the `CABRITA_PATH` environment variable for this path.

Using the our docker-compose in `/examples` folder:

```bash
# You can call directy the app passing the yaml path
$ cd path/to/examples
$ TEST_PROJECT_PATH=$(pwd) docker-compose up -d
$ cabrita --path cabrita.yml

# Or you can use the CABRITA_PATH environment variable
$ export CABRITA_PATH=/path/to/yml
$ cabrita
```

The new dashboard will show: ![Image](source/assets/c1.png)

#### Customize Ports

You can define, for each box, if the docker ports will be show in
dashboard. Let's add two new options: `port_view` and `port_detail` on
`cabrita.yml`:

```yaml
version: 2
title: My Docker Project
background_color: grey # options: black, blue, cyan, grey, yellow, white
compose_files:
  - ./docker-compose.yml
boxes:
  main_box:
    main: true
    name: My Services
    port_view: status # options: column, name, status
    port_detail: internal # options: internal, external or both
```

The dashboard will show: ![Image](source/assets/c1.png)

#### Customize Git info

For more git information, let's add two new options: `show_revision` and
`target_branch`:

```yaml
version: 2
title: My Docker Project
background_color: grey # options: black, blue, cyan, grey, yellow, white
compose_files:
  - ./docker-compose.yml
boxes:
  main_box:
    main: true
    name: My Services
    port_view: status # options: column, name, status
    port_detail: internal # options: internal, external or both
    show_revision: true # will show commit hash and git tag if available
    watch_branch: origin/staging # check how ahead or behind you are regard this branch
```

The "**Branch**" column are displayed in each box, by default (you can
disable it with the `show_git: false` option). This column shows the
actual branch name for each service in box. If the branch is dirty (i.e.
has non-committed modifications), text color will be yellow.

The `show_revision` option show, for each service in box, the commit
hash and git tag, if available.

The `watch_branch` will add on "Branch" column how many commits ahead or
behind the current branch are in comparison of the *watched* branch.

The dashboard will show: ![Image](source/assets/c1.png)

### Add new boxes

