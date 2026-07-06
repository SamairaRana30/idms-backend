from flask import Blueprint, request, jsonify
import jwt
import os
from datetime import datetime
from supabase import create_client

voting_bp = Blueprint('voting', __name__)

JWT_SECRET = os.getenv('JWT_SECRET')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def get_sb():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_current_user(req):
    auth = req.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None, 'Missing token'
    token = auth.split(' ')[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, 'Token expired'
    except Exception:
        return None, 'Invalid token'

def ok(data, code=200):
    return jsonify({'status': 'success', 'data': data}), code

def err(msg, code=400):
    return jsonify({'status': 'error', 'message': msg}), code

# ── SETUP ────────────────────────────────────────────────────────────────────
@voting_bp.route('/ballots/setup', methods=['POST'])
def setup_tables():
    return ok({'message': 'Tables already created in Supabase SQL Editor'})

# ── BALLOTS ──────────────────────────────────────────────────────────────────
@voting_bp.route('/ballots', methods=['GET'])
def get_ballots():
    user, error = get_current_user(request)
    if error: return err(error, 401)
    sb = get_sb()
    if user.get('role') == 'admin':
        res = sb.schema('idms_dev').table('ballots').select('*').order('created_at', desc=True).execute()
    else:
        now = datetime.now().isoformat()
        res = sb.schema('idms_dev').table('ballots').select('*').eq('status', 'published').lte('start_date', now).gte('end_date', now).execute()
    return ok(res.data)

@voting_bp.route('/ballots/<int:ballot_id>', methods=['GET'])
def get_ballot(ballot_id):
    user, error = get_current_user(request)
    if error: return err(error, 401)
    sb = get_sb()
    res = sb.schema('idms_dev').table('ballots').select('*').eq('id', ballot_id).execute()
    if not res.data: return err('Ballot not found', 404)
    ballot = res.data[0]
    opts = sb.schema('idms_dev').table('ballot_options').select('*').eq('ballot_id', ballot_id).order('position').execute()
    ballot['options'] = opts.data
    return ok(ballot)

@voting_bp.route('/ballots', methods=['POST'])
def create_ballot():
    user, error = get_current_user(request)
    if error: return err(error, 401)
    if user.get('role') != 'admin': return err('Admin only', 403)
    data = request.json
    if not data.get('title'): return err('Title required')
    options = data.get('options', [])
    if len(options) < 2: return err('Minimum 2 options required')
    if len(options) > 10: return err('Maximum 10 options allowed')
    sb = get_sb()
    ballot_res = sb.schema('idms_dev').table('ballots').insert({
        'title': data['title'],
        'description': data.get('description', ''),
        'ballot_type': data.get('ballot_type', 'single'),
        'status': data.get('status', 'draft'),
        'start_date': data.get('start_date'),
        'end_date': data.get('end_date'),
        'created_by': user.get('user_id')
    }).execute()
    ballot_id = ballot_res.data[0]['id']
    for i, opt in enumerate(options):
        text = opt.get('option_text', opt) if isinstance(opt, dict) else opt
        sb.schema('idms_dev').table('ballot_options').insert({
            'ballot_id': ballot_id,
            'option_text': text,
            'position': i
        }).execute()
    return ok({'ballot_id': ballot_id, 'message': 'Ballot created'}, 201)

@voting_bp.route('/ballots/<int:ballot_id>', methods=['PUT'])
def update_ballot(ballot_id):
    user, error = get_current_user(request)
    if error: return err(error, 401)
    if user.get('role') != 'admin': return err('Admin only', 403)
    data = request.json
    sb = get_sb()
    sb.schema('idms_dev').table('ballots').update({
        'title': data.get('title'),
        'description': data.get('description'),
        'ballot_type': data.get('ballot_type'),
        'status': data.get('status'),
        'start_date': data.get('start_date'),
        'end_date': data.get('end_date')
    }).eq('id', ballot_id).execute()
    return ok({'message': 'Ballot updated'})

@voting_bp.route('/ballots/<int:ballot_id>', methods=['DELETE'])
def delete_ballot(ballot_id):
    user, error = get_current_user(request)
    if error: return err(error, 401)
    if user.get('role') != 'admin': return err('Admin only', 403)
    sb = get_sb()
    sb.schema('idms_dev').table('ballots').delete().eq('id', ballot_id).execute()
    return ok({'message': 'Ballot deleted'})

# ── VOTES ────────────────────────────────────────────────────────────────────
@voting_bp.route('/votes', methods=['POST'])
def cast_vote():
    user, error = get_current_user(request)
    if error: return err(error, 401)
    data = request.json
    ballot_id = data.get('ballot_id')
    option_id = data.get('option_id')
    if not ballot_id or not option_id: return err('ballot_id and option_id required')
    sb = get_sb()
    ballot_res = sb.schema('idms_dev').table('ballots').select('*').eq('id', ballot_id).execute()
    if not ballot_res.data: return err('Ballot not found', 404)
    ballot = ballot_res.data[0]
    if ballot['status'] != 'published': return err('Ballot is not open for voting')
    now = datetime.now().isoformat()
    if ballot['start_date'] and now < ballot['start_date']: return err('Ballot has not started yet')
    if ballot['end_date'] and now > ballot['end_date']: return err('Ballot has already closed')
    existing = sb.schema('idms_dev').table('votes').select('id').eq('ballot_id', ballot_id).eq('member_id', user['user_id']).execute()
    if existing.data: return err('You have already voted on this ballot', 409)
    sb.schema('idms_dev').table('votes').insert({
        'ballot_id': ballot_id,
        'option_id': option_id,
        'member_id': user['user_id']
    }).execute()
    return ok({'message': 'Vote cast successfully'}, 201)

# ── RESULTS ──────────────────────────────────────────────────────────────────
@voting_bp.route('/ballots/<int:ballot_id>/results', methods=['GET'])
def get_results(ballot_id):
    user, error = get_current_user(request)
    if error: return err(error, 401)
    sb = get_sb()
    ballot_res = sb.schema('idms_dev').table('ballots').select('*').eq('id', ballot_id).execute()
    if not ballot_res.data: return err('Ballot not found', 404)
    ballot = ballot_res.data[0]
    if user.get('role') != 'admin' and ballot['status'] != 'closed':
        return err('Results only available after ballot closes', 403)
    opts = sb.schema('idms_dev').table('ballot_options').select('*').eq('ballot_id', ballot_id).order('position').execute()
    votes = sb.schema('idms_dev').table('votes').select('*').eq('ballot_id', ballot_id).execute()
    total_votes = len(votes.data)
    results = []
    for opt in opts.data:
        count = sum(1 for v in votes.data if v['option_id'] == opt['id'])
        pct = round((count / total_votes * 100), 2) if total_votes > 0 else 0
        results.append({
            'option_id': opt['id'],
            'option_text': opt['option_text'],
            'vote_count': count,
            'percentage': pct
        })
    return ok({
        'ballot_id': ballot_id,
        'ballot_title': ballot['title'],
        'status': ballot['status'],
        'total_votes': total_votes,
        'results': results
    })