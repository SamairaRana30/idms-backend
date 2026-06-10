import psycopg2
from supabase import create_client

SUPABASE_URL = "https://pkkwcefyqskgfchmemhe.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBra3djZWZ5cXNrZ2ZjaG1lbWhlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjY3NTI2MiwiZXhwIjoyMDkyMjUxMjYyfQ.x--s_YHcehZ-evQvSOEd51clibf1vcfaqiTqShxNyEU"

def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)