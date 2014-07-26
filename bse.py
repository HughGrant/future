# -*- coding: utf-8 -*-
import os, re, random
import requests
from bs4 import BeautifulSoup

MONEY_TYPE = {
    'US': 'USD',
}

class BSCollector(object):
    """docstring for BSCollector"""
    def __init__(self, url, pic_path, product_name=None):
        super(BSCollector, self).__init__()
        self.url = url
        self.product_name = product_name
        self.product_name_path = None
        html = requests.get(url)
        self.soup = BeautifulSoup(html.content)
        self.pd = {}
        self.attrs = {}
        self.pic_path = pic_path
        self.summary = None
        self.category_name = None
        self.trade_information = {}
        self.rich_descs = None
        # get product name if not provided in init func
        if not self.product_name:
            self.product_name = self.soup.find('h1', class_="fn").text.strip()

        self.product_name_path = valid_path(self.product_name)

    def collect_trade_information(self):
        table = self.soup.select('.btable')[0]
        names = table.select('.name')
        values = table.select('.value')
        names = [i.text.strip(':') for i in names]
        values = [i.text.strip() for i in values]
        raw_info = dict(zip(names, values))  
        
        for k, v in raw_info.iteritems():
            if 'Min.Order Quantity' == k:
                minOrderQuantity = v.split(' ')
                self.trade_information['minOrderQuantity'] = minOrderQuantity[0]
                self.trade_information['minOrderUnit'] = minOrderQuantity[1]

            elif 'FOB Price' == k and v != 'Get Latest Price':
                price = v.replace('Get Latest Price', '').split(' ')
                self.trade_information['moneyType'] = MONEY_TYPE[price[0]]
                self.trade_information['priceRangeMin'] = price[1].strip('$')
                self.trade_information['priceRangeMax'] = price[3].strip()
                self.trade_information['priceUnit'] = price[6]

            elif 'Port' == k:
                self.trade_information['port'] = v
            
            elif 'Payment Terms' == k:
                self.trade_information['paymentMethod'] = v.strip()
            
            elif 'Supply Ability' == k:
                sa = v.strip().split(' ')
                self.trade_information['supplyQuantity'] = sa[0]
                self.trade_information['supplyUnit'] = sa[1]
                self.trade_information['supplyPeriod'] = sa[-1]

        if 'minOrderQuantity' not in self.trade_information:
            self.trade_information['minOrderQuantity'] = '1'
            self.trade_information['minOrderUnit'] = 'Set/Sets'

        if 'Port' not in self.trade_information:
            self.trade_information['port'] = 'Shenzhen'

        if 'Payment Terms' not in self.trade_information:
            self.trade_information['paymentMethod'] = 'T/T,Western Union,MoneyGram,PAYPAL'

        if 'supplyQuantity' not in self.trade_information:
            self.trade_information['supplyQuantity'] = '100'
            self.trade_information['supplyUnit'] = 'Set/Sets'
            self.trade_information['supplyPeriod'] = 'Week'

    def collect_specifications(self):
        self.summary = self.soup.find('p', class_='description').text

    def collect_attrs(self):
        attrs_names = self.soup.find_all('span', class_='attr-name J-attr-name')
        attrs_values = self.soup.find_all('td', class_='value J-value')

        if len(attrs_names) != len(attrs_values):
            raise Exception('collected attribute is not paired')

        names = [i.text.strip().replace('.', '') for i in attrs_names]
        values = [i.text.strip() for i in attrs_values]
        self.attrs = dict(zip(names, values))

        # collect category name
        cns = self.soup.select('.category')
        cns = [cn.text for cn in cns]
        self.category_name = ' '.join(cns[2:])

    def collect_pics(self):
        path = os.path.join(self.pic_path, self.product_name_path)
        if not os.path.exists(path):
            os.makedirs(path)
        # main picture
        main_img = self.soup.find('img', class_='photo pic J-pic')
        src = main_img.get('src').replace('_250x250.jpg', '')
        abs_path = os.path.join(path, self.product_name_path + '.jpg')
        self.save_pic(abs_path, src)

        # description pictures
        imgs = self.soup.select('#J-rich-text-description noscript img')
        for i, img in enumerate(imgs):
            src = img['src']
            if src.endswith('.jpg'):
                abs_path = os.path.join(path, self.product_name_path + str(i) + '.jpg')
                self.save_pic(abs_path, src)

    def collect_package_delivery(self):
        # package & delivery
        h3 = self.soup.find('h3', text='Packaging & Delivery')
        if h3:
            table = h3.find_next_sibling('table')
            tds = table.select('td')
            for i, td in enumerate(tds):
                if i % 2 == 0:
                    self.pd.update({td.text:tds[i+1].text})
        else:
            self.pd.update({'Packaging Detail:':'Standard Shipping Package'})
            self.pd.update({'Delivery Detail:':'3 Working Days Usually'})

    def collect_rich_descs(self):
        div = self.soup.find('div', id='J-rich-text-description')
        div = BeautifulSoup(div.prettify())
        elements = div.find_all(['p', 'table', 'ul'])
        html = []
        for ele in elements:
            if 'p' == ele.name and not ele.find_parents('table'):
                if ele.find_all('span', text=re.compile('\S+')):
                    p_html = str(ele).strip().replace('\n', '').replace("'","\\'")
                    html.append(p_html)
                    if len(ele.text) > 40:
                        html.append('<br /><br />')
                    else:
                        html.append('<br />')
            elif ele.name in ['table', 'ul']:
                table_html = str(ele).strip().replace('\n', '').replace("'","\\'")
                html.append(table_html)
                html.append('<br />')
        self.rich_descs = ''.join(html)

        with file('t.html', 'wb') as f:
            print >> f, self.rich_descs

    def collect_key_words(self):
        # url = 'http://hz.my.data.alibaba.com/industry/.json?action=CommonAction&iName=searchKeywords&'
        pass

    def collect(self):
        self.collect_specifications()
        self.collect_rich_descs()
        self.collect_package_delivery()
        self.collect_attrs()
        self.collect_trade_information()
        self.collect_pics()
        self.collect_rich_descs()
        # self.collect_key_words()

    def save_pic(self, name, url):
        bin = requests.get(url)
        with open(name, 'wb+') as f:
            f.write(bin.content)

def collect_names(product_name):
    search_url = 'http://www.alibaba.com/trade/search?fsb=y&IndexArea=product_en&CatId=&SearchText='
    url = search_url + product_name.replace(' ', '+')
    html = requests.get(url)
    soup = BeautifulSoup(html.content)
    hrefs = soup.select('h2 a')
    names = [a['title'] for a in hrefs]
    return names

def valid_path(product_name):
    # remove special character to avoid bad path
    stable = {ord(i):None for i in '/\:*?"<>|'}
    return unicode(product_name).translate(stable)

def db_name(email):
    return email.replace('@', 'at').replace('.', 'dot')


if __name__ == '__main__':
    # url ='http://www.alibaba.com/product-detail/TDP1-5-TDP5-TDP6-Tablet-Making_1892266532.html'
    # bsc = BSCollector(url, 'e:/ppictures')
    # bsc.collect_rich_descs()

    collect_names('http://www.alibaba.com/trade/search?fsb=y&IndexArea=product_en&CatId=&SearchText=pneumatic+pet+strapping+machine')
