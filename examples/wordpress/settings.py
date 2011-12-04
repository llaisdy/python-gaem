# Helper functions

def days(number): return 60 * 60 * 24 * number

# Application settings

KEY = '73fd74b50e184dd4a09d51d31106648e'
URL = 'http://wordpress.example.org'

EXPIRES_UPLOADS = days(30)
EXPIRES_STATIC = days(7)
EXPIRES_DEFAULT = days(1)
