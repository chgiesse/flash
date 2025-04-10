# tsx components don't have the `.propTypes` property set
# Generate it instead with the provided metadata.json
# for them to be able to report invalid prop

import os
import re


init_check_re = re.compile("proptypes.js")

missing_init_msg = """
{warning_box}
{title}
{warning_box}

Add the following to `{namespace}/__init__.py` to enable
runtime prop types validation with tsx components:

_js_dist.append(dict(
    dev_package_path="proptypes.js",
    namespace="{namespace}"
))

"""

prop_type_file_template = """// AUTOGENERATED FILE - DO NOT EDIT

var PropTypes = window.PropTypes;


{components_prop_types}
"""

component_prop_types_template = (
    "window['{package_name}'].{component_name}.propTypes = {prop_types}"
)


def generate_type(type_name):
    def wrap(*_):
        return f"PropTypes.{type_name}"

    return wrap


def generate_union(prop_info):
    types = [generate_prop_type(t) for t in prop_info["value"]]
    return f"PropTypes.oneOfType([{','.join(types)}])"


def generate_shape(prop_info):
    props = []
    for key, value in prop_info["value"].items():
        props.append(f"{key}:{generate_prop_type(value)}")
    inner = "{" + ",".join(props) + "}"
    return f"PropTypes.shape({inner})"


def generate_array_of(prop_info):
    inner_type = generate_prop_type(prop_info["value"])
    return f"PropTypes.arrayOf({inner_type})"


def generate_any(*_):
    return "PropTypes.any"


def generate_enum(prop_info):
    values = str([v["value"] for v in prop_info["value"]])
    return f"PropTypes.oneOf({values})"


def generate_object_of(prop_info):
    return f"PropTypes.objectOf({generate_prop_type(prop_info['value'])})"


def generate_tuple(*_):
    # PropTypes don't have a tuple... just generate an array.
    return "PropTypes.array"


prop_types = {
    "array": generate_type("array"),
    "arrayOf": generate_array_of,
    "object": generate_type("object"),
    "shape": generate_shape,
    "exact": generate_shape,
    "string": generate_type("string"),
    "bool": generate_type("bool"),
    "number": generate_type("number"),
    "node": generate_type("node"),
    "func": generate_any,
    "element": generate_type("element"),
    "union": generate_union,
    "any": generate_any,
    "custom": generate_any,
    "enum": generate_enum,
    "objectOf": generate_object_of,
    "tuple": generate_tuple,
}


def generate_prop_type(prop_info):
    return prop_types[prop_info["name"]](prop_info)


def check_init(namespace):
    path = os.path.join(namespace, "__init__.py")
    if os.path.exists(path):
        with open(path, encoding="utf-8", mode="r") as f:
            if not init_check_re.search(f.read()):
                title = f"! Missing proptypes.js in `{namespace}/__init__.py` !"
                print(
                    missing_init_msg.format(
                        namespace=namespace,
                        warning_box="!" * len(title),
                        title=title,
                    )
                )


def generate_prop_types(
    metadata,
    package_name,
):
    patched = []

    for component_path, data in metadata.items():
        filename = component_path.split("/")[-1]
        extension = filename.split("/")[-1].split(".")[-1]
        if extension != "tsx":
            continue

        component_name = filename.split(".")[0]

        props = []
        for prop_name, prop_data in data.get("props", {}).items():
            props.append(f"  {prop_name}:{generate_prop_type(prop_data['type'])}")

        patched.append(
            component_prop_types_template.format(
                package_name=package_name,
                component_name=component_name,
                prop_types="{" + ",\n".join(props) + "}",
            )
        )

    if patched:
        with open(
            os.path.join(package_name, "proptypes.js"), encoding="utf-8", mode="w"
        ) as f:
            f.write(
                prop_type_file_template.format(
                    components_prop_types="\n\n".join(patched)
                )
            )

        check_init(package_name)
