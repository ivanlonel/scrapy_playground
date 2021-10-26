This project showcases a way to have a single [Scrapy](https://github.com/scrapy/scrapy) spider log in to a website and share the session cookies with other crawlers running simultaneously via `scrapy.crawler.CrawlerRunner`.

This is achieved by having all crawlers inherit from a `LoginSpider` class that handles login before firing each crawler's initial requests to the `parse` callback. Only the first instance sends the login request, while the remaining ones wait until it has successfully logged in and assigned the cookies to a class attribute visible by all of them.
