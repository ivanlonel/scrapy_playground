from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor

if __name__ == '__main__':
    configure_logging()
    runner = CrawlerRunner(get_project_settings())
    for spider in ('quotes', 'authors', 'tags'):
        runner.crawl(spider)
    runner.join().addBoth(lambda _: reactor.stop())
    reactor.run()  # the script will block here until all crawling jobs are finished
