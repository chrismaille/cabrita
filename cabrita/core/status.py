from buzio import console, formatStr
from dashing import dashing
from tabulate import tabulate
from cabrita.core.parser import Config
from cabrita.core.utils import get_path
import os

DEFAULT_DICT = {
    'compose': {
        'old_services_count': None,
        'new_services_count': None
    }
}


def _check_git(path):
    if not os.path.isdir(os.path.join(path, ".git")):
        ret = "ok"
    else:
        ret = console.run(
            "cd {} && git fetch && git status -bs --porcelain".format(path),
            get_stdout=True
        )
    if not ret:
        text = formatStr.warning(
            "NOT FOUND",
            use_prefix=False)
    elif 'behind' in ret:
        text = formatStr.error(
            'NEED PULL',
            use_prefix=False)
    else:
        text = formatStr.success(
            'OK',
            use_prefix=False)
    return text


def _check_timestamp(datadict, base_path):
    dest_full_path = os.path.join(
        get_path(datadict['dest_path'], base_path), datadict['name'])
    source_name = datadict.get('source_name', datadict['name'])
    source_full_path = os.path.join(
        get_path(datadict['source_path'], base_path), source_name)

    if not os.path.isfile(
            dest_full_path) or not os.path.isfile(source_full_path):
        return formatStr.warning(
            'NOT FOUND',
            use_prefix=False
        )

    source_date = os.path.getmtime(source_full_path)
    dest_date = os.path.getmtime(dest_full_path)

    if source_date > dest_date:
        text = formatStr.error(
            'NEED UPDATE',
            use_prefix=False)
    else:
        text = formatStr.success(
            'OK',
            use_prefix=False)
    return text


def get_check_status(dash):

    # Check for status file
    config = Config()
    status_full_path = get_path(dash.status_file_path, dash.path)
    if not os.path.isdir(status_full_path):
        os.makedirs(status_full_path)
    status_path = os.path.join(status_full_path, "status.yml")
    if config.check_file(status_path):
        data = config.get_file(status_path)
    else:
        data = DEFAULT_DICT

    table_headers = ['File', 'Status']
    table_data = []

    # Check docker-compose.yml status
    text = _check_git(dash.path)
    table_data.append(['docker-compose.yml', text])

    # Files in config
    filedata = dash.config.get('files', [])
    for key in filedata:
        text = _check_git(filedata[key]['source_path'])
        if "ok" in text.lower():
            text = _check_git(filedata[key]['dest_path'])
            if "ok" in text.lower():
                text = _check_timestamp(filedata[key], dash.config['file_path'])
        table_data.append([filedata[key]['name'], text])

    # Save status.yml
    config.save_file(status_path, data)

    table_data.sort(key=lambda x: x[0])

    final_text = tabulate(
        table_data,
        table_headers
    )
    return dashing.Text(final_text, color=6, border_color=5,
                        title="Check Files")
