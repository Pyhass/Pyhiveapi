import os
import re

from setuptools import find_packages, setup


def requirements_from_file(filename="requirements.txt"):
    with open(os.path.join(os.path.dirname(__file__), filename)) as r:
        reqs = r.read().strip().split("\n")
    # Return non emtpy lines and non comments
    return [r for r in reqs if re.match(r"^\w+", r)]


setup(
    name="pyhiveapi",
    version="0.3.4.2",
    description="A Python library to interface with the Hive API",
    long_description="A Python library to interface with the Hive API",
    url="https://github.com/Pyhive/pyhiveapi",
    package_data={"pyhiveapi.pyhiveapi": ["*.json"]},
    include_package_data=True,
    author="Rendili",
    author_email="rendili@outlook.com",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        # "Topic:: Software Development:: Libraries:: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    python_requires=">=3.6.*",
    keywords="Hive API Library",
    packages=find_packages(exclude=["contrib", "docs", "tests"]),
    entry_points={"console_scripts": ["hive=pyhiveapi.hive:Hive"]},
    install_requires=requirements_from_file(),
    extras_require={"dev": requirements_from_file("requirements_test.txt")},
)
