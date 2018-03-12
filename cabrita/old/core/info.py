import psutil
from dashing import dashing


def get_info():
    """Get machine info using PSUtil.

    Returns
    -------
        obj: dashing.HSplit instance

    """
    cpu_percent = round(psutil.cpu_percent(interval=None) * 10, 0) / 10
    free_memory = int(psutil.virtual_memory().available / 1024 / 1024)
    total_memory = int(psutil.virtual_memory().total / 1024 / 1024)
    memory_percent = (free_memory / total_memory) * 100
    free_space = round(psutil.disk_usage("/").free / 1024 / 1024 / 1024, 1)
    total_space = round(psutil.disk_usage(
        "/").total / 1024 / 1024 / 1024, 1)
    space_percent = (free_space / total_space) * 100

    if memory_percent > 100:
        memory_percent = 100

    if space_percent > 100:
        space_percent = 100

    if cpu_percent <= 50:
        cpu_color = 2
    elif cpu_percent <= 70:
        cpu_color = 3
    else:
        cpu_color = 1

    if memory_percent <= 20:
        memory_color = 1
    elif memory_percent <= 50:
        memory_color = 3
    else:
        memory_color = 2

    if space_percent <= 20:
        space_color = 1
    elif space_percent <= 50:
        space_color = 3
    else:
        space_color = 2

    widget = dashing.HSplit(
        dashing.HGauge(
            val=cpu_percent,
            color=cpu_color,
            border_color=cpu_color,
            title="CPU:{}%".format(cpu_percent)
        ),
        dashing.HGauge(
            val=memory_percent,
            color=memory_color,
            border_color=memory_color,
            title="Free Mem:{}M".format(free_memory)
        ),
        dashing.HGauge(
            val=space_percent,
            color=space_color,
            border_color=space_color,
            title="Free Space:{}Gb".format(free_space)
        )
    )
    return widget
