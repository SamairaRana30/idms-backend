def clean_data(df):

    original_rows = len(df)

    # STANDARDIZE COLUMN NAMES
    df.columns = df.columns.str.strip().str.lower()

    # STANDARDIZE EMAIL
    if 'email' in df.columns:
        df['email'] = (
            df['email']
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

    # STANDARDIZE PHONE
    if 'phone' in df.columns:
        df['phone'] = (
            df['phone']
            .fillna("")
            .astype(str)
            .str.replace(r'\D', '', regex=True)
        )

    # STANDARDIZE NAME
    if 'name' in df.columns:
        df['name'] = (
            df['name']
            .fillna("")
            .astype(str)
            .str.strip()
            .str.title()
        )

    # REMOVE DUPLICATES
    before = len(df)

    if 'member_id' in df.columns:
        df = df.drop_duplicates(subset=['member_id'])

    duplicates_removed = before - len(df)

    cleaning_report = {
        "original_rows": original_rows,
        "rows_after_cleaning": len(df),
        "duplicates_removed": duplicates_removed
    }

    return df, cleaning_report