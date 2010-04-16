#!/bin/bash -xe
#
# update this script with the required migration calls

python manage.py migrate account 0001 --fake
python manage.py migrate basic_profiles 0001 --fake
python manage.py migrate oshare 0001 --fake
python manage.py migrate photos 0001 --fake
python manage.py migrate tag_app 0001 --fake
python manage.py migrate tribes 0001 --fake
