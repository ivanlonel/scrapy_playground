from my_scrapy_project.spiders.login import LoginSpider


class QuotesSpider(LoginSpider):
    name = 'quotes'
    allowed_domains = ['quotes.toscrape.com']
    start_urls = ['https://quotes.toscrape.com/']
    custom_settings = {
        'HTTPCACHE_ENABLED': True,
        'HTTPCACHE_EXPIRATION_SECS': 3600
    }

    def parse(self, response):
        for row in response.css('div.quote'):
            item = {
                'text': row.xpath('normalize-space(./span[@class="text"]/text())').get(),
                'tags': row.xpath('normalize-space(./div[@class="tags"]/a[@class="tag"]/text())').getall(),
                'author': {
                    'name': row.xpath('normalize-space(./span/small[@class="author"]/text())').get(),
                    'goodreads_page': row.xpath('./span/a[contains(text(),"(Goodreads page)")]/@href').get()
                }
            }

            yield response.follow(
                url=row.xpath('./span/a[contains(text(),"(about)")]/@href').get(),
                callback=self.parse_author,
                errback=self.errback_author,
                cb_kwargs={'quote': item},
                dont_filter=True
            )

        next_page = response.css("nav > ul.pager > li.next > a::attr(href)").get()

        if next_page:
            yield response.follow(url=next_page, meta={'dont_cache': True})
        else:
            self.logger.debug(f'Next page URL not found in {response.url}')

    def parse_author(self, response, quote):
        details = response.css('div.author-details')
        quote['author'] |= {
            'name': details.xpath('normalize-space(./h3[@class="author-title"]/text())').get(),
            'birth_date': details.xpath('normalize-space(./p/span[@class="author-born-date"]/text())').get(),
            'birth_location': details.xpath('normalize-space(./p/span[@class="author-born-location"]/text())').get(),
            'description': details.xpath('normalize-space(./div[@class="author-description"]/text())').get(),
        }
        yield quote

    def errback_author(self, failure):
        self.logger.warning(f"Couldn't get author info: {failure!r}")
        yield failure.request.cb_kwargs['quote']
