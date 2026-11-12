#!/bin/sh
cd "$(dirname "$0")"
python3 admin.py || python admin.py
