from settings import *
from path import path
from openedx.core.lib.tempdir import mkdtemp_clean

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Add edx required
    'south',
    # ADD EDX-platform dependencies before test
    'xmodule_django',
    'track',
    'social.apps.django_app.default',
    'xblock_django',
    'student',

    # Real app of this package
    'ecoapi',
    'oai',
    'xapi'
)


# Copy from edx-platform
FEATURES = {}
COURSE_KEY_PATTERN = r'(?P<course_key_string>[^/+]+(/|\+)[^/+]+(/|\+)[^/]+)'
COURSE_ID_PATTERN = COURSE_KEY_PATTERN.replace('course_key_string', 'course_id')
ALL_LANGUAGES = (
    [u"en", u"English"],
    [u"it", u"Italian"],
)
XQUEUE_INTERFACE = {
        "basic_auth": [
            "edx",
            "edx"
        ],
        "django_auth": {
            "password": "password",
            "username": "lms"
        },
        "url": "http://localhost:18040"
}
TRACK_MAX_EVENT = 50000

TEST_ROOT = path("test_root")
DOC_STORE_CONFIG = {
    'host': 'localhost',
    'db': 'xmodule',
    'collection': 'modulestore',
    # If 'asset_collection' defined, it'll be used
    # as the collection name for asset metadata.
    # Otherwise, a default collection name will be used.
}
MODULESTORE = {
    'default': {
        'ENGINE': 'xmodule.modulestore.mixed.MixedModuleStore',
        'OPTIONS': {
            'mappings': {},
            'stores': [
                {
                    'NAME': 'split',
                    'ENGINE': 'xmodule.modulestore.split_mongo.split_draft.DraftVersioningModuleStore',
                    'DOC_STORE_CONFIG': DOC_STORE_CONFIG,
                    'OPTIONS': {
                        'default_class': 'xmodule.hidden_module.HiddenDescriptor',
                        'fs_root': TEST_ROOT / "data",
                        'render_template': 'edxmako.shortcuts.render_to_string',
                    }
                },
                {
                    'NAME': 'draft',
                    'ENGINE': 'xmodule.modulestore.mongo.DraftMongoModuleStore',
                    'DOC_STORE_CONFIG': DOC_STORE_CONFIG,
                    'OPTIONS': {
                        'default_class': 'xmodule.hidden_module.HiddenDescriptor',
                        'fs_root': TEST_ROOT / "data",
                        'render_template': 'edxmako.shortcuts.render_to_string',
                    }
                },
                {
                    'NAME': 'xml',
                    'ENGINE': 'xmodule.modulestore.xml.XMLModuleStore',
                    'OPTIONS': {
                        'data_dir': mkdtemp_clean(dir=TEST_ROOT),  # never inadvertently load all the XML courses
                        'default_class': 'xmodule.hidden_module.HiddenDescriptor',
                    }
                }
            ]
        }
    }
}


CONTENTSTORE = {
    'ENGINE': 'xmodule.contentstore.mongo.MongoContentStore',
    'DOC_STORE_CONFIG': {
        'host': 'localhost',
        'db': 'xcontent',
        'port': 27017,
    }
}