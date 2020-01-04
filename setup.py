from setuptools import setup, find_packages

with open('README.rst', 'r') as fd:
    long_description = fd.read()

setup(
    name='line-pay',
    version='0.0.1',
    description='LINE Pay API SDK for Python',
    long_description=long_description,
    author='Sumihiro Kagawa',
    author_email='sumihiro@gmail.com',
    url='https://github.com/sumihiro3/line-pay-sdk-python',
    license=license,
    packages=find_packages(exclude=('tests', 'docs', 'requests')),
	install_requires=['requests'],
)
