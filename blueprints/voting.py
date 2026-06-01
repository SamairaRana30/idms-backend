from flask import Blueprint, request, g
from psycopg2.extras import RealDictCursor

from middleware.auth import require_auth, require_admin
from utils.supabase_client import get_db, close_db
from utils.helpers import success, error, paginate
from utils.audit import log_action

voting_bp = Blueprint('voting', __name__, url_prefix='/api/v1/ballots')


@voting_bp.route('', methods=['GET'])
@require_auth
def list_ballots():
    page, limit, offset = paginate(request)
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT COUNT(*) FROM ballots")
        total = cur.fetchone()['count']

        cur.execute(
            """SELECT b.id, b.title, b.description, b.status,
                      b.start_date, b.end_date, b.created_at,
                      u.full_name AS created_by_name
               FROM ballots b
               LEFT JOIN users u ON u.id::text = b.created_by
               ORDER BY b.created_at DESC LIMIT %s OFFSET %s""",
            (limit, offset)
        )
        ballots = [dict(r) | {'id': str(r['id'])} for r in cur.fetchall()]
        return success({'ballots': ballots, 'total': total, 'page': page})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@voting_bp.route('', methods=['POST'])
@require_auth
@require_admin
def create_ballot():
    data        = request.get_json() or {}
    title       = data.get('title', '').strip()
    description = data.get('description', '')
    start_date  = data.get('start_date')
    end_date    = data.get('end_date')
    options     = [o.strip() for o in data.get('options', []) if str(o).strip()]

    if not title:
        return error('Title is required', 400)
    if len(options) < 2:
        return error('At least 2 options are required', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO ballots (title, description, created_by, start_date, end_date) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (title, description, g.user['user_id'], start_date, end_date)
        )
        ballot_id = cur.fetchone()[0]

        for opt in options:
            cur.execute(
                "INSERT INTO ballot_options (ballot_id, text) VALUES (%s, %s)",
                (ballot_id, opt)
            )
        conn.commit()
        log_action('ballot.create', 'ballot', str(ballot_id), g.user['user_id'], {'title': title})
        return success({'ballot_id': str(ballot_id)}, 201)
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@voting_bp.route('/<ballot_id>', methods=['GET'])
@require_auth
def get_ballot(ballot_id):
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """SELECT b.*, u.full_name AS created_by_name
               FROM ballots b
               LEFT JOIN users u ON u.id::text = b.created_by
               WHERE b.id = %s""",
            (ballot_id,)
        )
        ballot = cur.fetchone()
        if not ballot:
            return error('Ballot not found', 404)

        cur.execute(
            "SELECT id, text FROM ballot_options WHERE ballot_id = %s ORDER BY created_at",
            (ballot_id,)
        )
        options = [dict(o) | {'id': str(o['id'])} for o in cur.fetchall()]

        cur.execute(
            "SELECT option_id, COUNT(*) AS cnt FROM votes WHERE ballot_id = %s GROUP BY option_id",
            (ballot_id,)
        )
        counts = {str(r['option_id']): int(r['cnt']) for r in cur.fetchall()}

        cur.execute(
            "SELECT id FROM votes WHERE ballot_id = %s AND user_id = %s",
            (ballot_id, g.user['user_id'])
        )
        has_voted = cur.fetchone() is not None

        return success({
            'ballot':      dict(ballot) | {'id': str(ballot['id'])},
            'options':     options,
            'vote_counts': counts,
            'has_voted':   has_voted
        })
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@voting_bp.route('/<ballot_id>', methods=['DELETE'])
@require_auth
@require_admin
def delete_ballot(ballot_id):
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("DELETE FROM ballot_options WHERE ballot_id = %s", (ballot_id,))
        cur.execute("DELETE FROM votes WHERE ballot_id = %s", (ballot_id,))
        cur.execute("DELETE FROM ballots WHERE id = %s RETURNING id", (ballot_id,))
        if not cur.fetchone():
            conn.rollback()
            return error('Ballot not found', 404)
        conn.commit()
        log_action('ballot.delete', 'ballot', ballot_id, g.user['user_id'])
        return success({'message': 'Ballot deleted'})
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@voting_bp.route('/<ballot_id>/open', methods=['PUT'])
@require_auth
@require_admin
def open_ballot(ballot_id):
    return _set_ballot_status(ballot_id, 'open')


@voting_bp.route('/<ballot_id>/close', methods=['PUT'])
@require_auth
@require_admin
def close_ballot(ballot_id):
    return _set_ballot_status(ballot_id, 'closed')


def _set_ballot_status(ballot_id, status):
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("UPDATE ballots SET status = %s WHERE id = %s RETURNING id", (status, ballot_id))
        if not cur.fetchone():
            conn.rollback()
            return error('Ballot not found', 404)
        conn.commit()
        log_action(f'ballot.{status}', 'ballot', ballot_id, g.user['user_id'])
        return success({'message': f'Ballot is now {status}'})
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@voting_bp.route('/<ballot_id>/vote', methods=['POST'])
@require_auth
def cast_vote(ballot_id):
    data      = request.get_json() or {}
    option_id = data.get('option_id')
    if not option_id:
        return error('option_id is required', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT status FROM ballots WHERE id = %s", (ballot_id,))
        ballot = cur.fetchone()
        if not ballot:
            return error('Ballot not found', 404)
        if ballot['status'] != 'open':
            return error('Ballot is not open for voting', 400)

        cur.execute(
            "SELECT id FROM ballot_options WHERE id = %s AND ballot_id = %s",
            (option_id, ballot_id)
        )
        if not cur.fetchone():
            return error('Invalid option for this ballot', 400)

        cur.execute(
            "INSERT INTO votes (ballot_id, option_id, user_id) VALUES (%s, %s, %s)",
            (ballot_id, option_id, g.user['user_id'])
        )
        conn.commit()
        return success({'message': 'Vote recorded'})
    except Exception as e:
        if conn:
            conn.rollback()
        if 'unique' in str(e).lower() or '23505' in str(e):
            return error('You have already voted on this ballot', 409)
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@voting_bp.route('/<ballot_id>/results', methods=['GET'])
@require_auth
def get_results(ballot_id):
    is_admin = g.user.get('role') == 'admin'
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT * FROM ballots WHERE id = %s", (ballot_id,))
        ballot = cur.fetchone()
        if not ballot:
            return error('Ballot not found', 404)
        if ballot['status'] != 'closed' and not is_admin:
            return error('Results are only available after the ballot is closed', 403)

        cur.execute(
            "SELECT id, text FROM ballot_options WHERE ballot_id = %s ORDER BY created_at",
            (ballot_id,)
        )
        options = [dict(o) | {'id': str(o['id'])} for o in cur.fetchall()]

        cur.execute("SELECT COUNT(*) FROM votes WHERE ballot_id = %s", (ballot_id,))
        total_votes = int(cur.fetchone()['count'])

        cur.execute("SELECT COUNT(*) FROM users WHERE is_active = true")
        total_eligible = int(cur.fetchone()['count'])

        results = []
        for opt in options:
            cur.execute(
                "SELECT COUNT(*) FROM votes WHERE ballot_id = %s AND option_id = %s",
                (ballot_id, opt['id'])
            )
            cnt = int(cur.fetchone()['count'])
            pct = round(cnt / total_votes * 100, 1) if total_votes > 0 else 0
            results.append({**opt, 'votes': cnt, 'percentage': pct})

        turnout = round(total_votes / total_eligible * 100, 1) if total_eligible > 0 else 0

        return success({
            'ballot':          dict(ballot) | {'id': str(ballot['id'])},
            'results':         results,
            'total_votes':     total_votes,
            'total_eligible':  total_eligible,
            'turnout_percent': turnout
        })
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)
