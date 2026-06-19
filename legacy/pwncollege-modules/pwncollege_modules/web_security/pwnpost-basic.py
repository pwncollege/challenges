{% extends "flask-template.py" %}

{% block imports %}
{% if challenge.pw_name == "pin" %}
import random
{%endif%}
{% endblock %}

{% block handlers %}

{% include "temporary-db.py" %}

# https://www.sqlite.org/lang_createtable.html
db.execute("""CREATE TABLE posts AS SELECT "First Post!" AS content""")

@app.route("/", methods=["POST"])
def challenge_post():
    content = flask.request.form.get("content", "")
    db.execute("INSERT INTO posts VALUES (?)", [content])
    return flask.redirect(flask.request.path)

@app.route("/", methods=["GET"])
def challenge_get():
    page = "<html><body>\nWelcome to pwnpost, the anonymous posting service. Post away!\n"
    page += "<form method=post>Post:<input type=text name=content><input type=submit value=Submit></form>\n"

    for post in db.execute("SELECT content FROM posts").fetchall():
        page += "<hr>" + post["content"] + "\n"

    return page + "</body></html>"

{% endblock %}
