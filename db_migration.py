from database import get_db_connection


def migrate_to_database(df):

    conn = get_db_connection()

    cur = conn.cursor()

    inserted_rows = 0

    for _, row in df.iterrows():

        cur.execute(
            """
            INSERT INTO cleaned_members
            (
                member_id,
                name,
                email,
                phone
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                str(row.get("member_id", "")),
                str(row.get("name", "")),
                str(row.get("email", "")),
                str(row.get("phone", ""))
            )
        )

        inserted_rows += 1

    conn.commit()

    cur.close()
    conn.close()

    return inserted_rows