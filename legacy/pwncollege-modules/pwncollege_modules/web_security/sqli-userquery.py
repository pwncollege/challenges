{% extends "flask-template.py" %}

{% block imports %}
{% if challenge.table_identifier == "{random_user_table}" %}
import random
{% endif %}
{% endblock %}

{% block handlers %}

{% include "temporary-db.py" %}

{% if challenge.table_identifier == "{random_user_table}" %}
random_user_table = f"users_{random.randrange(2**32, 2**33)}"
{% endif %}
db.execute(f"""CREATE TABLE {{challenge.table_identifier}} AS SELECT "admin" AS username, ? as password""", [open("/flag").read()])
# https://www.sqlite.org/lang_insert.html
db.execute(f"""INSERT INTO {{challenge.table_identifier}} SELECT "guest" as username, "password" as password""")

@app.route("/", methods=["GET"])
def challenge():
    query = flask.request.args.get("query", "%")

    try:
        {% if challenge.table_identifier == "{random_user_table}" %}# https://www.sqlite.org/schematab.html{%endif+%}
        # https://www.sqlite.org/lang_select.html
        sql = f'SELECT username FROM {{challenge.table_identifier}} WHERE username LIKE "{query}"'
        print(f"DEBUG: {query=}")
        results = "\n".join(user["username"] for user in db.execute(sql).fetchall())
    except sqlite3.Error as e:
        results = f"SQL error: {e}"

    return f"""
        <html><body>Welcome to the user query service!
        <form>Query:<input type=text name=query value='{query}'><input type=submit value=Submit></form>
        <hr>
        <b>Query:</b> <pre>{ sql{% if challenge.table_identifier == "{random_user_table}" %}.replace(random_user_table, "REDACTED"){%endif%} }</pre><br>
        <b>Results:</b><pre>{results}</pre>
        </body></html>
        """

{% endblock %}
