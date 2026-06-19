{% extends "flask-template.py" %}

{% block handlers %}

flag = open("/flag").read().strip() if os.geteuid() == 0 else "pwn.college{fake_flag}"

{% include "temporary-db.py" %}

# https://www.sqlite.org/lang_createtable.html
db.execute("""CREATE TABLE posts AS SELECT ? AS content, "admin" AS author, FALSE AS published""", [flag])
db.execute("""CREATE TABLE users AS SELECT "admin" AS username, ? as password""", [{{ challenge.admin_pw_code or "flag"}}])
# https://www.sqlite.org/lang_insert.html
db.execute("""INSERT INTO users SELECT "guest" as username, "password" as password""")
db.execute("""INSERT INTO users SELECT "hacker" as username, "1337" as password""")

@app.route("/login", methods=["POST"])
def challenge_login():
    username = flask.request.form.get("username")
    password = flask.request.form.get("password")
    if not username:
        flask.abort(400, "Missing `username` form parameter")
    if not password:
        flask.abort(400, "Missing `password` form parameter")

    # https://www.sqlite.org/lang_select.html
    user = db.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
    if not user:
        flask.abort(403, "Invalid username or password")

    {% if challenge.insecure_cookie -%}
    response = flask.redirect("/")
    response.set_cookie('auth', username+"|"+password)
    return response
    {% else -%}
    flask.session["username"] = username
    return flask.redirect("/")
    {% endif %}

@app.route("/draft", methods=["POST"])
def challenge_draft():
    {% if challenge.insecure_cookie -%}
    username, password = flask.request.cookies.get("auth", "|").split("|")
    user = db.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
    if not user:
        flask.abort(403, "Invalid username or password")
    {% else -%}
    username = flask.session.get("username", None)
    if not username:
        flask.abort(403, "Log in first!")
    {% endif %}

    {% if challenge.disable_admin_posting -%}
    if username == "admin":
        flask.abort(400, "pwnpost no longer supports admin posting due to rampant flag disclosure")
    {% endif -%}

    content = flask.request.form.get("content", "")
    # https://www.sqlite.org/lang_insert.html
    db.execute(
        "INSERT INTO posts (content, author, published) VALUES (?, ?, ?)",
        (content, username, bool(flask.request.form.get("publish")))
    )
    return flask.redirect("/")

@app.route("/publish", methods=["{{challenge.publish_method}}"])
def challenge_publish():
    {% if challenge.insecure_cookie -%}
    username, password = flask.request.cookies.get("auth", "|").split("|")
    user = db.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
    if not user:
        flask.abort(403, "Invalid username or password")
    {% else -%}
    username = flask.session.get("username", None)
    if not username:
        flask.abort(403, "Log in first!")
    {% endif %}

    {% if challenge.disable_admin_posting -%}
    if username == "admin":
        flask.abort(400, "pwnpost no longer supports admin posting due to rampant flag disclosure")
    {% endif -%}

    # https://www.sqlite.org/lang_update.html
    db.execute("UPDATE posts SET published = TRUE WHERE author = ?", [username])
    return flask.redirect("/")

@app.route("/", methods=["GET"])
def challenge_get():
    page = "<html><body>\nWelcome to pwnpost, now with users!<hr>\n"
    {% if challenge.insecure_cookie -%}
    username, password = flask.request.cookies.get("auth", "|").split("|")
    user = db.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
    if user:
    {%- else -%}
    username = flask.session.get("username", None)
    if username:
    {%- endif +%}
        page += """
            <form action=draft method=post>
              Post:<textarea name=content>Write something!</textarea>
              <input type=checkbox name=publish>Publish
              <input type=submit value=Save>
            </form><br>
            {% if challenge.publish_method == "GET" -%}
            <a href=publish>Publish your drafts!</a>
            {% else -%}
            <form action=publish method=post><input type=submit value="Publish All Drafts"></form>
            {% endif -%}
            <hr>
        """

        for post in db.execute("SELECT * FROM posts").fetchall():
            page += f"""<h2>Author: {post["author"]}</h2>"""
            if post["published"]:
                page += post["content"] + "<hr>\n"
            {% if challenge.show_own_drafts -%}
            elif post["author"] == username:
                page += "<b>YOUR DRAFT POST:</b> " + post["content"] + "<hr>\n"
            {% endif -%}
            else:
                page += f"""(Draft post, showing first 12 characters):<br>{post["content"][:12]}<hr>"""
    else:
        page += """
            <form action=login method=post>
              Username:<input type=text name=username>
              Password:<input type=text name=password>
              <input type=submit name=submit value=Login>
            </form><hr>
        """

    return page + "</body></html>"

{% endblock %}
