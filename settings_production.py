
DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    "default": {
        "ENGINE": "postgresql_psycopg2", # Add "postgresql_psycopg2", "postgresql", "mysql", "sqlite3" or "oracle".
        "NAME": "oppster",                       # Or path to database file if using sqlite3.
        "USER": "oppster",                             # Not used with sqlite3.
        "PASSWORD": "mented73",                         # Not used with sqlite3.
        "HOST": "localhost",                             # Set to empty string for localhost NOT! Not used with sqlite3.
        "PORT": "",                             # Set to empty string for default. Not used with sqlite3.
    }
}

SITE_DOMAIN = "oppster.oppian.com"