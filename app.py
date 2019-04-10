import hashlib
import os
import shutil

from flask import Flask, render_template, session, redirect, request, send_file, url_for
from werkzeug.utils import secure_filename

import common

app = Flask(__name__)
app.secret_key = 'HomeWorkSystem'  # should be random.

DATA_DIR = './data'

PATH_USERS = '%s/users.json' % DATA_DIR
PATH_HOMEWORK = '%s/homework.json' % DATA_DIR

STORAGE_DIR = '%s/storage' % DATA_DIR

data_users = common.load_json(PATH_USERS, {})  # type: dict
data_homework = common.load_json(PATH_HOMEWORK, [])  # type: list


@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    current_user = session.get('user')  # type: dict
    if current_user is not None:
        t_data = {
            'user': current_user,
            'homework': enumerate(data_homework),
        }
        return render_template('index.html', **t_data)
    else:
        return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        form = request.form
        if form['username'] not in data_users.keys():
            data_users[form['username']] = {
                'username': form['username'],
                'password': form['password'],
                'is_admin': 'is_admin' in form,
            }
            common.save_json(PATH_USERS, data_users)
        else:
            pass

        return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        form = request.form
        for username, user in data_users.items():
            if form['username'] == username and form['password'] == user['password']:
                session['user'] = user
                return redirect('/index')

        return redirect('/login')


@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect('/login')


@app.route('/set_homework', methods=['GET', 'POST'])
@app.route('/set_homework/<int:h_id>', methods=['GET', 'POST'])
def set_homework(h_id=None):
    current_user = session.get('user')  # type: dict
    if not current_user['is_admin']:
        return redirect('/login')

    if request.method == 'GET':
        t_data = {
            'item': data_homework[h_id] if h_id is not None else None,
        }
        return render_template('set_homework.html', **t_data)
    elif request.method == 'POST':
        form = request.form
        h_data = {
            'name': form['name'],
            'description': form['description'],
        }

        if h_id is None or not 0 <= h_id < len(data_homework):
            h_data['key'] = hashlib.md5(os.urandom(32)).hexdigest()  # use by storage.
            os.makedirs('%s/%s' % (STORAGE_DIR, h_data['key']))
            data_homework.append(h_data)
        else:
            data_homework[h_id].update(h_data)

        common.save_json(PATH_HOMEWORK, data_homework)
        return redirect('/index')


@app.route('/submit_homework/<int:h_id>', methods=['GET', 'POST'])
def submit_homework(h_id):
    current_user = session.get('user')  # type: dict
    if request.method == 'GET':
        t_data = {
            'user': current_user,
            'item': data_homework[h_id],
        }
        return render_template('submit_homework.html', **t_data)
    elif request.method == 'POST':
        files = request.files
        file = files['file']
        if file.filename != '':
            h_data = data_homework[h_id]  # type: dict

            f_data = {
                'name': secure_filename(file.filename),
                'user': current_user['username'],
                'file': hashlib.md5(os.urandom(32)).hexdigest(),
            }

            os.makedirs('%s/%s' % (STORAGE_DIR, h_data['key']), exist_ok=True)
            file.save('%s/%s/%s' % (STORAGE_DIR, h_data['key'], f_data['file']))

            p_storage_info = '%s/%s/info.json' % (STORAGE_DIR, h_data['key'])
            storage_info = common.load_json(p_storage_info, [])  # type: list
            storage_info.append(f_data)
            common.save_json(p_storage_info, storage_info)

            return redirect('/index')
        else:
            return redirect(request.url)


@app.route('/remove_homework/<int:h_id>', methods=['GET'])
def remove_homework(h_id):
    current_user = session.get('user')  # type: dict
    if not current_user['is_admin']:
        return redirect('/login')

    h_data = data_homework.pop(h_id)
    shutil.rmtree('%s/%s' % (STORAGE_DIR, h_data['key']))
    common.save_json(PATH_HOMEWORK, data_homework)
    return redirect('/index')


@app.route('/view_homework/<int:h_id>', methods=['GET'])
def view_homework(h_id):
    current_user = session.get('user')  # type: dict
    if not current_user['is_admin']:
        return redirect('/login')

    h_data = data_homework[h_id]  # type: dict
    p_storage_info = '%s/%s/info.json' % (STORAGE_DIR, h_data['key'])
    storage_info = common.load_json(p_storage_info, [])  # type: list
    t_data = {
        'user': current_user,
        'item': data_homework[h_id],
        'item_id': h_id,
        'files': enumerate(storage_info),
    }
    return render_template('view_homework.html', **t_data)


@app.route('/download_homework/<int:h_id>/<int:f_id>', methods=['GET'])
def download_homework(h_id, f_id):
    current_user = session.get('user')  # type: dict
    if not current_user['is_admin']:
        return redirect('/login')

    h_data = data_homework[h_id]  # type: dict
    p_storage_info = '%s/%s/info.json' % (STORAGE_DIR, h_data['key'])
    storage_info = common.load_json(p_storage_info, [])  # type: list
    f_data = storage_info[f_id]  # type: dict
    p_file = '%s/%s/%s' % (STORAGE_DIR, h_data['key'], f_data['file'])

    return send_file(p_file, attachment_filename=f_data['name'], as_attachment=True)


@app.route('/delete_homework/<int:h_id>/<int:f_id>', methods=['GET'])
def delete_homework(h_id, f_id):
    current_user = session.get('user')  # type: dict
    if not current_user['is_admin']:
        return redirect('/login')

    h_data = data_homework[h_id]  # type: dict
    p_storage_info = '%s/%s/info.json' % (STORAGE_DIR, h_data['key'])
    storage_info = common.load_json(p_storage_info, [])  # type: list
    f_data = storage_info.pop(f_id)  # type: dict
    common.save_json(p_storage_info, storage_info)
    p_file = '%s/%s/%s' % (STORAGE_DIR, h_data['key'], f_data['file'])
    os.unlink(p_file)

    return redirect(url_for('view_homework', h_id=h_id))


if __name__ == '__main__':
    app.run()
