import re
import scrapy
from scrapy.loader import ItemLoader
from ..items import BdcItem
from itemloaders.processors import TakeFirst

pattern = r'(\xa0)?'
base = 'https://www.bdc.ca/BlogPostListBlock/ViewMore?pageLink=6234&language=en-CA&skip={}&take=5&blogPostListType=Horizontal%20-%20Large'
class BdcSpider(scrapy.Spider):
	name = 'bdc'
	page = 0
	start_urls = [base.format(page)]

	def parse(self, response):
		articles = response.xpath('//div[@class="blog-post-description"]')
		post_links = []

		for article in articles:
			date = article.xpath('.//span[@class="pretitle-tag"]/text()').get().split('|')[0].strip()
			link = article.xpath('.//a[@class="focused-link mt-auto"]/@href').get()
			post_links.append(link)
			yield response.follow(link, self.parse_post, cb_kwargs=dict(date=date))

		if len(post_links) == 5:
			self.page += 5
			yield response.follow(base.format(self.page), self.parse)

	def parse_post(self, response, date):
		title = response.xpath('//h1/text()').get().strip()
		if not title:
			title = ''.join(response.xpath('//h1//text()').getall())
		content = response.xpath('//div[@class="col-12 col-md-8 col-lg-8 no-gutters"]//text()').getall()
		content = [p.strip() for p in content if p.strip()]
		content = re.sub(pattern, "",' '.join(content))

		item = ItemLoader(item=BdcItem(), response=response)
		item.default_output_processor = TakeFirst()

		item.add_value('title', title)
		item.add_value('link', response.url)
		item.add_value('content', content)
		item.add_value('date', date)

		yield item.load_item()
