"""
Django settings for municipal_finance project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

import dj_database_url
import os
import environ
import logging

logger = logging.getLogger("municipal_finance")


TESTING = False

env = environ.Env()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ROOT_DIR = environ.Path(__file__) - 2

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "true") == "true"

PRELOAD_CUBES = os.environ.get("PRELOAD_CUBES", "false") == "true"

# SECURITY WARNING: keep the secret key used in production secret!
if DEBUG:
    SECRET_KEY = "-r&cjf5&l80y&(q_fiidd$-u7&o$=gv)s84=2^a2$o^&9aco0o"
else:
    SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

DATA_GOOGLE_ANALYTICS_ID = "UA-48399585-37"
SCORECARD_GOOGLE_ANALYTICS_ID = "UA-48399585-40"

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "municipal_finance",
    "scorecard",
    "infrastructure",
    "household",
    "webflow",
    "django.contrib.sites",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "pipeline",
    "django_extensions",
    "corsheaders",
    "rest_framework",
    "django_q",
    "storages",
    "debug_toolbar",
    "constance",
    "constance.backends.database",
    "import_export",
)

# Sites
# 2: Scorecard
# 3: API

if os.environ.get("SITE_ID", None):
    SITE_ID = int(os.environ.get("SITE_ID"))

DATA_PORTAL_URL = os.environ.get(
    "DATA_PORTAL_URL", "https://municipaldata.treasury.gov.za"
)

API_URL = DATA_PORTAL_URL + "/api"

MAPIT = {"url": "https://mapit.code4sa.org", "generation": "2"}

MIDDLEWARE = [
    "django.middleware.gzip.GZipMiddleware",
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    "municipal_finance.middleware.RedirectsMiddleware",
    "municipal_finance.middleware.SiteMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "municipal_finance.middleware.ApiErrorHandler",
]

CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"

CONSTANCE_ADDITIONAL_FIELDS = {
    'quarter_select': ['django.forms.fields.ChoiceField', {
        'widget': 'django.forms.Select',
        'choices': ((1, "1"), (2, "2"), (3, "3"), (4, "4"),)
    }],
}

CONSTANCE_CONFIG = {
    "LAST_AUDIT_YEAR": [
        2019,
        "The last financial year that should be included when compiling "
        "fiscal indicators for municipal profiles",
        int,
    ],
    "LAST_OPINION_YEAR": [
        2019,
        "The last financial year that should be included when gathering "
        "audit opinions for municipal profiles",
        int,
    ],
    "LAST_UIFW_YEAR": [
        2019,
        "The last financial year that should be included when compiling "
        "indicators that make use Unautherised, Irregular, Fruitless and "
        "Wasteful expenditure data for municipal profiles"
        "expenditure data",
        int,
    ],
    "LAST_AUDIT_QUARTER": [
        "2019q4",
        "The last quarter for which an audit is expected, used for "
        "determining if a demarcation was established before or after "
        "the last qudit tok place",
        str,
    ],
    "GRANTS_LATEST_YEAR": [
        2019,
        "The last year for which grant spending data is available. "
        "This is used to show \"Spent up to 2020-21 Q3\" or whatever is "
        "the selected year and quarter.",
        int,
    ],
    "GRANTS_LATEST_QUARTER": [
        4,
        "The last quarter for which grant spending data is available. "
        "This is used to show \"Spent up to 2020-21 Q3\" or whatever is "
        "the selected year and quarter.",
        "quarter_select",
    ],
}

ROOT_URLCONF = "municipal_finance.urls"

WSGI_APPLICATION = "municipal_finance.wsgi.application"

# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgres://municipal_finance:municipal_finance@localhost:5432/municipal_finance",
)
db_config = dj_database_url.parse(DATABASE_URL)
db_config["ATOMIC_REQUESTS"] = True
DATABASES = {"default": db_config}

# Caches
if DEBUG:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
            "LOCATION": "/var/tmp/django_cache",
        }
    }

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = "en-za"
TIME_ZONE = "Africa/Johannesburg"
USE_I18N = False
USE_L10N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True
FORMAT_MODULE_PATH = "municipal_finance.formats"


# CORS
CORS_ORIGIN_ALLOW_ALL = True


# Templates

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "debug": DEBUG,
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "municipal_finance.context_processors.google_analytics",
                "municipal_finance.context_processors.sentry_dsn",
                "municipal_finance.context_processors.api_details",
            ],
        },
    }
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

ASSETS_DEBUG = DEBUG
ASSETS_URL_EXPIRE = False

# assets must be placed in the 'static' dir of your Django app

# where the compiled assets go
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
# the URL for assets
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    str(ROOT_DIR.path("assets/bundles")),
]
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "pipeline.finders.PipelineFinder",
)

PYSCSS_LOAD_PATHS = [
    os.path.join(BASE_DIR, "municipal_finance", "static"),
    os.path.join(BASE_DIR, "municipal_finance", "static", "bower_components"),
    os.path.join(BASE_DIR, "scorecard", "static"),
    os.path.join(BASE_DIR, "scorecard", "static", "bower_components"),
    os.path.join(BASE_DIR, "census", "static"),
]

PIPELINE = {
    "STYLESHEETS": {
        "docs": {
            "source_filenames": (
                "bower_components/fontawesome/css/font-awesome.css",
                "bower_components/bootstrap-sass/assets/stylesheets/_bootstrap.scss",
                "slate/stylesheets/screen.css",
                "stylesheets/docs.scss",
            ),
            "output_filename": "docs.css",
        },
        "api-home": {
            "source_filenames": (
                "bower_components/fontawesome/css/font-awesome.css",
                "bower_components/bootstrap-sass/assets/stylesheets/_bootstrap.scss",
                "stylesheets/site.scss",
            ),
            "output_filename": "api-home.css",
        },
        "table": {
            "source_filenames": (
                "bower_components/fontawesome/css/font-awesome.css",
                "bower_components/bootstrap-sass/assets/stylesheets/_bootstrap.scss",
                "stylesheets/vendor/select2.min.css",
                "stylesheets/table.scss",
            ),
            "output_filename": "table.css",
        },
        "scorecard": {
            "source_filenames": (
                "stylesheets/vendor/leaflet-0.6.4.css",
                "stylesheets/vendor/leaflet.label.css",
            ),
            "output_filename": "scorecard.css",
        },
    },
    "JAVASCRIPT": {
        "js": {
            "source_filenames": (
                "javascript/vendor/jquery-1.12.3.min.js",
                "javascript/app.js",
            ),
            "output_filename": "app.js",
        },
        "docs": {
            "source_filenames": (
                "javascript/vendor/jquery-1.12.3.min.js",
                "slate/javascripts/lib/_energize.js",
                "slate/javascripts/lib/_lunr.js",
                "slate/javascripts/lib/_jquery_ui.js",
                "slate/javascripts/lib/_jquery.tocify.js",
                "slate/javascripts/lib/_jquery.highlight.js",
                "slate/javascripts/lib/_imagesloaded.min.js",
                "slate/javascripts/app/_lang.js",
                "slate/javascripts/app/_search.js",
                "slate/javascripts/app/_toc.js",
                "bower_components/underscore/underscore-min.js",
                "bower_components/backbone/backbone-min.js",
                "javascript/vendor/js.cookie.js",
                "bower_components/bootstrap-sass/assets/javascripts/bootstrap.min.js",
                "javascript/docs.js",
            ),
            "output_filename": "docs.js",
        },
        "api-home": {
            "source_filenames": (
                "javascript/vendor/jquery-1.12.3.min.js",
                "bower_components/bootstrap-sass/assets/javascripts/bootstrap.min.js",
                "javascript/app.js",
            ),
            "output_filename": "home.js",
        },
        "table": {
            "source_filenames": (
                "javascript/vendor/jquery-1.12.3.min.js",
                "bower_components/underscore/underscore-min.js",
                "bower_components/backbone/backbone-min.js",
                "javascript/vendor/d3-format.min.js",
                "javascript/vendor/select2.min.js",
                "javascript/vendor/js.cookie.js",
                "bower_components/bootstrap-sass/assets/javascripts/bootstrap.min.js",
                "javascript/table.js",
            ),
            "output_filename": "table.js",
        },
        "scorecard": {
            "source_filenames": (
                "bower_components/underscore/underscore-min.js",
                "bower_components/d3/d3.min.js",
                "js/vendor/d3-format.min.js",
                "js/vendor/typeahead-0.11.1.js",
                "js/vendor/leaflet-0.6.4.js",
                "js/vendor/leaflet.label.js",
                "js/charts.js",
                "js/place-finder.js",
                "js/maps.js",
            ),
            "output_filename": "scorecard.js",
        },
        "infrastructure": {
            "source_filenames": (
                "js/utils.js",
                "js/sorter.js",
                "js/barchart.js",
                "js/mm-webflow.js",
            ),
            "output_filename": "infrastructure.js",
        },
    },
    "CSS_COMPRESSOR": None,
    "JS_COMPRESSOR": None,
    "DISABLE_WRAPPER": True,
    "COMPILERS": ("municipal_finance.pipeline.PyScssCompiler",),
}

# Simplified static file serving.
# https://warehouse.python.org/project/whitenoise/
STATICFILES_STORAGE = "municipal_finance.pipeline.GzipManifestPipelineStorage"

WHITENOISE_MIMETYPES = {
    '.map': 'application/octet-stream',
}

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(asctime)s %(levelname)s %(module)s %(process)d %(thread)d %(message)s"
        }
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        }
    },
    "root": {"handlers": ["console"], "level": "ERROR"},
    "loggers": {
        "municipal_finance": {"level": "DEBUG" if DEBUG else "INFO"},
        #"sqlalchemy.engine": {"level": "INFO" if DEBUG else "WARN"},
        "django": {"level": "DEBUG" if DEBUG else "INFO"},
    },
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 150,
}

Q_CLUSTER = {
    "name": "DjangORM",
    "workers": 1,
    "timeout": 3600,
    "retry": 700,
    "queue_limit": 100,
    "bulk": 50,
    "orm": "default",
    "poll": 5,
    "max_attempts": 1,
    "ack_failures": True,  # Dequeue failed tasks
}

if not DEBUG:
    DEFAULT_FILE_STORAGE = "municipal_finance.storage.MediaStorage"
    AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY", "")
    AWS_STORAGE_BUCKET_NAME = env.str(
        "AWS_STORAGE_BUCKET_NAME", "munimoney-media"
    )
    AWS_S3_CUSTOM_DOMAIN = "%s.s3.amazonaws.com" % AWS_STORAGE_BUCKET_NAME
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
    }
else:
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME")
    AWS_DEFAULT_ACL = "public-read"
    AWS_BUCKET_ACL = "public-read"
    AWS_AUTO_CREATE_BUCKET = True
    AWS_S3_ENDPOINT_URL = env.str("AWS_S3_ENDPOINT_URL", None)
    AWS_S3_REGION_NAME = env.str("AWS_S3_REGION_NAME", None)
    AWS_S3_SECURE_URLS = env.bool("AWS_S3_SECURE_URLS", True)
    AWS_S3_CUSTOM_DOMAIN = env.str("AWS_S3_CUSTOM_DOMAIN", None)
    AWS_S3_FILE_OVERWRITE = False

# Do NOT use this for feature flags. Just use it to tell the outside world
# which environment messages e.g. logs or errors are coming from.
ENVIRONMENT = env.str("ENVIRONMENT")

SENTRY_DSN = env.str("SENTRY_DSN", None)
SENTRY_PERF_SAMPLE_RATE = env.float("SENTRY_PERF_SAMPLE_RATE", 0.1)

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=SENTRY_PERF_SAMPLE_RATE,
        environment=ENVIRONMENT,

        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True
    )

DEBUG_TOOLBAR = os.environ.get(
    "DJANGO_DEBUG_TOOLBAR", "false").lower() == "true"
logger.info("Django Debug Toolbar %s." %
            "enabled" if DEBUG_TOOLBAR else "disabled")
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": "municipal_finance.settings.show_toolbar_check"
}


def show_toolbar_check(request):
    return DEBUG and DEBUG_TOOLBAR
