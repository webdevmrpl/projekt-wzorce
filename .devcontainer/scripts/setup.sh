#!/bin/sh

git config core.editor "code --wait" # Set VS Code as default editor for git (for rebasing)

cd /app/.devcontainer/scripts
./setup-virtualenv.sh
