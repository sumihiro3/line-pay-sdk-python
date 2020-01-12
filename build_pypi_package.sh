#!/usr/bin/env bash
echo "build sdist & wheel"
python setup.py sdist
python setup.py bdist_wheel

echo "Check package"
twine check ./dist/*

echo "Build & Check package done."
echo "Upload command is twine upload dist/* --skip-existing"
