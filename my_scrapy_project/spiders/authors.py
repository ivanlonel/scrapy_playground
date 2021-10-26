from my_scrapy_project.spiders.login import LoginSpider


class AuthorsSpider(LoginSpider):
    name = 'authors'
    allowed_domains = ['quotes.toscrape.com']
    start_urls = ['https://quotes.toscrape.com/']

    def parse(self, response):
        for row in response.xpath('//div[@class="quote"]/span[small[@class="author"]]'):
            yield response.follow(
                url=row.xpath('./a[contains(text(),"(about)")]/@href').get(),
                callback=self.parse_author,
                cb_kwargs={'goodreads_page': row.xpath('./a[contains(text(),"(Goodreads page)")]/@href').get()}
            )

        next_page = response.css("nav > ul.pager > li.next > a::attr(href)").get()

        if next_page:
            yield response.follow(url=next_page)
        else:
            self.logger.debug(f'Next page URL not found in {response.url}')

    def parse_author(self, response, goodreads_page):
        details = response.css('div.author-details')
        yield {
            'name': details.xpath('normalize-space(./h3[@class="author-title"]/text())').get(),
            'birth_date': details.xpath('normalize-space(./p/span[@class="author-born-date"]/text())').get(),
            'birth_location': details.xpath('normalize-space(./p/span[@class="author-born-location"]/text())').get(),
            'description': details.xpath('normalize-space(./div[@class="author-description"]/text())').get(),
            'goodreads_page': goodreads_page
        }
