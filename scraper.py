# -*- coding: utf-8 -*-
from datetime import datetime
from lxml import html
import dryscrape
import csv

from constants import first_type, second_type

IN_STOCK = u'有货'
URL = 'https://search.jd.com/Search?keyword=qnap&enc=utf-8&wq=qnap&pvid=yhzxfuxi.4ocx0a00n52av'


class ProductObj(object):

    def __init__(self, brand, mpn, url, name, price, stock):
        self.brand = brand
        self.mpn = mpn
        self.url = url
        self.name = name
        self.price = price
        self.stock = ProductObj.check_in_stock(stock)

    @staticmethod
    def check_in_stock(stock):
        if unicode(stock) == IN_STOCK:
            return 1
        return 0

    def as_dict(self):
        d = dict()
        d['Brand'] = unicode(self.brand).encode('utf-8')
        d['MPN'] = self.mpn
        d['URL'] = self.url
        d['Name'] = unicode(self.name).encode('utf-8')
        d['Price'] = unicode(self.price).encode('utf-8')
        d['Stock'] = self.stock
        return d


class ScrapeStrategy(object):

    def __init__(self, scrape_function):
        self.scrape = scrape_function

    def scrape(self):
        pass


def scrape_first_type_object(tree, link):

    brand = tree.xpath(first_type.BRAND_PATH)[0]
    stock = tree.xpath(first_type.STOCK_PATH)[0]
    name = tree.xpath(first_type.NAME_PATH)[0]
    price = tree.xpath(first_type.PRICE_PATH)[0]
    mpn = tree.xpath(first_type.MPN_PATH)[0]

    product_obj = ProductObj(brand, mpn, link, name, price, stock)
    return product_obj


def scrape_second_type_object(tree, link):

    brand = tree.xpath(second_type.BRAND_PATH)[0]
    stock = tree.xpath(second_type.STOCK_PATH)[0]
    name = tree.xpath(second_type.NAME_PATH)[0]
    price = tree.xpath(second_type.PRICE_PATH)[0]
    mpn = tree.xpath(second_type.MPN_PATH)[0]

    product_obj = ProductObj(brand, mpn, link, name, price, stock)
    return product_obj


class Validator:
    def __init__(self, first_type_strategy, second_type_strategy):
        self.first_type_strategy = first_type_strategy
        self.second_type_strategy = second_type_strategy

    def choose_strategy(self, tree):
        if tree.xpath(first_type.NAME_PATH):
            return self.first_type_strategy
        else:
            return self.second_type_strategy


def scrape():

    session = dryscrape.Session()
    session.set_attribute('auto_load_images', False)
    session.visit(URL)

    response = session.body()
    global_tree = html.fromstring(response)
    products_links = global_tree.xpath('//div[@id="J_goodsList"]/ul/li/div/div[1]/a/@href')
    output = []

    validator = Validator(ScrapeStrategy(scrape_first_type_object), ScrapeStrategy(scrape_second_type_object))

    for i, products_link in enumerate(products_links):
        t0 = datetime.now()

        session.visit('http:' + products_link)
        response = session.body()
        tree = html.fromstring(response)

        strategy = validator.choose_strategy(tree)
        output.append(strategy.scrape(tree, products_link))
        print datetime.now() - t0


    with open('products.csv', 'w') as csvfile:
        fieldnames = ['Brand', 'MPN', 'URL', 'Name', 'Price', 'Stock']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for obj in output:
            writer.writerow(obj.as_dict())

scrape()