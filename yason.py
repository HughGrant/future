# -*- coding:utf-8 -*-
import os, shutil
from glob import glob
import yaml
from flask import Flask, render_template, send_from_directory, request
from flask import redirect, url_for, jsonify, session
from pymongo import MongoClient
from bson import ObjectId
from bse import BSCollector, collect_names, valid_path, db_name

app = Flask(__name__)
app.secret_key = '\x9bU\xa2\xf9Y\xa78\xc4\xde\xc5\x10t\xc0A\xe3`&\xd5\xeb\x00\xc5\x02e\xf7'
db = MongoClient()
image_path = os.path.join(os.getcwd(), 'images')

@app.route('/')
def index_page():
    tabs = []
    pages = []
    for fname in glob('*.yaml'):
        file_path = os.path.join(os.getcwd(), fname)
        c = yaml.load(file(file_path))
        pages.append(c)
        tabs.append({'id': c['tab']['id'], 'name': c['tab']['name']})

    accounts = db['yason'].accounts.find()
    return render_template('dindex.html', 
            accounts=accounts, tabs=tabs,
            pages=pages)


# @app.route('/login')
# def login():
#     condition = {'username':username, 'password':password}
#     user = db.users.find_one(condition)
    # if user:

@app.route('/set_db', methods=['POST'])
def set_db():
    session['db_name'] = db_name(request.form['email'])
    return 'success'

@app.route('/product_category', methods=['POST'])
def product_category():
    categories = db[session['db_name']].products_table.distinct('category_name')
    return render_template('product_category.html', categories=categories)

@app.route('/product_keyword', methods=['POST'])
def product_keywords():
    keywords = db[session['db_name']].products_table.distinct('key_words')
    return render_template('product_keyword.html', keywords=keywords)
    
@app.route('/list_products', methods=['POST'])
def list_products():
    cn = request.form['category_name']
    query = db[session['db_name']].products_table.find({'category_name':cn})
    if not query.count():
        return 'No products under this category'
    return render_template('dproducts.html', products=query)

@app.route('/add_keyword', methods=['POST'])
def add_keyword():
    search_keyword = request.form['search_keyword']
    keyword = request.form['keyword']
    data = {
        'search_keyword': search_keyword,
        'keyword': keyword,
        'company_cnt': '0',
        'showwin_cnt': '0',
        'hotness': '0'
    }
    result = db[session['db_name']].key_words_table.insert(data)
    return render_template('keywords.html', keywords=[data])

@app.route('/check_keyword', methods=['POST'])
def check_keyword():
    pid = {'_id':ObjectId(request.form['pid'])}
    product = db.products_table.find_one(pid)
    sc = {'search_keyword':product['key_words']}
    count = db.key_words_table.find(sc).count()
    return str(count)

@app.route('/check_product_name', methods=['POST'])
def check_product_name():
    product_name = request.form['product_name']
    count = db.product_name_table.find({'product_name':product_name}).count()
    return str(count)

@app.route('/remove_keywords', methods=['POST'])
def remove_keyword():
    keywords = request.form['keywords']
    result = db.key_words_table.remove({'search_keyword':keywords})
    return jsonify(result)

@app.route('/common_alter', methods=['POST'])
def common_alter():
    new_value = request.form['new_value'].strip()
    prop_name = request.form['prop_name']
    pid = {'_id':ObjectId(request.form['pid'])}
    cdb = db[session['db_name']]
    if prop_name == 'product_name':
        return alter_name_aftermath(new_value, pid, cdb)

    re = cdb.products_table.update(pid, {'$set':{prop_name:new_value}})
    if re['ok']:
        return 'success'
    return 'fail'

def alter_name_aftermath(pn, pid, cdb):
    pn = valid_path(pn)
    product = cdb.products_table.find_one(pid)
    
    if product['product_name'] == pn:
        return 'No need to change'

    old = os.path.join(image_path, product['product_name_path'])
    new = os.path.join(image_path, pn)
    if os.path.exists(old):
        os.rename(old, new)

    old_file_path = os.path.join(new, product['product_name_path'] + '.jpg')
    if os.path.exists(old_file_path):
        new_file_path = os.path.join(new, pn + '.jpg')
        os.rename(old_file_path, new_file_path)

    result = cdb.products_table.update(pid, {'$set':{'product_name':pn, 'product_name_path':pn}})
    if result['ok']:
        return 'success'
    return 'fail'

@app.route('/renew_desc', methods=['POST'])
def renew_desc():
    pid = {'_id':ObjectId(request.form['pid'])}
    cdb = db[session['db_name']]
    product = cdb.products_table.find_one(pid)
    bsc = BSCollector(product['url'], image_path, product['product_name'])
    bsc.collect_rich_descs()
    old_path = os.path.join(image_path, product['product_name_path'])
    if os.path.exists(old_path):
        shutil.rmtree(old_path)
    bsc.collect_pics()
    data = {'rich_descs':bsc.rich_descs}
    result = cdb.products_table.update(pid, {'$set':data})
    if result['ok']:
        return 'success'
    return 'fail'

@app.route('/create_product', methods=['POST'])
def create_product():
    url = request.form['url']
    kws = request.form['key_words']
    category = request.form['category']
    bsc = BSCollector(url, image_path)
    bsc.collect()
    data = {
        'url': url,
        'key_words': kws,
        'attrs': bsc.attrs,
        'pd': bsc.pd,
        'summary': bsc.summary,
        'category_name': bsc.category_name,
        'trade_information': bsc.trade_information,
        'rich_descs': bsc.rich_descs,
        'product_name': bsc.product_name.title(),
        'product_name_path': bsc.product_name_path
    }
    if category:
        data.update({'category_name':category})

    pid = db.products_table.insert(data)
    p = db.products_table.find_one({'_id':pid})
    return render_template('product.html', products=[p])

@app.route('/list_keywords', methods=['POST'])
def list_keywords():
    if 'keyword' in request.form:
        keyword = request.form['keyword']
    else:
        pid = ObjectId(request.form['pid'])
        product = db[session['db_name']].products_table.find_one(pid)
        keyword = product['key_words']
    kws = db[session['db_name']].key_words_table.find({'search_keyword':keyword})
    if not kws.count():
        return "Keywords not collected yet"
    return render_template('keywords.html', keywords=kws)

# @app.route('/collect_names', methods=['POST'])
# def collect_names():
#     product_name = request.form['product_name']
#     names = collect_names(product_name)
#     data = []
#     for name in names:
#         data.append({'product_name':product_name, 'variant':name})
#     result = db[session['db_name']].product_name_table.insert(data)
#     return '%d names collected' % len(result)

@app.route('/create_ali_account', methods=['POST'])
def create_ali_account():
    email = request.form['email']
    result = db.accounts.find({'email':email}).count()
    if result:
        return ''
    pwd = request.form['password']
    account = {'email':email,'password':pwd}
    db.accounts.insert(account)
    return render_template('logBtn.html', accounts=[account,])


def delete_product_aftermath(product_name_path):
    try:
        shutil.rmtree(os.path.join(image_path, product_name_path))
    except Exception, e:
        print str(e)

@app.route('/common_delete', methods=['POST'])
def common_delete():
    _id = {'_id':ObjectId(request.form['_id'])}
    collection = request.form['collection']
    collection = db[session['db_name']][collection]
    if collection.name == 'products_table':
        product = collection.find_one(_id)
        delete_product_aftermath(product['product_name_path'])

    result = collection.remove(_id)
    return 'success' 

@app.route('/create_order', methods=['POST'])
def create_order():
    cid = request.form['customer_id']
    if not cid:
        return 'no customer id', 403
    data = {
        'customer_id': cid,
        'goods_name': request.form['goods_name'],
        'quantity': request.form['quantity'],
        'unit_price': request.form['unit_price'],
        'shipping_cost': request.form['shipping_cost'],
    }
    cdb = db[session['db_name']]
    customer = cdb.customers.find_one({'_id':ObjectId(cid)})
    data.update({'customer_name':customer['name']})
    cdb.orders.insert(data)
    return render_template('order_info.html', orders=[data])

@app.route('/customer_order', methods=['POST'])
def customer_order():
    orders = db[session['db_name']].orders.find() 
    if not orders.count():
        return 'no orders right now'
    return render_template('order_info.html', orders=orders)
    
@app.route('/customer_info', methods=['POST'])
def customer_info():
    customers = db[session['db_name']].customers.find()
    if not customers.count():
        return 'Currently no customer '
    return render_template('customer_info.html', customers=customers)

@app.route('/create_customer', methods=['POST'])
def create_customer():
    data = {
        'name': request.form['name'],
        'email': request.form['email'],
        'telephone': request.form['telephone'],
        'country': request.form['country'],
        'address': request.form['address'],
        'pcode': request.form['pcode']
    }
    db[session['db_name']].customers.insert(data)
    return render_template('customer_info.html', customers=[data])

@app.route('/monthly_profit', methods=['POST'])
def monthly_profit():
    rate = request.form['exchange_rate']
    titles = ['日期', '客户性质', '客户邮箱地址', '客户名字', '国家',
              '收款金额(USD)', '付款方式', '折RMB实际收款额 (%s)' % rate,
              '注明采购的商品名称及数量及单价', '货物成本', '包裹总重量',
              '运费', '净毛利', '跟踪号', '货代公司', '发货日期']

@app.route('/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.getcwd(), filename)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')
