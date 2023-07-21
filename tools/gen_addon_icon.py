# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)
# Copyright (c) 2019 Eficent Business and IT Consulting Services S.L.
#        (http://www.eficent.com)

import os
import shutil
import click
import requests
import tempfile

from .gitutils import commit_if_needed
from .manifest import read_manifest, find_addons, NoManifestFound


ICONS_DIR = os.path.join("static", "description")

ICON_TYPE = "png"

ICON_TYPES = ["png", "svg"]


def gen_one_addon_icon(icon_dir, src_icon=None, filetype=ICON_TYPE):
    icon_filename = os.path.join(icon_dir, "icon.%s" % filetype)
    if not src_icon:
        src_icon = os.path.join(
            os.path.dirname(__file__).rpartition("tools")[0],
            "template",
            "module",
            ICONS_DIR,
            "icon.%s" % filetype,
        )
    if os.path.exists(src_icon):
        if not os.path.exists(icon_dir):
            os.makedirs(icon_dir)
        shutil.copyfile(src_icon, icon_filename)
        return icon_filename
    return None


def download_icon():
    url = "https://raw.githubusercontent.com/brain-tec/static/master/img/" \
          "braintec_app_icon.png"
    request = requests.get(url)
    request.raise_for_status()

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(request.content)
        src_icon = tmp.name
    return src_icon


@click.command()
@click.option(
    "--addon-dir",
    "addon_dirs",
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
    multiple=True,
    help="Directory where addon manifest is located. This option " "may be repeated.",
)
@click.option(
    "--addons-dir",
    type=click.Path(dir_okay=True, file_okay=False, exists=True),
    help="Directory containing several addons, the icon will be "
    "put for all installable addons found there.",
)
@click.option(
    "--src-icon",
    type=click.Path(dir_okay=False, file_okay=True, exists=True),
    help="Path to a custom icon.png file. If not set, it'll use the "
    "OCA template icon.",
)
@click.option("--commit/--no-commit", help="git commit icon, if not any.")
@click.option(
    "--add-bt-icon",
    is_flag=True,
    help="Download and add the braintec logo as app icon. "
         "If --add-bt-icon is set, it will override the --src-icon option.",
)
def gen_addon_icon(addon_dirs, addons_dir, src_icon, commit, add_bt_icon):
    """Put default OCA icon of type ICON_TYPE.

    Do nothing if the icon already exists in ICONS_DIR, otherwise put
    the default icon.
    """
    if add_bt_icon:
        src_icon = download_icon()

    addons = []
    if addons_dir:
        addons.extend(find_addons(addons_dir))
    for addon_dir in addon_dirs:
        addon_name = os.path.basename(os.path.abspath(addon_dir))
        try:
            manifest = read_manifest(addon_dir)
        except NoManifestFound:
            continue
        addons.append((addon_name, addon_dir, manifest))
    icon_filenames = []
    for addon_name, addon_dir, manifest in addons:
        if not manifest.get("preloadable", True):
            continue
        icon_dir = os.path.join(addon_dir, ICONS_DIR)
        exist = False
        for icon_type in ICON_TYPES:
            icon_filename = os.path.join(icon_dir, "icon.%s" % icon_type)
            if os.path.exists(icon_filename):
                # icon was created manually
                exist = True
                break
        if exist and not add_bt_icon:
            continue
        icon_filename = gen_one_addon_icon(icon_dir, src_icon=src_icon)
        if icon_filename:
            icon_filenames.append(icon_filename)
    if icon_filenames and commit:
        commit_if_needed(icon_filenames, "[ADD] icon.%s" % ICON_TYPE)


if __name__ == "__main__":
    gen_addon_icon()
