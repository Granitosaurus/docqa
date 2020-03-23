import json
import os
import sys
from collections import defaultdict
from datetime import timedelta
from pathlib import Path
from random import shuffle

from tinydb.database import Table
from werkzeug.utils import secure_filename

from flask import Flask, request, render_template, redirect, flash, url_for, abort
from tinydb import TinyDB, Query
import requests
import requests_cache

from docqa.templating import url_add_listq, url_rm_listq, url_get_listq, url_sub, url_inc, url_index, \
    url_add
from docqa.utils import is_url

requests_cache.install_cache(expire_after=timedelta(hours=24))

app = Flask(__name__)
DATA_DIR = Path(sys.path[0]) / 'data'
app.config['DATA_DIR'] = DATA_DIR
app.config['DB'] = defaultdict()


def get_db(file) -> Table:
    DB = app.config['DB']
    if file not in DB:
        print(f'opening DB for: {file}')
        DB[file] = TinyDB(DATA_DIR / file, sort_keys=True, indent=2, separators=(',', ': '))
    return DB[file]


def get_files():
    return os.listdir(DATA_DIR)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'json'


def import_file(filename, randomize=True):
    """
    Import json file to database.
    the import json must be a list of objects
    every object gets `_docqa` meta field attached with `status` and `comments` keys.
    """
    filename = str(filename)
    with open(filename) as f:
        data = json.loads(f.read())
    os.remove(filename)
    db = get_db(filename)
    if randomize:
        shuffle(data)
    for value in data:
        value['_docqa'] = {
            'status': 'new',
            'comments': {},
        }
        print(db.insert(value))


@app.route('/')
def hello():
    return render_template('index.html', files=get_files())


@app.route('/qa/<file>/<doc_id>/<key>', methods=['POST'])
def qa_comment(file, doc_id, key):
    comment = request.form['comment']
    doc_id = int(doc_id)
    db = get_db(file)
    doc = db.get(doc_id=doc_id)
    doc['_docqa']['comments'][key] = comment
    if db.write_back([doc], doc_ids=[doc_id]):
        print(f'added comment: "{key}": "{comment}" to doc {doc_id}')
    return redirect(request.referrer)


@app.route('/qa/<file>/new')
def qa_new(file):
    after = int(request.args.get('after', 0))
    Doc = Query()
    db = get_db(file)
    docs = db.search(Doc._docqa.status == 'new')
    try:
        doc = next(doc for doc in docs if doc.doc_id > after)
    except StopIteration:
        if request.referrer:
            return redirect(request.referrer)
        else:
            return redirect(url_for('show', file=file, status='fail'))
    doc_id = doc.doc_id
    pass_args = {k: v for k, v in request.args.items() if k != 'after'}
    return redirect(url_for('qa', file=file, doc_id=doc_id, **pass_args))


@app.route('/show/<status>/<file>')
def show(file, status):
    db = get_db(file)
    docs = db.search(Query()._docqa.status == status)
    return render_template('show.html', docs=docs, file=file)


@app.route('/qa/<file>/<int:doc_id>/<status>')
def qa_status(file, doc_id, status):
    if status not in ['pass', 'fail', 'new', 'rm']:
        return abort(502)
    db = get_db(file)
    if status == 'rm':
        try:
            db.remove(doc_ids=[doc_id])
        except KeyError:  # maybe it's already gone
            pass
    else:
        doc = db.get(doc_id=doc_id)
        doc['_docqa']['status'] = status
        db.update(doc, doc_ids=[doc_id])
    new_doc = db.get(Query()._docqa.status == 'new')
    if not new_doc:
        if request.referrer:
            return redirect(request.referrer)
        else:
            return redirect(url_for('show', status=status, file=file))
    if request.referrer and '/show/' in request.referrer:
        return redirect(request.referrer)
    return redirect(url_for('qa', file=file, doc_id=new_doc.doc_id, **request.args))


@app.route('/qa/<file>/<int:doc_id>')
def qa(file, doc_id):
    # get document details
    db = get_db(file)
    if doc_id == 'new':
        Doc = Query()
        doc = db.get(Doc._docqa.status == 'new')
        doc_id = doc.doc_id
    else:
        doc = db.get(doc_id=doc_id)
    if doc and '_docqa' not in doc:
        doc['_docqa'] = {}
        db.update(doc, doc_ids=[doc_id])
    doc_qa = doc.pop('_docqa')

    # params
    display = request.args.get('display') or list(doc.keys())[0]

    # pagination
    # prev_url = url_inc(-1) if doc_id > 1 else ''
    # next_url = url_inc() if len(db) > doc_id else ''
    # rand_url = url_for('qa', file=file, doc_id=randint(1, len(db)), display=display, hide=hide)

    return render_template(
        'qa.html',
        doc=doc, doc_id=doc_id, doc_qa=doc_qa,
        file=file,
        # next_url=next_url, prev_url=prev_url, rand_url=rand_url,
        display=display,
    )


@app.route('/rm/<file>')
def remove_file(file):
    file = secure_filename(file)
    os.remove(app.config['DATA_DIR'] / file)
    return redirect('/')


@app.route('/add', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = app.config['DATA_DIR'] / secure_filename(file.filename)
            file.save(str(filename))
            import_file(filename)
            return redirect(url_for('upload_file',
                                    filename=filename))
    return redirect('/')


@app.route('/render')
def render():
    url = request.args.get('url')
    return requests.get(url).text


# Register templating functions
app.jinja_env.globals['url_add_listq'] = url_add_listq
app.jinja_env.globals['url_rm_listq'] = url_rm_listq
app.jinja_env.globals['url_get_listq'] = url_get_listq
app.jinja_env.globals['url_sub'] = url_sub
app.jinja_env.globals['url_inc'] = url_inc
app.jinja_env.globals['url_index'] = url_index
app.jinja_env.globals['url_add'] = url_add
app.jinja_env.globals['is_url'] = is_url
