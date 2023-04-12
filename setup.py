import os
from setuptools import setup
import toml

PACKAGE_NAME = "contact-energy-nz"

with open("pyproject.toml", "r") as f:
    data = toml.load(f)

version = data["project"]["version"].split(".")



setup(
    name=PACKAGE_NAME,
    version=f'{version[0]}.{version[1]}.{os.environ["BUILD_NUMBER"]}',
)