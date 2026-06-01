from flask import Blueprint, request, g
from psycopg2.extras import RealDictCursor

from middleware.auth import token_required, admin_required
from utils.supabase_client import get_db, close_db
from utils.helpers import success, error

voting_bp = Blueprint('voting', __name__, url_prefix='/api/v1/voting')


@voting_bp.route('/ballots', methods=['GET'])
@token_required
def list_ballots():
    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """SELECT b.id, b.title, b.description, b.status, b.start_date, b.end_date, b.created_at,
                      u.full_name AS created_by_name
               FROM ballots b JOIN users u ON u.id = b.created_by
               ORDER BY b.created_at DESC"""
        )
        ballots = [dict(r) | {'id': str(r['id'])} for r in cur.fetchall()]
        return success({'ballots': ballots})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@voting_bp.route('/ballots', methods=['POST'])
@token_required
@admin_required
def create_ballot():
    data = request.get_json() or {}
    title      = data.get('title', '').strip()
    description= data.get('description', '')
    start_date = data.get('start_date')
    end_date   = data.get('end_date')
    options    = data.get('options', [])

    if not title or not options:
        return error('Title and at least one option are required', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO ballots (title, description, created_by, start_date, end_date)
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (title, description, g.user['user_id'], start_date, end_date)
        )
        ballot_id = cur.fetchone()[0]
        for opt in options:
            cur.execute(
                "INSERT INTO ballot_options (ballot_id, option_text) VALUES (%s, %s)",
                (ballot_id, opt.strip())
            )
        conn.commit()
        return success({'ballot_id': str(ballot_id)}, message='Ballot created', status=201)
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@voting_bp.route('/ballots/<ballot_id>', methods=['GET'])
@token_required
def get_ballot(ballot_id):
    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM ballots WHERE id = %s", (ballot_id,))
        ballot = cur.fetchone()
        if not ballot:
            return error('Ballot not found', 404)

        cur.execute("SELECT id, option_text FROM ballot_options WHERE ballot_id = %s", (ballot_id,))
        options = [dict(o) | {'id': str(o['id'])} for o in cur.fetchall()]

        cur.execute(
            "SELECT option_selected, COUNT(*) AS votes FROM votes WHERE ballot_id = %s GROUP BY option_selected",
            (ballot_id,)
        )
        counts = {str(r['option_selected']): r['votes'] for r in cur.fetchall()}

        cur.execute(
            "SELECT id FROM votes WHERE ballot_id = %s AND user_id = %s",
            (ballot_id, g.user['user_id'])
        )
        has_voted = cur.fetchone() is not None

        return success({
            'ballot': dict(ballot) | {'id': str(ballot['id'])},
            'options': options,
            'vote_counts': counts,
            'has_voted': has_voted
        })
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@voting_bp.route('/ballots/<ballot_id>/vote', methods=['POST'])
@token_required
def cast_vote(ballot_id):
    data = request.get_json() or {}
    option_id = data.get('option_id')
    if not option_id:
        return error('option_id is required', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT status FROM ballots WHERE id = %s", (ballot_id,))
        ballot = cur.fetchone()
        if not ballot:
            return error('Ballot not found', 404)
        if ballot[0] != 'open':
            return error('Ballot is not open for voting', 400)

        cur.execute(
            "INSERT INTO votes (ballot_id, user_id, option_selected) VALUES (%s, %s, %s)",
            (ballot_id, g.user['user_id'], option_id)
        )
        conn.commit()
        return success(message='Vote recorded')
    except Exception as e:
        if conn:
            conn.rollback()
        if 'unique' in str(e).lower():
            return error('You have already voted on this ballot', 409)
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@voting_bp.route('/ballots/<ballot_id>/status', methods=['PATCH'])
@token_required
@admin_required
def update_ballot_status(ballot_id):
    data = request.get_json() or {}
    status = data.get('status')
    if status not in ('draft', 'open', 'closed'):
        return error("Status must be 'draft', 'open', or 'closed'", 400)

    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE ballots SET status = %s WHERE id = %s", (status, ballot_id))
        conn.commit()
        return success(message=f'Ballot status updated to {status}')
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)
