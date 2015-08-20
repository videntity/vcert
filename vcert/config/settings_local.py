import os

from settings import *

DEBUG = False
TIME_ZONE = 'America/New_York'


# Add your own production Key and Secret using the
# developer interfaces for Facebook, Twitter and LinkedIn.

FACEBOOK_APP_ID =	"change-me"
FACEBOOK_API_SECRET=    "chenge-me"


# Social Auth Keys
TWITTER_CONSUMER_KEY              = 'change-me'
TWITTER_CONSUMER_SECRET           = 'change-me'

# https://developer.linkedin.com
LINKEDIN_CONSUMER_KEY        = 'change-me'
LINKEDIN_CONSUMER_SECRET     = 'change-me'

AWS_ACCESS_KEY_ID = 'change-me'
AWS_SECRET_ACCESS_KEY = 'change-me'

AWS_KEY = AWS_ACCESS_KEY_ID
AWS_SECRET = AWS_SECRET_ACCESS_KEY

ADMINS = (
     ('Your admin', 'foo@bar.com'),
     ('Your other admin', 'bar@foo.com'),
)

