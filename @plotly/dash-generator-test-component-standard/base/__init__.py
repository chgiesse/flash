import json
import os as _os

_basepath = _os.path.dirname(__file__)
_filepath = _os.path.abspath(_os.path.join(_basepath, "package.json"))
with open(_filepath) as f:
    package = json.load(f)

package_name = package["name"].replace(" ", "_").replace("-", "_")
__version__ = package["version"]

from ._imports_ import *  # noqa: F401, F403
from ._imports_ import __all__  # noqa: E402

_js_dist = [
    dict(
        relative_package_path="dash_generator_test_component_standard.js",
        namespace="dash_generator_test_component_standard",
    ),
    dict(
        relative_package_path="godfather.ttf",
        namespace="dash_generator_test_component_standard",
        dynamic=True,
    ),
]

_css_dist = [
    dict(
        relative_package_path="style.css",
        namespace="dash_generator_test_component_standard",
    )
]

for _component in __all__:
    setattr(locals()[_component], "_js_dist", _js_dist)
    setattr(locals()[_component], "_css_dist", _css_dist)
