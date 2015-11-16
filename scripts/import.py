'''
Created on Sep 11, 2012

@author: ionut
'''

import logging
import os
import tornado.httpclient
from functools import partial
from random import shuffle
from tornado import ioloop

import settings
import utils

BASE_DIR = '/media/ionut/Poze'
NUM_PROCS = 4
current_file_count = 0
client = tornado.httpclient.AsyncHTTPClient()

logging.basicConfig(level=logging.INFO, #filename='import.log', 
    format='[%(asctime)s] - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

files = []
for (dirpath, dirnames, filenames) in os.walk(BASE_DIR):
    for filename in filenames:
        if not filename.lower().endswith(".jpg") and not filename.lower().endswith(".jpeg"):
#             logging.info('skipping %s from %s' % (filename, dirpath))
            continue
        files.append(os.path.join(dirpath, filename))
shuffle(files)
logging.info('found %d files' % len(files))    

def _on_add(filename, response):
    global current_file_count
    current_file_count -= 1
    if response.error:
        logging.error('could not process file %s error : %s' % (filename, response.error))
    elif response.body != 'already imported':
        logging.info('processed %s, result: %s' % (filename, response.body))
    _import()
    
def _import():
    
    global current_file_count
    while len(files) > 0 and current_file_count < NUM_PROCS:
        filename = files.pop()
        current_file_count += 1
#         logging.info('processing %s' % (filename))
        with open(filename, 'r') as f: 
            filedata = f.read()
        f = ('image', os.path.split(filename)[1], filedata)
        content_type, body = utils.encode_multipart_formdata([('secret', settings.SECRET)], [f])
        headers = {'Content-Type': content_type} 
        req = tornado.httpclient.HTTPRequest(url='http://photomap.local/upload/', 
                                             method="POST", 
                                             body=body, 
                                             headers=headers) 
        client.fetch(req, callback=partial(_on_add, filename)) 
    
    if not files:
        logging.info('stopping IOLoop')
        ioloop.IOLoop.instance().stop()
        return 

logging.info('starting ioloop')
_import()
ioloop.IOLoop.instance().start()