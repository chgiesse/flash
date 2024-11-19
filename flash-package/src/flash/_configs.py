import os
import quart

# noinspection PyCompatibility
from dash import exceptions
from dash._utils import AttributeDict


def pages_folder_config(name, pages_folder, use_pages):
    if not pages_folder:
        return None
    is_custom_folder = str(pages_folder) != "pages"
    pages_folder_path = os.path.join(quart.helpers.get_root_path(name), pages_folder)
    if (use_pages or is_custom_folder) and not os.path.isdir(pages_folder_path):
        error_msg = f"""
        A folder called `{pages_folder}` does not exist. If a folder for pages is not
        required in your application, set `pages_folder=""`. For example:
        `app = Dash(__name__,  pages_folder="")`
        """
        raise exceptions.InvalidConfig(error_msg)
    return pages_folder_path
