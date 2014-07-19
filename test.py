from splinter import Browser

dc = {'chromeOptions': {'args':['--user-data-dir=e:/hope/chrome']}}
dc = {'chromeOptions': {'args': ['--user-data-dir=e:/hope/chrome'], 'extensions': []}, 'browserName': 'chrome', 'version': '', 'platform': 'ANY', 'javascriptEnabled': True}
b = Browser('chrome', desired_capabilities=dc)