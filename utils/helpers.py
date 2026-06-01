from flask import jsonify


def success(data=None, status=200):
    body = {'success': True}
    if data is not None:
        body['data'] = data
    return jsonify(body), status


def error(message, status=400):
    return jsonify({'success': False, 'error': message, 'code': status}), status


def paginate(request):
    try:
        page  = max(1, int(request.args.get('page', 1)))
        limit = min(100, max(1, int(request.args.get('limit', 20))))
    except (TypeError, ValueError):
        page, limit = 1, 20
    offset = (page - 1) * limit
    return page, limit, offset
