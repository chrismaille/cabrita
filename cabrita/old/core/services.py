import requests
from buzio import console, formatStr
from dashing import dashing
from tabulate import tabulate


def get_check_services(dash):
    """Check Docker-Compose and Ngrok status.

    Returns
    -------
        obj: dashing.Text

    """
    table_headers = ['Service', 'Status']
    table_data = []
    # Check Ngrok
    if dash.check_ngrok:
        try:
            ret = requests.get(
                "http://127.0.0.1:4040/api/tunnels", timeout=1)
            if ret.status_code == 200:
                text = formatStr.success("OK",
                                         use_prefix=False)
            else:
                text = formatStr.error("ERROR",
                                       use_prefix=False)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except BaseException:
            text = formatStr.error("NOT RUNNING",
                                   use_prefix=False)
    table_data.append(['Ngrok', text])

    final_text = tabulate(
        table_data,
        table_headers
    )
    return dashing.Text(final_text, color=6, border_color=5, title="3rd Services Status")
