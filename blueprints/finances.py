from flask import Blueprint, request, g
from psycopg2.extras import RealDictCursor

from middleware.auth import token_required, admin_required
from utils.supabase_client import get_db, close_db
from utils.helpers import success, error

finances_bp = Blueprint('finances', __name__, url_prefix='/api/v1/finances')


@finances_bp.route('', methods=['GET'])
@token_required
def list_finances():
    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """SELECT f.id, f.type, f.amount, f.description, f.transaction_date, f.created_at,
                      u.full_name AS recorded_by_name
               FROM finances f JOIN users u ON u.id = f.recorded_by
               ORDER BY f.transaction_date DESC"""
        )
        records = [dict(r) | {'id': str(r['id'])} for r in cur.fetchall()]

        cur.execute("SELECT COALESCE(SUM(amount),0) FROM finances WHERE type='income'")
        total_income = float(cur.fetchone()[0])
        cur.execute("SELECT COALESCE(SUM(amount),0) FROM finances WHERE type='expense'")
        total_expense = float(cur.fetchone()[0])

        return success({
            'records': records,
            'summary': {
                'total_income':  total_income,
                'total_expense': total_expense,
                'balance':       round(total_income - total_expense, 2)
            }
        })
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@finances_bp.route('', methods=['POST'])
@token_required
@admin_required
def add_record():
    data = request.get_json() or {}
    f_type           = data.get('type')
    amount           = data.get('amount')
    description      = data.get('description', '').strip()
    transaction_date = data.get('transaction_date')

    if f_type not in ('income', 'expense'):
        return error("Type must be 'income' or 'expense'", 400)
    if not amount or not transaction_date:
        return error('Amount and transaction_date are required', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO finances (type, amount, description, recorded_by, transaction_date)
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (f_type, amount, description, g.user['user_id'], transaction_date)
        )
        record_id = str(cur.fetchone()[0])
        conn.commit()
        return success({'record_id': record_id}, message='Record added', status=201)
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@finances_bp.route('/<record_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_record(record_id):
    conn = cur = None
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM finances WHERE id = %s", (record_id,))
        conn.commit()
        return success(message='Record deleted')
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)
