# -*- coding: utf-8 -*-
import os
import time
from pymongo import MongoClient
from bson import ObjectId
from bse import BSCollector, valid_path
from webdriver import WebDriver as Chrome
from utils import select_file

# ['hotmail', 'live', 'outlook']
USER_DATA_DIR = 'e:/hope/chrome_profile'
LOGIN_URL = 'https://login.alibaba.com/'
VIP_URL = 'http://sh.vip.alibaba.com/'
ID_METHOD = {
    'minOrderQuantity': 'fill',
    'priceRangeMin': 'fill',
    'supplyQuantity': 'fill',
    'priceUnit': 'select',
    'moneyType': 'select',
    'minOrderUnit': 'select',
    'supplyUnit': 'select',
    'priceRangeMax': 'fill',
    'paymentMethod': 'check',
    'port': 'fill',
    'supplyPeriod': 'select',
}

class Ali(object):
    """docstring for Ali"""
    def __init__(self, email):
        super(Ali, self).__init__()
        # email here as the broswer profile dir name
        self.b = Chrome(user_data_dir=os.path.join(USER_DATA_DIR, valid_path(email)))
        self.search_url = 'http://www.alibaba.com/trade/search?fsb=y&IndexArea=product_en&CatId=&SearchText='
        self.manage_product_url = 'http://hz.productposting.alibaba.com/product/manage_products.htm'
        self.copy_product_url = 'http://hz.productposting.alibaba.com/product/post_product_interface.htm?from=manage&import_product_id='
        self.keywords_url = 'http://hz.my.data.alibaba.com/industry/keywords.htm'
        self.yason = MongoClient()['yason']
        self.key_words_table = self.yason.key_words_table
        self.products_table = self.yason.products_table
        self.product_name_table = self.yason.product_name_table

    def js_fill(self, selector, value):
        js = "document.querySelector('%s').value = '%s'" % (selector, value)
        self.b.execute_script(js)

    def login(self, email, password):
        self.b.visit(VIP_URL)

        if not self.b.status_code.is_success():
            return False

        username = self.b.find_by_css('#xloginPassportId').first
        if username.value != email:
            self.js_fill('#xloginPassportId', email)

        pwd = self.b.find_by_css('#xloginPasswordId').first
        if pwd.value != password:
            self.js_fill('#xloginPasswordId', password)

        self.b.find_by_css('#signInButton').first.click()
        return True

    def get_auth_code(self):
        self.b.find_by_css('input[class="get-authcode-btn"]').first.click()

    def input_auth_code(self, auth_code):
        self.b.find_by_css('input[class="auth-code"]').first.fill(auth_code)
        self.b.find_by_css('input[class="validate-submit-btn submit-btn"]').first.click()

    def upload_product(self, product_id):
        p = self.products_table.find_one({'_id':ObjectId(product_id)})

        self.b.visit('http://hz.productposting.alibaba.com/product/posting.htm')
        # clear the ui mask
        if self.b.find_by_css('div[class="ui-mask"]'):
            self.b.find_by_css('a[class="ui-window-close"]').first.click()

        # fill the category form
        # self.b.find_by_css('#keyword').first.fill(p['category_name'])
        self.js_fill('#keyword', p['category_name'])
        self.b.find_by_css('button').first.click()
        self.b.find_by_css('.current').first.double_click()
        # fill the product info page
        self.fill_product_detail(p)

    def browser_select_file(self, name):
        image_path = 'e:\hope\images'
        file_path = os.path.join(image_path, name, name + '.jpg')
        select_file(file_path, u'打开')

    def copy_to_new_product(self, aid, search_keyword):
        url = self.copy_product_url + aid
        p = self.products_table.find_one({'aid':aid})
        self.b.visit(url)
        self.b.find_by_css('#yuigen0').first.click()
        self.browser_select_file(p['product_name_path'])
        self.fill_three_key_words(search_keyword)
        self.fill_new_product_name(p['product_name'])
        submit_btn = self.b.find_by_css('#submitFormBtnA').first
        submit_btn.mouse_over()
        while not self.b.find_by_css('#withPicStatic').first.visible:
            time.sleep(1)
        submit_btn.click()
        if self.b.is_element_present_by_css('#display-new', 5):
            return True

    def get_product_id(self, product_name, product_id):
        if 'products_manage' not in self.b.url:
            self.b.visit(self.manage_product_url)

        first_page = self.b.find_link_by_text('1')
        if first_page:
            first_page.click()

        aid = self.get_product_aid_recursively(product_name, product_id)
        return aid

    def get_product_aid_recursively(self, product_name, product_id):
        while self.b.is_element_not_present_by_css('.product-item-title'):
            time.sleep(1)
          
        nonesence = 'http://hz.productposting.alibaba.com/product/product_detail.htm?id='
        a = self.b.find_link_by_partial_text(product_name)
        if a:
            aid = a.first['href'].replace(nonesence, '').strip()
            self.products_table.update({'_id':ObjectId(product_id)}, {'$set':{'aid': aid}})
            return aid
        else:
            if self.b.find_by_css('.ui-pagination-disabled.ui-pagination-next'):
                return None
            else:
                self.b.find_by_css('.ui-pagination-next').first.click()
                self.get_product_aid_recursively(product_name, product_id)
        return None

    def collect_key_words(self, keywords):
        if self.b.url != self.keywords_url:
            self.b.visit(self.keywords_url)

        if self.b.is_element_present_by_css('#J-search-keywords'):
            self.b.find_by_css('#J-search-keywords').first.fill(keywords)
            self.b.find_by_css('#J-search-trigger').first.click()
        else:
            return 0

        counter = 0
        while self.b.is_element_present_by_css('.J-keyword-line'):
            one_page_keywords = self.b.find_by_css('.J-keyword-line')
            for line in one_page_keywords:
                tds = line.find_by_tag('td')
                counter += 1
                data = {
                    'search_keyword': keywords,
                    'keyword': tds[0].text,
                    'company_cnt': tds[1].text,
                    'showwin_cnt': tds[2].text,
                    'hotness': tds[3].text
                }
                self.key_words_table.insert(data)
            if counter > 60:
                return counter
            #save key words
            if self.b.is_element_present_by_css('.ui-pagination-next.ui-pagination-disabled'):
                return counter
            else:
                self.b.find_by_css('.ui-pagination-next').first.click()
        return counter

    def fill_new_product_name(self, product_name):
        variant_name = self.product_name_table.find_one({'product_name':product_name}).sort('used_count')
        # self.b.find_by_css('#productName').first.fill(variant_name['variant'])
        self.js_fill('#productName', variant_name['variant'])
        self.product_name_table.update(variant_name, {'$inc':{'used_count':1}})

    def fill_three_key_words(self, search_keyword):
        condition = {'search_keyword':search_keyword.lower()}
        kws = self.key_words_table.find(condition).sort('used_count').limit(3)
        keywords = []
        for kw in kws:
            keywords.append(kw['keyword'])
            self.key_words_table.update(kw, {'$inc':{'used_count':1}})

        # self.b.find_by_css('#productKeyword').first.fill(keywords[0])
        # self.b.find_by_css('#keywords2').first.fill(keywords[1])
        # self.b.find_by_css('#keywords3').first.fill(keywords[2])
        self.b.js_fill('#productKeyword', keywords[0])
        self.b.js_fill('#keywords2', keywords[1])
        self.b.js_fill('#keywords3', keywords[2])

    def fill_product_detail(self, bse):
        while self.b.is_element_not_present_by_css('h1[class="ui-form-guide"]'):
            time.sleep(1)
        # product name
        # self.b.find_by_css('#productName').first.fill(bse['product_name'])
        self.js_fill('#productName', bse['product_name'])
        # three key words
        self.fill_three_key_words(bse['key_words'])
        # listing description
        # self.b.find_by_css('#summary').first.fill(bse['summary'])
        self.js_fill('#summary', bse['summary'])
        # product detail
        name = self.b.find_by_css('.attr-title')
        option = self.b.find_by_css('.attribute-table-td')
        pi = bse['attrs']

        for i, n in enumerate(name):
            text = n.text
            if text == 'Type:':
                pi.pop('Type:')

            elif text == 'After-sales Service Provided:':
                default_service = 'No overseas service provided'
                self.b.find_option_by_text(pi.pop('After-sales Service Provided:', default_service)).first.click()

            elif text == 'Certification:':
                option[i].find_by_tag('input').first.fill(pi.pop('Certification:', 'China Compulsory Certification'))

            elif text == 'Weight:':
                option[i].find_by_tag('input').first.fill(pi.pop('Weight:', 'kg'))

            elif text == 'Dimension(L*W*H):':
                option[i].find_by_tag('input').first.fill(pi.pop('Dimension(L*W*H):', 'mm'))

            elif text == 'Model Number:':
                option[i].find_by_tag('input').first.fill(pi.pop('Model Number:', 'YASON'))

            elif text == 'Brand Name:':
                option[i].find_by_tag('input').first.fill(pi.pop('Brand Name:', 'YASON'))

            elif text == 'Power:':
                power = pi.pop('Power:', None)
                if power:
                    option[i].find_by_tag('input').first.fill(power)

            elif text == 'Voltage:':
                option[i].find_by_tag('input').first.fill(pi.pop('Voltage:', '220v or 110v or customized'))

            elif text == 'Condition:':
                self.b.find_option_by_text('New').first.click()

            elif text == 'Place of Origin:':
                self.b.select('contryValue', 'CN-China (Mainland)')
                self.b.select('provinceValue', 'GUA-Guangdong')

            elif text == 'Driven Type:':
                dt = pi.pop('Driven Type:', 'Manual')
                checked = self.choose_option(option[i].find_by_tag('select').first, dt)
                if not checked:
                    option[i].find_by_tag('input').first.fill(dt.capitalize())

            elif text == 'Application:':
                self.check_boxes(option[i], pi.pop('Application:', 'Chemical,Medical'))

            elif text == 'Packaging Type:':
                self.check_boxes(option[i], pi.pop('Packaging Type:', 'Cartons'))

            elif text == 'Packaging Material:':
                self.check_boxes(option[i], pi.pop('Packaging Material:', 'Paper,Wood'))

            elif text == 'Automatic Grade:':
                ag = pi.pop('Automatic Grade:', 'Semi-Automatic')
                checked = self.choose_option(option[i].find_by_tag('select').first, ag)
                if not checked:
                    option[i].find_by_tag('input').first.fill(ag.capitalize())

        if pi:
            add_button = self.b.find_by_css('#copyActionButton').first
            # there is a default one, so minus it
            for i in range(len(pi) - 1):
                add_button.click()
            attrs = self.b.find_by_css('.custom-attr-item')
            for att in attrs:
                n, v = pi.popitem()
                inputs = att.find_by_tag('input')
                inputs[0].fill(n)
                inputs[1].fill(v)


        # trade information NO WHOLESALE right now
        if self.b.is_element_present_by_id('setDefaultBtn'):
            self.b.find_by_css('#setDefaultBtn').first.click()

        for k, v in bse['trade_information'].iteritems():
            if 'fill' == ID_METHOD[k]:
                self.b.find_by_id(k).first.fill(v)
            elif 'select' == ID_METHOD[k]:
                self.choose_option(self.b.find_by_id(k).first, v)
            elif 'paymentMethod' == k:
                self.check_payment_method(v)

        self.b.find_by_css('#packagingDesc').first.fill(bse['pd']['Packaging Detail:'])
        self.b.find_by_css('#consignmentTerm').first.fill(bse['pd']['Delivery Detail:'])
        # rich descriptions
        js = "tinyMCE.activeEditor.setContent('%s')" % bse['rich_descs']
        self.b.execute_script(js)
        # select product main image
        self.b.find_by_css('#yuigen0').first.click()
        self.browser_select_file(bse['product_name_path'])

    def check_payment_method(self, values):
        values = values.split(',')
        values = [v.strip() for v in values]
        checked_values = []
        check_boxes = {}
        for i in range(1, 7):
            box = self.b.find_by_id('paymentMethod' + str(i)).first
            check_boxes[box.value] = box

        for value in values:
            if value in check_boxes:
                check_boxes[value].check()
                checked_values.append(value)
        # if all checked then no other needs to be added
        if len(values) == len(checked_values):
            return

        left_values = set(values) - set(checked_values)
        self.b.find_by_css('#paymentMethodOther').check()
        other = ', '.join([v.capitalize() for v in left_values])
        self.b.find_by_css('#paymentMethodOtherDesc').first.fill(other)

    def choose_option(self, select, value):
        options = select.find_by_tag('option')
        for option in options:
            if option.text == value:
                option.check()
                return True
        # check Other option before return
        for option in options:
            if option.text == 'Other':
                option.check()
        return False

    def check_boxes(self, checkbox, values):
        values = values.split(',')
        values = [v.strip() for v in values]
        options = checkbox.find_by_tag('input')
        other_check_box = None
        checked_values = []

        for option in options:
            true_value = option.value.split('-')[-1]
            if true_value == 'Other':
                other_check_box = option
            elif true_value in values:
                checked_values.append(true_value)
                option.check()
        # deal with other
        if len(values) == len(checked_values):
            return

        left_values = set(values) - set(checked_values)
        other_check_box.check()
        other = ', '.join([v.capitalize() for v in left_values])
        checkbox.find_by_tag('input')[-1].fill(other)

    def quit(self):
        try:
            self.b.quit()
        except Exception, e:
            print e

if __name__ == '__main__':
    print 'unable to execute from here'
