
INSPECT_DATA_FOR_DJANGO = [
    {
        "Id": "0ff14f3a0420db5fa445acfa2741a18be25bbf0b3b4c79e362165432039a67e5",
        "Created": "2018-05-15T15:59:59.316096671Z",
        "Path": "python",
        "Args": [
            "manage.py",
            "runserver",
            "-v1",
            "0.0.0.0:8080"
        ],
        "State": {
            "Status": "running",
            "Running": True,
            "Paused": False,
            "Restarting": False,
            "OOMKilled": False,
            "Dead": False,
            "Pid": 6993,
            "ExitCode": 0,
            "Error": "",
            "StartedAt": "2018-05-15T16:08:59.438525191Z",
            "FinishedAt": "2018-05-15T16:08:34.042025625Z"
        },
        "Image": "sha256:f17b832c2c7e7449d763b8a7e78d1c95ce34f19fe75701f1314733d404809d5b",
        "ResolvConfPath": "/var/lib/docker/containers/0ff14f3a0420db5fa445acfa2741a18be25bbf0b3b4c79e362165432039a67e5/resolv.conf",
        "HostnamePath": "/var/lib/docker/containers/0ff14f3a0420db5fa445acfa2741a18be25bbf0b3b4c79e362165432039a67e5/hostname",
        "HostsPath": "/var/lib/docker/containers/0ff14f3a0420db5fa445acfa2741a18be25bbf0b3b4c79e362165432039a67e5/hosts",
        "LogPath": "/var/lib/docker/containers/0ff14f3a0420db5fa445acfa2741a18be25bbf0b3b4c79e362165432039a67e5/0ff14f3a0420db5fa445acfa2741a18be25bbf0b3b4c79e362165432039a67e5-json.log",
        "Name": "/examples_django_1",
        "RestartCount": 0,
        "Driver": "overlay2",
        "Platform": "linux",
        "MountLabel": "",
        "ProcessLabel": "",
        "AppArmorProfile": "docker-default",
        "ExecIDs": None,
        "HostConfig": {
            "Binds": [
                "/home/chris/Documentos/Projetos/cabrita/examples/django_app:/opt/app:rw"
            ],
            "ContainerIDFile": "",
            "LogConfig": {
                "Type": "json-file",
                "Config": {}
            },
            "NetworkMode": "examples_backend",
            "PortBindings": {
                "8080/tcp": [
                    {
                        "HostIp": "",
                        "HostPort": "8081"
                    },
                    {
                        "HostIp": "",
                        "HostPort": "8090"
                    }
                ]
            },
            "RestartPolicy": {
                "Name": "",
                "MaximumRetryCount": 0
            },
            "AutoRemove": False,
            "VolumeDriver": "",
            "VolumesFrom": [],
            "CapAdd": None,
            "CapDrop": None,
            "Dns": None,
            "DnsOptions": None,
            "DnsSearch": None,
            "ExtraHosts": None,
            "GroupAdd": None,
            "IpcMode": "shareable",
            "Cgroup": "",
            "Links": None,
            "OomScoreAdj": 0,
            "PidMode": "",
            "Privileged": False,
            "PublishAllPorts": False,
            "ReadonlyRootfs": False,
            "SecurityOpt": None,
            "UTSMode": "",
            "UsernsMode": "",
            "ShmSize": 67108864,
            "Runtime": "runc",
            "ConsoleSize": [
                0,
                0
            ],
            "Isolation": "",
            "CpuShares": 0,
            "Memory": 0,
            "NanoCpus": 0,
            "CgroupParent": "",
            "BlkioWeight": 0,
            "BlkioWeightDevice": None,
            "BlkioDeviceReadBps": None,
            "BlkioDeviceWriteBps": None,
            "BlkioDeviceReadIOps": None,
            "BlkioDeviceWriteIOps": None,
            "CpuPeriod": 0,
            "CpuQuota": 0,
            "CpuRealtimePeriod": 0,
            "CpuRealtimeRuntime": 0,
            "CpusetCpus": "",
            "CpusetMems": "",
            "Devices": None,
            "DeviceCgroupRules": None,
            "DiskQuota": 0,
            "KernelMemory": 0,
            "MemoryReservation": 0,
            "MemorySwap": 0,
            "MemorySwappiness": None,
            "OomKillDisable": False,
            "PidsLimit": 0,
            "Ulimits": None,
            "CpuCount": 0,
            "CpuPercent": 0,
            "IOMaximumIOps": 0,
            "IOMaximumBandwidth": 0
        },
        "GraphDriver": {
            "Data": {
                "LowerDir": "/var/lib/docker/overlay2/8e51a55b173c566672f12349a2e20f599cd1813152fb7dc2a2a2ca35d05416e2-init/diff:/var/lib/docker/overlay2/99a0d23a626a975216a604e85464f163cd824b202cadf6c89d125a5c2ca1525e/diff:/var/lib/docker/overlay2/7c106daf42f3177723116a06824402e089f1d4e8c1c2451543fdb2405d1d1484/diff:/var/lib/docker/overlay2/171f0ed9b09d85e83abfc6409ddd5d14d639aef11a958929e00a4040b73aa59b/diff:/var/lib/docker/overlay2/9436f1c7defb36f290ec3b2c32f0314c3021c7e8422b9f31d2723bc00297f430/diff:/var/lib/docker/overlay2/553335ef683932e29237d21f705f9a043c08c8c6dc1173db13a40459a34be5b4/diff:/var/lib/docker/overlay2/c8feee33aaea9178ab6b8a9a876e44a55ab5987eec00d7106e0d4d187a7ec4c0/diff:/var/lib/docker/overlay2/04826330f9d326041314d83b2e3f9f6c408471eebb9b0d909126a34efa506fec/diff:/var/lib/docker/overlay2/937841fdfbd725a4af29c9f1f2914f8593d61ff78227e27229f393e072b0ac76/diff:/var/lib/docker/overlay2/720b7dfb3caea7934826d0f42f7a6c7e3bf613e8d8235c347341390957582296/diff:/var/lib/docker/overlay2/4bae8954169a656e918f9e5fee3a95d34319be17a1e23898a1babca7d30dbda4/diff:/var/lib/docker/overlay2/8e66cc15e07910a993bccd78519dd8630d33a3833eb4e8bc6df2ba689e38104d/diff",
                "MergedDir": "/var/lib/docker/overlay2/8e51a55b173c566672f12349a2e20f599cd1813152fb7dc2a2a2ca35d05416e2/merged",
                "UpperDir": "/var/lib/docker/overlay2/8e51a55b173c566672f12349a2e20f599cd1813152fb7dc2a2a2ca35d05416e2/diff",
                "WorkDir": "/var/lib/docker/overlay2/8e51a55b173c566672f12349a2e20f599cd1813152fb7dc2a2a2ca35d05416e2/work"
            },
            "Name": "overlay2"
        },
        "Mounts": [
            {
                "Type": "bind",
                "Source": "/home/chris/Documentos/Projetos/cabrita/examples/django_app",
                "Destination": "/opt/app",
                "Mode": "rw",
                "RW": True,
                "Propagation": "rprivate"
            }
        ],
        "Config": {
            "Hostname": "0ff14f3a0420",
            "Domainname": "",
            "User": "",
            "AttachStdin": False,
            "AttachStdout": False,
            "AttachStderr": False,
            "ExposedPorts": {
                "8080/tcp": {}
            },
            "Tty": False,
            "OpenStdin": False,
            "StdinOnce": False,
            "Env": [
                "DEBUG=True",
                "PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
                "LANG=C.UTF-8",
                "GPG_KEY=0D96DF4D4110E5C43FBFB17F2D347EA6AA65421D",
                "PYTHON_VERSION=3.6.5",
                "PYTHON_PIP_VERSION=10.0.1"
            ],
            "Cmd": [
                "python",
                "manage.py",
                "runserver",
                "-v1",
                "0.0.0.0:8080"
            ],
            "Image": "django:dev",
            "Volumes": {
                "/opt/app": {}
            },
            "WorkingDir": "/opt/app",
            "Entrypoint": None,
            "OnBuild": None,
            "Labels": {
                "com.docker.compose.config-hash": "1b4761a8a80dfd2753b955b15288dda009a332478400b1f30da634910272c49d",
                "com.docker.compose.container-number": "1",
                "com.docker.compose.oneoff": "False",
                "com.docker.compose.project": "examples",
                "com.docker.compose.service": "django",
                "com.docker.compose.version": "1.20.1"
            }
        },
        "NetworkSettings": {
            "Bridge": "",
            "SandboxID": "8d61df8a69ad6dab4c9f0478112fdbb1429c6165b6873293f471a820cd2b784d",
            "HairpinMode": False,
            "LinkLocalIPv6Address": "",
            "LinkLocalIPv6PrefixLen": 0,
            "Ports": {
                "8080/tcp": [
                    {
                        "HostIp": "0.0.0.0",
                        "HostPort": "8090"
                    },
                    {
                        "HostIp": "0.0.0.0",
                        "HostPort": "8081"
                    }
                ]
            },
            "SandboxKey": "/var/run/docker/netns/8d61df8a69ad",
            "SecondaryIPAddresses": None,
            "SecondaryIPv6Addresses": None,
            "EndpointID": "",
            "Gateway": "",
            "GlobalIPv6Address": "",
            "GlobalIPv6PrefixLen": 0,
            "IPAddress": "",
            "IPPrefixLen": 0,
            "IPv6Gateway": "",
            "MacAddress": "",
            "Networks": {
                "examples_backend": {
                    "IPAMConfig": None,
                    "Links": None,
                    "Aliases": [
                        "0ff14f3a0420",
                        "django"
                    ],
                    "NetworkID": "36cb799765946fe41b07dfbdb38de404c86b38d46e67858ca730ce1ff9a3c123",
                    "EndpointID": "1aea2bd87d82e1dde324822a6175a850b313b9ab537322a8b5907ddafcdcddd8",
                    "Gateway": "172.21.0.1",
                    "IPAddress": "172.21.0.6",
                    "IPPrefixLen": 16,
                    "IPv6Gateway": "",
                    "GlobalIPv6Address": "",
                    "GlobalIPv6PrefixLen": 0,
                    "MacAddress": "02:42:ac:15:00:06",
                    "DriverOpts": None
                }
            }
        }
    }
]

