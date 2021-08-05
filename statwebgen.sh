#!/usr/bin/env bash

echo "$@"
if [[ $1 == "build" ]]; then
    python3 /mnt/c/Users/jelle/Repositories/statwebgen/generator/generator.py build "${@:2}"
elif [[ $1 == "serve" ]]; then
    node /mnt/c/Users/jelle/Repositories/statwebgen/server/index.js serve "${@:2}"
else
    echo "?"
fi