import sqlite3, random, os
def connect_to_name_gen_db():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, "name_gen.db")
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    return cur

def generate_name(cur):
    '''
    retrieves one random adjective and noun.
    '''
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

def generate_username():
    cur = connect_to_name_gen_db()
    return generate_name(cur)
