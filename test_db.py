import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Test database connection
url = os.getenv('DEV_DATABASE_URL')
print(f"Using URL: {url}")

try:
    # Clean the URL
    if '?' in url:
        url = url.split('?')[0]
    
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    
    # Set schema
    cur.execute("SET search_path TO idms_dev")
    
    # Test query
    cur.execute("SELECT * FROM users LIMIT 1")
    result = cur.fetchone()
    print("✅ Database connection successful!")
    print(f"Found user: {result}")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Database error: {str(e)}")