from my_scrapy_project.spiders.login import LoginSpider


class TagsSpider(LoginSpider):
    name = 'tags'
    allowed_domains = ['quotes.toscrape.com']
    start_urls = ['https://quotes.toscrape.com/']
    custom_settings = {
        'ITEM_PIPELINES': {
            'my_scrapy_project.pipelines.DuplicatesPipeline': 400
        }
    }

    def parse(self, response):
        for tag in response.css('div.quote > div.tags > a.tag'):
            yield {'id': tag.xpath('normalize-space(./text())').get()}

        next_page = response.css("nav > ul.pager > li.next > a::attr(href)").get()

        if next_page:
            yield response.follow(url=next_page)
        else:
            self.logger.debug(f'Next page URL not found in {response.url}')
