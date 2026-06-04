import pandas as pd
import os

from column_mapping import COLUMN_MAPPING
from data_cleaner import clean_data


def parse_file(filepath):

    try:

        # ---------------- CSV ----------------
        if filepath.endswith(".csv"):

            try:
                df = pd.read_csv(
                    filepath,
                    encoding='utf-8',
                    sep=None,
                    engine='python',
                    on_bad_lines='skip'
                )

            except:

                df = pd.read_csv(
                    filepath,
                    encoding='latin-1',
                    sep=None,
                    engine='python',
                    on_bad_lines='skip'
                )

        # ---------------- EXCEL ----------------
        elif filepath.endswith(".xlsx") or filepath.endswith(".xls"):

            df = pd.read_excel(filepath)

        # ---------------- JSON ----------------
        elif filepath.endswith(".json"):

            df = pd.read_json(filepath)

        else:
            return {}

        # ---------------- COLUMN MAPPING ----------------

        mapped_columns = {}

        for col in df.columns:

            clean_col = col.strip()

            if clean_col in COLUMN_MAPPING:

                mapped_columns[col] = COLUMN_MAPPING[clean_col]

        df = df.rename(columns=mapped_columns)

        # ---------------- DATA CLEANING ----------------

        df, cleaning_report = clean_data(df)

        # ---------------- SAVE CLEANED FILE ----------------

        filename = os.path.basename(filepath)

        cleaned_path = os.path.join(
            "cleaned_uploads",
            f"cleaned_{filename}"
        )

        df.to_csv(cleaned_path, index=False)

        # ---------------- RETURN ----------------

        return {
            "message": "File cleaned successfully"
        }

    except Exception as e:

        print("PARSER ERROR:", str(e))

        raise Exception(f"File parsing failed: {str(e)}")