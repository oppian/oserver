'''deploy server.

Usage: deploy.py --type=[prod|dev] /deploy/directory

ENV:
 * BUILD_TYPE [dev|prod]
 * DB_USER
 * DB_PASS
 * DB_NAME
 * DB_SETUP
 * SITE_DOMAIN
 * DEBUG
 * APACHE_USER
 * APACHE_CONF
 * FIXTURE_FILE (optional)
'''

DJANGO_VERSION = "1.2.dev12229"

from string import Template
import getopt
import os
import subprocess
import sys
import pwd
import shutil

def _getenv(name):
    try:
        var = os.environ[name]
        return var
    except:
        raise Usage("Error: environment variable '%s' not set" % name)

def _template(source, dest, mapping=os.environ):
    """
    Takes source file and writes it to dest using mapping.
    """
    # read the template into a string
    source_file = open(source)
    contents = source_file.read()
    source_file.close()
    # substitute the variables
    template = Template(contents)
    result = template.substitute(mapping)
    # write the template to settings_local.py
    dest_file = open(dest, 'w')
    dest_file.write(result)
    dest_file.close()

def do_database():
    """
    If type is dev then it wipes the database.
    Env vars used:
     * DB_USER
     * DB_PASS
     * DB_NAME
    """
    
    BUILD_TYPE = _getenv('BUILD_TYPE')
    DB_USER = _getenv('DB_USER')
    DB_PASS = _getenv('DB_PASS')
    DB_NAME = _getenv('DB_NAME')
    DB_SETUP = eval(_getenv('DB_SETUP'))

    # dev only resets db 
    if DB_SETUP:
        print "Setting up the database"
        # drop db: sudo -u postgres dropdb $DB_NAME
        subprocess.call(['sudo', '-u', 'postgres', 'dropdb', DB_NAME], stderr=open('/dev/null', 'w'))

        # drop db user: sudo -u postgres dropuser $DB_USER
        subprocess.call(['sudo', '-u', 'postgres', 'dropuser', DB_USER], stderr=open('/dev/null', 'w'))

        # create user: sudo -u postgres psql postgres
        p = subprocess.Popen(['sudo', '-u', 'postgres', 'psql'], stdin=subprocess.PIPE)
        p.stdin.write("CREATE ROLE %s PASSWORD '%s' NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT LOGIN;\n" % (DB_USER, DB_PASS))
        p.stdin.close()
        p.wait()

        # create db: sudo -u postgres createdb -O $DB_USER $DB_NAME
        subprocess.call(['sudo', '-u', 'postgres', 'createdb', '-O', DB_USER, DB_NAME])

def do_settingsfile(deploy_dir):
    """
    Writes the setting file from a template.
    """
    print "Writing out settings file"
    _template(
              os.path.join(deploy_dir, 'settings_template.py'),
              os.path.join(deploy_dir, 'settings_local.py'),
              )
    
def do_virtualenv(deploy_dir):
    """
    Set up the virtual environment.
    """
    print "Setting up virtual environment"
    # python lib/pinax/scripts/pinax-boot.py --development --source=lib/pinax pinax-env  --django-version=$DJANGO_VERSION
    subprocess.call(['python', 'lib/pinax/scripts/pinax-boot.py', '--development', '--source=lib/pinax', '--django-version=%s' % DJANGO_VERSION, 'pinax-env'])
    # activate it
    activate_this = os.path.join(deploy_dir, "pinax-env/bin/activate_this.py")
    execfile(activate_this, dict(__file__=activate_this))
    os.environ['PATH'] = '%s:%s' % (os.path.join(deploy_dir, 'pinax-env/bin'), _getenv('PATH'))
    # install requirements: pip install --no-deps --requirement requirements.txt
    subprocess.call(['pip', 'install', '--no-deps', '--requirement', 'requirements.txt'])
    
def do_django(deploy_dir):
    """
    This runs the various django commands to setup the media, database, etc
    """
    print "Running django commands"
    # media: python manage.py build_static --noinput
    subprocess.call(['python', 'manage.py', 'build_static', '--noinput',])
    # syncdb: python manage.py syncdb --noinput
    subprocess.call(['python', 'manage.py', 'syncdb', '--noinput',])
    # fixture
    try:
        subprocess.call(['python', 'manage.py', 'loaddata', _getenv('FIXTURE_FILE'),])
    except:
        # no fixture file
        pass
    # chown the deploy dir to be the apache user
    APACHE_USER = _getenv('APACHE_USER')
    os.chown(deploy_dir, pwd.getpwnam(APACHE_USER)[2], -1)

def do_cron(deploy_dir):
    """
    Setup the cron template
    """
    print "Creating cron file"
    cron_dir = os.path.join(deploy_dir, 'cron.d')
    if not os.path.isdir(cron_dir):
        os.mkdir(cron_dir)
    _template(
              os.path.join(deploy_dir, 'conf/cron.template'),
              os.path.join(cron_dir, 'chronograph'),
              )
    # link them
    for cronfile in os.listdir(cron_dir):
        cronfile = os.path.join(cron_dir, cronfile)
        # delete if exists
        try:
            os.unlink(os.path.join('/etc/cron.d/', os.path.basename(cronfile)))
        except:
            pass
        # link to cron.d dir
        os.symlink(cronfile, os.path.join('/etc/cron.d/', os.path.basename(cronfile)))
        # need to be owned by root
        os.chown(cronfile, pwd.getpwnam('root')[2], -1)
        # need to be exec
        os.chmod(cronfile, 0775)
    # make chonograph.sh executable
    os.chmod(os.path.join(deploy_dir, 'deploy/chronograph.sh'), 0775)
    
def do_apache(deploy_dir):
    """
    Setups apache
    """
    print "Setting up Apache"
    # enable required mods
    print "Enabling mod_rewrite"
    subprocess.call(['a2enmod', 'rewrite'])
    # rewrite config
    print "Writing out http.conf"
    _template(
              os.path.join(deploy_dir, 'conf/http.conf.template'),
              os.path.join(deploy_dir, 'conf/http.conf'),
              )
    
    print "Saving existing conf"
    apache_conf = os.path.join('/etc/apache2/sites-available', _getenv('APACHE_CONF'))
    try:
        shutil.copyfile(apache_conf, os.path.join('/tmp', _getenv('APACHE_CONF')))
    except:
        # config doesn't exists
        pass
    
    # link to apache conf
    print "Linking to APACHE_CONF"
    try:
        # delete existing
        os.unlink(apache_conf)
    except:
        # doesn't exist
        pass
    # create the symlink
    os.symlink(os.path.join(deploy_dir, 'conf/http.conf'), apache_conf)
    
    # enable if needed
    subprocess.call(['a2ensite', _getenv('APACHE_CONF')])
    
    print "Testing Apache config"
    retcode = subprocess.call(['apache2ctl', 'configtest'])
    if retcode:
        print "Error in apache config"
        # copy back
        shutil.copyfile(os.path.join('/tmp', _getenv('APACHE_CONF')), apache_conf)
        raise Usage('Error in apache config')
    
    print "Restarting Apache"
    subprocess.call(['apache2ctl', 'restart'])
    
    

def debug_env():
    import sys
    print "debug env"
    print "PATH=%s" % _getenv('PATH')
    print "sys path:"
    for path in sys.path:
        print path

def process(deploy_dir):
    """
    Deploys the server to the directory.
    """
    # setup the database
    do_database()
    # setup the settings file
    do_settingsfile(deploy_dir)
    # setup virtualenv
    do_virtualenv(deploy_dir)
    # django/pinax setup
    do_django(deploy_dir)
    # cron file setup
    do_cron(deploy_dir)
    do_apache(deploy_dir)


## main template

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    if argv is None:
        argv = sys.argv
    # parse command line options
    try:
        try:
            opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
        except getopt.error, msg:
            raise Usage(msg)
        type = None
        # process options
        for o, a in opts:
            if o in ("-h", "--help"):
                print __doc__
                return 0
        # process arguments
#        for arg in args:
#            process(arg) # process() is defined elsewhere
        # no args
        # deploy dir is one dir up
        deploy_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        os.environ['DEPLOY_DIR'] = deploy_dir
        process(deploy_dir)
    except Usage, err:
        print >> sys.stderr, err.msg
        print >> sys.stderr, "for help use --help"
        return 2

if __name__ == "__main__":
    sys.exit(main())



