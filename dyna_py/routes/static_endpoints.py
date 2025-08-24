from flask import send_from_directory, abort
import os

PLUGINS_ROOT = os.path.abspath('./public/plugins')

def serve_plugin_file(subpath):
    full = os.path.join(PLUGINS_ROOT, subpath)
    if not os.path.isfile(full):
        abort(404)
    
    if full.endswith('.js'):
        return send_from_directory(PLUGINS_ROOT, subpath, mimetype='text/javascript')
    if full.endswith('.json'):
        return send_from_directory(PLUGINS_ROOT, subpath, mimetype='application/json')
    
    return send_from_directory(PLUGINS_ROOT, subpath)
