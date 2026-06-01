from flask import Blueprint, request, g
from psycopg2.extras import RealDictCursor

from middleware.auth import require_auth, require_admin
from utils.supabase_client import get_db, close_db
from utils.helpers import success, error, paginate

finances_bp = Blueprint('finances', __name__, url_prefix='/api/v1/finances')


@finances_bp.route('/summary', methods=['GET'])
@require_auth
def get_summary():
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT COALESCE(SUM(amount),0) FROM finance_records WHERE type='income'")
        total_income  = float(cur.fetchone()['coalesce'])
        cur.execute("SELECT COALESCE(SUM(amount),0) FROM finance_records WHERE type='expense'")
        total_expense = float(cur.fetchone()['coalesce'])
        return success({
            'total_income':   total_income,
            'total_expenses': total_expense,
            'balance':        round(total_income - total_expense, 2)
        })
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@finances_bp.route('/report', methods=['GET'])
@require_auth
@require_admin
def get_report():
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT
                TO_CHAR(DATE_TRUNC('month', COALESCE(transaction_date::timestamp, created_at)), 'YYYY-MM') AS month,
                type,
                SUM(amount)  AS total,
                COUNT(*)     AS count
            FROM finance_records
            GROUP BY DATE_TRUNC('month', COALESCE(transaction_date::timestamp, created_at)), type
            ORDER BY DATE_TRUNC('month', COALESCE(transaction_date::timestamp, created_at)) DESC
        """)
        rows = cur.fetchall()

        # Build month map
        months = {}
        for r in rows:
            m = r['month']
            if m not in months:
                months[m] = {'month': m, 'income': 0, 'expense': 0}
            months[m][r['type']] = float(r['total'])

        breakdown = sorted(months.values(), key=lambda x: x['month'], reverse=True)
        for b in breakdown:
            b['balance'] = round(b['income'] - b['expense'], 2)

        return success({'breakdown': breakdown, 'total_months': len(breakdown)})
    except Exception as e:
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@finances_bp.route('', methods=['GET'])
@require_auth
def list_finances():
    page, limit, offset = paginate(request)
    f_type   = request.args.get('type', '').strip()
    date_from = request.args.get('from', '').strip()
    date_to   = request.args.get('to', '').strip()

    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=RealDictCursor)

        conditions = []
        params     = []
        if f_type in ('income', 'expense'):
            conditions.append("f.type = %s")
            params.append(f_type)
        if date_from:
            conditions.append("COALESCE(f.transaction_date, f.created_at::date) >= %s")
            params.append(date_from)
        if date_to:
            conditions.append("COALESCE(f.transaction_date, f.created_at::date) <= %s")
            params.append(date_to)

        where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''

        cur.execute(f"SELECT COUNT(*) FROM finance_records f {where}", params)
        total = cur.fetchone()['count']

        cur.execute(
            f"""SELECT f.id, f.type, f.amount, f.description, f.category,
                       COALESCE(f.transaction_date, f.created_at::date) AS date,
                       f.created_at,
                       u.full_name AS recorded_by_name
                FROM finance_records f
                LEFT JOIN users u ON u.id::text = f.recorded_by
                {where}
                ORDER BY COALESCE(f.transaction_date, f.created_at::date) DESC
                LIMIT %s OFFSET %s""",
            [*params, limit, offset]
        )
        records = [dict(r) | {'id': str(r['id'])} for r in cur.fetchall()]

        cur.execute("SELECT COALESCE(SUM(amount),0) FROM finance_records WHERE type='income'")
        total_income  = float(cur.fetchone()['coalesce'])
        cur.execute("SELECT COALESCE(SUM(amount),0) FROM finance_records WHERE type='expense'")
        total_expense = float(cur.fetchone()['coalesce'])

        return success({
            'records': records,
            'total':   total,
            'page':    page,
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
@require_auth
def add_record():
    data             = request.get_json() or {}
    f_type           = data.get('type')
    amount           = data.get('amount')
    description      = data.get('description', '').strip()
    category         = data.get('category', '').strip()
    transaction_date = data.get('transaction_date') or None

    if f_type not in ('income', 'expense'):
        return error("Type must be 'income' or 'expense'", 400)
    if not amount:
        return error('Amount is required', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO finance_records "
            "(type, amount, description, category, transaction_date, recorded_by) "
            "VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
            (f_type, amount, description, category or None, transaction_date, g.user['user_id'])
        )
        record_id = str(cur.fetchone()[0])
        conn.commit()
        return success({'record_id': record_id}, 201)
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@finances_bp.route('/<record_id>', methods=['PUT'])
@require_auth
@require_admin
def edit_record(record_id):
    data    = request.get_json() or {}
    allowed = {'type', 'amount', 'description', 'category', 'transaction_date'}
    updates = {k: v for k, v in data.items() if k in allowed and v is not None}
    if not updates:
        return error('No valid fields to update', 400)

    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        set_clause = ', '.join(f"{k} = %s" for k in updates)
        cur.execute(
            f"UPDATE finance_records SET {set_clause} WHERE id = %s",
            [*updates.values(), record_id]
        )
        conn.commit()
        return success({'message': 'Record updated'})
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)


@finances_bp.route('/<record_id>', methods=['DELETE'])
@require_auth
@require_admin
def delete_record(record_id):
    conn = cur = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("DELETE FROM finance_records WHERE id = %s", (record_id,))
        conn.commit()
        return success({'message': 'Record deleted'})
    except Exception as e:
        if conn:
            conn.rollback()
        return error(str(e), 500)
    finally:
        close_db(conn, cur)
