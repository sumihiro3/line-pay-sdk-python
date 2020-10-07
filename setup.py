from setuptools import setup, find_packages


def _requirements():
    with open("requirements.txt", "r") as fd:
        return [name.strip() for name in fd.readlines()]


with open("README.rst", "r") as fd:
    long_description = fd.read()

setup(
    name="line-pay",
    version="0.2.0",
    description="LINE Pay API SDK for Python",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    author="Sumihiro Kagawa",
    author_email="sumihiro@gmail.com",
    url="https://github.com/sumihiro3/line-pay-sdk-python",
    license="MIT",
    packages=find_packages(exclude=("tests", "docs", "requests", "examples")),
        install_requires=_requirements(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development"
    ],
    keywords=["LINE", "LINE Pay"]
)
