#!/bin/bash -e

## Post hook setup script

# vars used
DB_USER=oppster
DB_NAME=oppster
DB_PASS=mented73
HOSTNAME=oppster.oppian.com

# deploy should be first argument
DEPLOY_DIR=$1
cd $DEPLOY_DIR

## postgresql

echo "Setting up database..."


# drop db
(sudo -u postgres dropdb $DB_NAME)

# drop dbuser if exists
(sudo -u postgres dropuser $DB_USER)

# create dbuser (note: done this way instead of createuser as you can put a password in)
sudo -u postgres psql postgres <<EOF
CREATE ROLE $DB_USER PASSWORD '$DB_PASS' NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT LOGIN;
EOF

# create db
sudo -u postgres createdb -O $DB_USER $DB_NAME

## settings file
cp -f settings_production.py settings_local.py


## setup virtualenv

DJANGO_VERSION=1.2.dev12229

# bootstrap virtualenv
echo "Setting up virtualenv..."
python lib/pinax/scripts/pinax-boot.py --development --source=lib/pinax pinax-env  --django-version=$DJANGO_VERSION

# activate it
source pinax-env/bin/activate

# install requirements
pip install --no-deps --requirement requirements.txt


## django/pinax setup

# media
echo "Gathering static media..."
python manage.py build_static --noinput

# syncdb
echo "Create database models..."
python manage.py syncdb --noinput


## cron setup
sed -e "s|@DEPLOY_DIR@|$DEPLOY_DIR|g" $DEPLOY_DIR/conf/cron.template > $DEPLOY_DIR/cron.d/chronograph
echo "Linking cron files..."
for CFILE in $DEPLOY_DIR/cron.d/* ; do
  echo "Linking $CFILE..."
  ln -s -f $CFILE /etc/cron.d/
done

# make chronograph.sh exec
chmod +x deploy/chronograph.sh


## chown of files to allow media and writing of pyc files
chown -R www-data $DEPLOY_DIR

## cron needs to be owned root
chown root deploy/chronograph.sh

## apache

## enable macro mod
a2enmod macro

## enable rewrite mod
a2enmod rewrite

# rewrite config
sed -e "s|@DEPLOY_DIR@|$DEPLOY_DIR|g" -e "s|@HOSTNAME@|$HOSTNAME|g" $DEPLOY_DIR/conf/http.conf.template > $DEPLOY_DIR/conf/http.conf
sed -e "s|@DEPLOY_DIR@|$DEPLOY_DIR|g" -e "s|@HOSTNAME@|$HOSTNAME|g" $DEPLOY_DIR/deploy/modpython.py.template > $DEPLOY_DIR/deploy/modpython.py


echo "Linking to apache config..."
ln -s -f $DEPLOY_DIR/conf/http.conf /etc/apache2/sites-available/oserver
a2ensite oserver

echo "Restarting apache..."
apache2ctl configtest
apache2ctl restart

