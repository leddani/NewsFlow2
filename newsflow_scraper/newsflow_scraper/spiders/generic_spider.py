import scrapy


class GenericSpiderSpider(scrapy.Spider):
    name = "generic_spider"
    allowed_domains = []  # Lejo të gjitha domain-et

    def start_requests(self):
        url = getattr(self, 'url', None)
        if url:
            yield scrapy.Request(url, callback=self.parse)
        else:
            self.logger.error('Nuk u dha asnjë URL për scraping.')

    def parse(self, response):
        title = response.xpath('//title/text()').get() or 'No Title'
        content = ' '.join(response.xpath('//p//text()').getall())
        yield {
            'title': title,
            'url': response.url,
            'content': content or 'No content found.'
        }
