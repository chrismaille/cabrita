from buzio import console, formatStr
from dashing import dashing
from tabulate import tabulate
from cabrita.core.parser import Config
import os

DEFAULT_DICT = {
    'compose': {
        'old_services_count': None,
        'new_services_count': None
    }
}


def get_check_status(dash):

    # Check for status file
    config = Config()
    if not os.path.isdir(dash.status_file_path):
        os.makedirs(dash.status_file_path)
    status_path = os.path.join(dash.status_file_path, "status.yml")
    if config.check_file(status_path):
        data = config.get_file(status_path)
    else:
        data = DEFAULT_DICT

    table_headers = ['Check', 'Status']
    table_data = []

    # Check docker-compose.yml status
    ret = console.run(
        "cd {} && git fetch && git status -bs --porcelain".format(
            dash.path),
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
        new_count = len([
            service
            for service in dash.services
        ])
        if not data['compose']['old_services_count']:
            data['compose']['old_services_count'] = new_count
        data['compose']['new_services_count'] = new_count
        if data['compose']['old_services_count'] == new_count:
            text = formatStr.success(
                'OK',
                use_prefix=False)
        else:
            text = formatStr.error(
                'NEED BUILD',
                use_prefix=False)
    table_data.append(['docker-compose.yml', text])

    # Save status.yml
    config.save_file(status_path, data)

    final_text = tabulate(
        table_data,
        table_headers
    )
    return dashing.Text(final_text, color=6, border_color=5,
                        title="Project Status")
