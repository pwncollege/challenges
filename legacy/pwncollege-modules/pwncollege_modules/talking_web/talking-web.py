{% extends "base/flask.py" %}

{% block handlers %}

{% if challenge.allowed_clients or challenge.allowed_username %}
{% include "peer-discovery.py" %}
{% endif %}

{% if challenge.index_form %}
@app.route("/", methods=["GET"])
def challenge_index():
    return """<html>
      <h1>Your form:</h1>
      <form action="/{{challenge.endpoint_name}}" method=post>
      {% for k in challenge.post_parameters %}
      <input name={{k}}>
      {% endfor %}
      <input type=submit value=Submit>
      </form>
    </html>"""
{% endif %}

{% if challenge.public_html %}
@app.route("/~hacker/<path:path>", methods=["GET"])
def public_html(path="index.html"):
    try:
        ruid, euid, suid = os.getresuid()
        os.seteuid(ruid)
        return flask.send_from_directory("/home/hacker/public_html", path)
    except PermissionError:
        flask.abort(403)
    finally:
        os.seteuid(euid)
{% endif %}

{% if challenge.redirects %}
import random
import string

secret_endpoint = "".join(random.sample(string.ascii_letters, 8))

@app.route("/", methods=["GET"])
def challenge_redirector():
    {% if challenge.allowed_clients -%}
    if name_of_program_for(peer_process_of(flask.request.input_stream.fileno())) not in {{ challenge.allowed_clients }}:
        flask.abort(400, "You are using an incorrect client to access this resource!")

    {% endif -%}
    return flask.redirect(f"/{secret_endpoint}-{{challenge.endpoint_name}}")

@app.route(f"/{secret_endpoint}-{{challenge.endpoint_name}}", methods={{ challenge.methods }})
{% else %}
@app.route("/{{challenge.endpoint_name}}", methods={{ challenge.methods }})
{% if challenge.arbitrary_path %}@app.route("/{{challenge.endpoint_name}}/<path:path>", methods=["GET"]){% endif %}
{% endif %}
def challenge({% if challenge.arbitrary_path %}path="index.html"{% endif %}):
    {% if challenge.allowed_clients -%}
    if name_of_program_for(peer_process_of(flask.request.input_stream.fileno())) not in {{ challenge.allowed_clients }}:
        flask.abort(400, "You are using an incorrect client to access this resource!")

    {% endif -%}
    {% if challenge.allowed_username -%}
    if peer_process_of(flask.request.input_stream.fileno()).username() != "{{ challenge.allowed_username }}":
        flask.abort(400, f"""
              This page must be accessed using a browser run by the {{ challenge.allowed_username }} user.
              Usually, this means you would run the scripted browser in /challenge/client or /challenge/victim,
              and it'll access this page for you.
              Of course, this sort of functionality doesn't exist on the actual web, as google.com can't access
              your user ID on your local machine, but we use this hack here for teaching purposes.
        """)

    {% endif -%}
    {% if challenge.useragent_substr -%}
    if "{{challenge.useragent_substr}}" not in flask.request.headers.get('User-Agent'):
        flask.abort(400, "You are using an incorrect client to access this resource!")

    {% endif -%}
    {% for k,v in challenge.get_parameters.items() -%}
    if flask.request.args.get("{{k}}", None) != "{{v}}":
        flask.abort(403, "Incorrect value for get parameter {{k}}!")

    {% endfor -%}
    {% for k,v in challenge.post_parameters.items() -%}
    if flask.request.form.get("{{k}}", None) != "{{v}}":
        flask.abort(403, "Incorrect value for post parameter {{k}}!")

    {% endfor -%}
    {% if challenge.flag_in_html -%}
    return f"""
        <html>
          <head><title>Talking Web</title></head>
        <body>
          <h1>Great job!</h1>
          {% if challenge.commented_flag %}<!-- TOP SECRET: {% endif %}<p>{open("/flag").read().strip()}</p>{% if challenge.commented_flag %} -->{%endif+%}
        </body>
        </html>
    """
    {% elif challenge.flag_in_header -%}
    response = flask.make_response("<html><head><title>Talking Web</title></head><body><h1>Great job!</h1></body></html>")
    response.headers["X-Flag"] = open("/flag").read().strip()
    return response
    {% elif challenge.flag_in_javascript -%}
    response = flask.Response(f"""var flag = "{open("/flag").read().strip()}";""", content_type="text/javascript")
    return response
    {% elif challenge.flag_in_text -%}
    response = flask.Response(open("/flag").read().strip(), content_type="text/plain")
    return response
    {% endif -%}

{% endblock %}
