import os, shutil
from flask import Flask, render_template, send_from_directory, request
from flask import redirect, url_for, jsonify, session
from pymongo import MongoClient
from bson import ObjectId
from bse import BSCollector, collect_names, valid_path

app = Flask(__name__)
db = MongoClient()['yason']
image_path = os.path.join(os.getcwd(), 'images')

@app.route('/')
def index():
    kws = db.products_table.distinct('key_words')
    accounts = db.accounts.find()
    return render_template('index.html', kws=kws, accounts=accounts)

# @app.route('/login')
# def login():
#     condition = {'username':username, 'password':password}
#     user = db.users.find_one(condition)
    # if user:

@app.route('/list_product_by_kw', methods=['POST'])
def list_product_by_kw():
    kws = request.form['keywords']
    query = db.products_table.find({'key_words':kws})
    if not query.count():
        return 'No products under this keywords'
    return render_template('product.html', products=query)

@app.route('/add_keywords', methods=['POST'])
def add_keyword():
    kw = request.form['key_words'].split(':')
    data = {
        'search_keyword': kw[0],
        'keyword': kw[1],
        'company_cnt': '0',
        'showwin_cnt': '0',
        'hotness': '0'
    }
    result = db.key_words_table.insert(data)
    return jsonify({'ok':1})

@app.route('/check_keyword', methods=['POST'])
def check_keyword():
    keywords = request.form['keywords']
    count = db.key_words_table.find({'search_keyword':keywords}).count()
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

@app.route('/change_product_name', methods=['POST'])
def change_product_name():
    pn = request.form['product_name'].title().strip()
    pn = valid_path(pn)

    pid = {'_id':ObjectId(request.form['pid'])}
    product = db.products_table.find_one(pid)
    old = os.path.join(image_path, product['product_name_path'])
    new = os.path.join(image_path, pn)
    if os.path.exists(old):
        os.rename(old, new)

    old_file_path = os.path.join(new, product['product_name_path'] + '.jpg')
    if os.path.exists(old_file_path):
        new_file_path = os.path.join(new, pn + '.jpg')
        os.rename(old_file_path, new_file_path)

    result = db.products_table.update(pid, {'$set':{'product_name':pn, 'product_name_path':pn}})
    return jsonify(result)

@app.route('/rich', methods=['POST'])
def recollect_rich_desc():
    pid = {'_id':ObjectId(request.form['pid'])}
    product = db.products_table.find_one(pid)
    bsc = BSCollector(product['url'], image_path, product['product_name'])
    bsc.collect_rich_descs()
    old_path = os.path.join(image_path, product['product_name_path'])
    if os.path.exists(old_path):
        shutil.rmtree(old_path)
    bsc.collect_pics()
    data = {'rich_descs':bsc.rich_descs}
    result = db.products_table.update(pid, {'$set':data})
    return jsonify(result)

@app.route('/product', methods=['POST'])
def upload_product():
    url = request.form['url']
    kws = request.form['key_words']
    index = request.form['index']
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
    pid = db.products_table.insert(data)
    p = db.products_table.find_one({'_id':pid})
    return render_template('product.html', products=[p], index=index)


@app.route('/change_key_words', methods=['POST'])
def change_key_words():
    new_kw = request.form['key_words']
    pid = {'_id':ObjectId(request.form['pid'])}
    db.products_table.update(pid, {'$set':{'key_words':new_kw}})
    return jsonify({'success':True})

@app.route('/list_key_words', methods=['POST'])
def list_key_words():
    key_words = request.form['key_words']
    kws = db.key_words_table.find({'search_keyword':key_words})
    return render_template('keywords.html', keywords=kws)

@app.route('/collect_variant_names', methods=['POST'])
def collect_variant_names():
    product_name = request.form['product_name']
    names = collect_names(product_name)
    data = []
    for name in names:
        data.append({'product_name':product_name, 'variant':name})
    result = db.product_name_table.insert(data)
    return jsonify({'ok':len(result)})

@app.route('/set_account', methods=['POST'])
def create_account():
    email = request.form['email']
    result = db.accounts.find({'email':email}).count()
    if result:
        return ''
    pwd = request.form['password']
    account = {'email':email,'password':pwd}
    db.accounts.insert(account)
    return render_template('logBtn.html', accounts=[account,])


@app.route('/delete_product', methods=['POST'])
def delete_product():
    pid = ObjectId(request.form['pid'])
    product = db.products_table.find_one(pid)
    result = db.products_table.remove({'_id':pid})
    try:
        shutil.rmtree(os.path.join(image_path, product['product_name_path']))
    except Exception, e:
        print e
    return jsonify(result)

@app.route('/order', methods=['POST'])
def create_order():
    pass
    
@app.route('/customer', methods=['POST'])
def customer_info():
    data = {
        'name': request.form['name'],
        'email': request.form['email'],
        'telephone': request.form['telephone'],
        'country': request.form['country'],
        'address': request.form['country'],
        'pcode': request.form['pcode']
    }
    db.customers.insert(data)
    return ''

@app.route('/profit_table', methods=['POST'])
def create_profit_table():
    pass

@app.route('/<path:filename>')
def serve_js(filename):
    return send_from_directory(os.getcwd(), filename)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')
