#!/usr/bin/env python

import flask
import io
import os
import zipfile
from flask import jsonify
from eve import Eve
from eve.auth import BasicAuth, requires_auth

# location where repositories are stored
REPOSITORY_PATH = '/var/lib/fende/'

# verify status of os.system call
verify_status = lambda status: True if status == 0 else False


class FENDEAuth(BasicAuth):
    """username:password@link"""

    def check_auth(
            self, username, password, allowed_roles,
            resource, method):
        return username == 'f&=gAt&ejuTHuqUKafaKe=2*' and \
               password == 'bUpAnebeC$ac@4asaph#DrEb'


app = Eve(auth=FENDEAuth)


@app.route('/move/<name_id>')
@requires_auth(FENDEAuth)
def move_repository(name_id):
    """move VNF repository."""

    path = REPOSITORY_PATH + 'temp/' + name_id
    final_path = REPOSITORY_PATH + name_id
    status = os.system("mv %s %s" % (path, final_path))
    return jsonify({'success': verify_status(status)})


@app.route('/repository/create/<name_id>/<path:url>')
@requires_auth(FENDEAuth)
def create_repository(name_id, url):
    """Clone VNF repository."""

    path = REPOSITORY_PATH + name_id
    status = os.system("git clone %s %s" % (url, path))
    return jsonify({'success': verify_status(status)})


@app.route('/repository/update/<name_id>')
@requires_auth(FENDEAuth)
def update_repository(name_id):
    """Update local repository."""

    path = REPOSITORY_PATH + name_id
    os.system("git -C %s reset --hard" % path)
    status = os.system("git -C %s pull" % path)
    return jsonify({'success': verify_status(status)})


@app.route('/vnfd/<name_id>')
@requires_auth(FENDEAuth)
def get_vnfd(name_id):
    """Read vnfd file and return the content."""

    vnfd_path = REPOSITORY_PATH + '%s/Descriptors/vnfd.json' % name_id
    with open(vnfd_path) as vnfd_file:
        vnfd_data = vnfd_file.read()

    return jsonify({'vnfd_data': vnfd_data})


@app.route('/nsd/<name_id>')
@requires_auth(FENDEAuth)
def get_nsd(name_id):
    """Read nsd file and return the content."""

    nsd_path = REPOSITORY_PATH + '%s/Descriptors/nsd.json' % name_id
    with open(nsd_path) as nsd_file:
        nsd_data = nsd_file.read()

    return jsonify({'nsd_data': nsd_data})


@app.route('/vnf/function/<name_id>')
@requires_auth(FENDEAuth)
def get_function(name_id):
    """Read function file and return the content."""

    function_path = REPOSITORY_PATH + '%s/Source/function.click' % name_id
    with open(function_path) as function_file:
        function_data = function_file.read()

    return jsonify({'function_data': function_data})


@app.route('/vnf/repository/<name_id>')
@requires_auth(FENDEAuth)
def get_repository(name_id):
    """Compress and return the entire repository."""

    function_path = REPOSITORY_PATH + name_id
    zip_name = '/tmp/%s.zip' % name_id
    zipped_repository = zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED)

    for root, subdirs, files in os.walk(function_path):
        # exclude .git from zipped repository
        if '.git' in subdirs:
            subdirs.remove('.git')

        for repo_file in files:
            file_path = os.path.join(root, repo_file)
            zipped_repository.write(file_path, file_path[len(function_path):])

    zipped_repository.close()

    return jsonify({'repository_path': zip_name})


@app.route('/config/<name_id>')
@requires_auth(FENDEAuth)
def get_config(name_id):
    """Read config file and return the content."""

    config_path = REPOSITORY_PATH + '%s/Configs/config.json' % name_id
    with open(config_path) as config_file:
        config_data = config_file.read()

    return jsonify({'config_data': config_data})


@app.route('/lifecycle/<name_id>')
@requires_auth(FENDEAuth)
def get_lifecycle(name_id):
    """Read lifecycle file and return the content."""

    lifecycle_path = REPOSITORY_PATH + '%s/Lifecycle/lifecycle.json' % name_id
    with open(lifecycle_path) as lifecycle_file:
        lifecycle_data = lifecycle_file.read()

    return jsonify({'lifecycle_data': lifecycle_data})


@app.route('/lifecycle/<name_id>/<script_name>')
@requires_auth(FENDEAuth)
def get_script(name_id, script_name):
    """Read lifecycle script file and return the content."""

    script_path = REPOSITORY_PATH + '%s/Management/Scripts/%s.sh' % (name_id, script_name)
    with open(script_path) as script_file:
        script_data = script_file.read()


@app.route('/management/<name_id>')
@requires_auth(FENDEAuth)
def get_management(name_id):
    """Read management file and return the content."""

    management_path = REPOSITORY_PATH + '%s/Management/management.json' % name_id
    with open(management_path) as management_file:
        management_data = management_file.read()

    return jsonify({'management_data': management_data})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
