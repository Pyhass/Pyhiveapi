"""Setup pyhiveapi package."""

import os
import re

import unasync
from setuptools import setup


def requirements_from_file(filename="requirements_all.txt"):
    """Get requirements from file."""
    with open(os.path.join(os.path.dirname(__file__), filename), encoding="utf-8") as r:
        reqs = r.read().strip().split("\n")
    # Return non empty lines and non comments
    return [r for r in reqs if re.match(r"^\w+", r)]


setup(
    version="1.0.4",
    package_data={"data": ["*.json"]},
    include_package_data=True,
    cmdclass={
        "build_py": unasync.cmdclass_build_py(
            rules=[
                unasync.Rule(
                    "/src/apyhiveapi/",
                    "/pyhiveapi/",
                    additional_replacements={
                        "apyhiveapi": "pyhiveapi",
                        "asyncio": "threading",
                    },
                ),
                unasync.Rule(
                    "/src/apyhiveapi/api/",
                    "/pyhiveapi/api/",
                    additional_replacements={
                        "apyhiveapi": "pyhiveapi",
                    },
                ),
            ]
        )
    },
    install_requires=requirements_from_file(),
    extras_require={"dev": requirements_from_file("requirements_test_all.txt")},
)
