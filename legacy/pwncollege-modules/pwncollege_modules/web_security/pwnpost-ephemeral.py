{% extends "flask-template.py" %}

{% block handlers %}

@app.route("/", methods=["GET"])
def challenge_get():
    return f"""
        <html><body>
        <h1>pwnmsg ephemeral message service</h1>
        The message:
        {% if not challenge.msg_in_textarea -%}
        {flask.request.args.get("msg", "(none)")}
        <hr>
        {% endif -%}
        <form>
            {% if not challenge.msg_in_textarea -%}
            Craft a message:
            <input type=text name=msg>
            {% else -%}
            <textarea name=msg>{flask.request.args.get("msg", "Type your message here!")}</textarea>
            {% endif -%}
            <input type=submit value="Make URL!">
        </form>
        </body></html>
    """

{% endblock %}
