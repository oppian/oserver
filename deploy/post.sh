#!/bin/bash

DEPLOY_DIR=$1

## Post hook setup script

## postgresql
DB_USER=oppster
DB_NAME=oppster
DB_PASS=mented73

# drop db
sudo -u postgres dropdb $DB_NAME

# drop user if exists
sudo -u postgres dropuser $DB_USER

# create user (note: done this way instead of createuser as you can put a password in)
sudo -u postgres psql postgres <<EOF
CREATE ROLE $DB_USER PASSWORD '$DB_PASS' NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT LOGIN;
EOF

# create user
sudo -u postgres createdb -O $DB_USER $DB_NAME
