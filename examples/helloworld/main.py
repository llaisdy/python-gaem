import gaem
import gaem.middleware
import gaem.middleware.api
import gaem.middleware.cache
import gaem.middleware.fetch
import gaem.middleware.dos

KEY = '73fd74b50e184dd4a09d51d31106648e'
URL = 'http://www.example.org'

MIDDLEWARE_CLASSES = (
    gaem.middleware.api.Cache(key=KEY),
    gaem.middleware.cache.Memcache(),
    gaem.middleware.cache.Datastore(),
    gaem.middleware.dos.DoS(),
    gaem.middleware.fetch.Fetch(url=URL),
)

application = gaem.Application(MIDDLEWARE_CLASSES)

if __name__ == '__main__':
    application.run()
