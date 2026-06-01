from flask import jsonify


def success(data=None, message=None, status=200):
    body = {'success': True}
    if message:
        body['message'] = message
    if data is not None:
        body.update(data)
    return jsonify(body), status


def error(message, status=400):
    return jsonify({'success': False, 'error': message}), status
