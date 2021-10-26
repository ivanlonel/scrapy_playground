import os
import scrapy
from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.downloadermiddlewares.cookies import CookiesMiddleware
from twisted.internet.defer import DeferredLock
from my_scrapy_project.utils import async_sleep


class LoginSpider(scrapy.Spider):
    LOGIN_URL = 'https://quotes.toscrape.com/login'
    COOKIE_ERROR = 1
    __cookies = None
    __first_spider_opened = False
    __lock = DeferredLock()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, scrapy.signals.spider_opened)
        return spider

    async def spider_opened(self, spider):
        """
        If multiple child instances are running in the same process,
        ensures only the first spider will proceed without waiting for cookies.
        """

        LoginSpider.__lock.acquire()
        try:
            if LoginSpider.__first_spider_opened:
                while not LoginSpider.__cookies:
                    await async_sleep(1)
                if LoginSpider.__cookies == self.COOKIE_ERROR:
                    # https://github.com/scrapy/scrapy/issues/3435
                    try:
                        await self.crawler.engine.close_spider(spider, 'Unable to obtain session cookies')
                    except RuntimeError as e:
                        self.logger.debug(f'engine.close_spider raised {e!r}')
            else:
                LoginSpider.__first_spider_opened = True
        finally:
            LoginSpider.__lock.release()

    def start_requests(self):
        """
        Only the first spider instance will send the login request.
        The others shouldn't call start_requests() before cookies are ready.
        """
        if LoginSpider.__cookies:
            for url in self.start_urls:
                yield scrapy.Request(url,
                                     cookies=LoginSpider.__cookies,
                                     meta={'dont_cache': True},
                                     dont_filter=True)
        else:
            yield scrapy.Request(self.LOGIN_URL,
                                 callback=self.login,
                                 errback=self.errback_login,
                                 meta={'dont_cache': True},
                                 dont_filter=True)

    def login(self, response):
        formcss = 'form[action="/login"]'
        form = response.css(formcss)

        yield scrapy.FormRequest.from_response(
            response,
            formcss=formcss,
            formdata={
                'csrf_token': form.css('input[name="csrf_token"]::attr(value)').get(),
                'username': os.environ.get('MY_USERNAME', 'dummy_username'),
                'password': os.environ.get('MY_PASSWORD', 'dummy_password')
            },
            callback=self.after_login,
            errback=self.errback_login,
            dont_filter=True
        )

    def errback_login(self, failure):
        LoginSpider.__cookies = self.COOKIE_ERROR
        failure.raiseException()

    def after_login(self, response):
        if response.css('a[href="/logout"]').get():
            try:
                downloader_middlewares = self.crawler.engine.downloader.middleware.middlewares
                cookies_mw = next(iter(mw for mw in downloader_middlewares if isinstance(mw, CookiesMiddleware)))
                jar = cookies_mw.jars[response.meta.get('cookiejar')].jar
                LoginSpider.__cookies = [vars(cookie)
                                         for domain in jar._cookies.values()
                                         for path in domain.values()
                                         for cookie in path.values()]
            except Exception:
                LoginSpider.__cookies = self.COOKIE_ERROR
                raise

            self.logger.info('Successfully logged in')

            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter=True)
        else:
            retry_request = get_retry_request(response.request, spider=self, reason='Logout URL not found')
            if retry_request:
                yield retry_request
            else:
                LoginSpider.__cookies = self.COOKIE_ERROR
                raise scrapy.exceptions.CloseSpider(reason='Login failed')
