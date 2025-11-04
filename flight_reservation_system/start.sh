#!/bin/bash
python migrate_json_to_db.py
gunicorn app:app