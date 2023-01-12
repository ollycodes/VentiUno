import sqlite3, random, os

def generate_username():
    '''
    retrieves one random adjective and noun.
    '''
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "name_gen.db")
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    tables = ["Adjectives", "Nouns"]
    username = ""

    for table in tables:
        cur.execute(f"SELECT Word FROM {table}")
        rows = cur.fetchall()
        word = rows[random.randrange(len(rows))]
        word = ",".join(word)
        word = word.replace(" ","")
        username += word.capitalize()
    return username
