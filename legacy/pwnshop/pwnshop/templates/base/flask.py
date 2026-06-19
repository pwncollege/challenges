#!/opt/pwn.college/python

{% block imports %}
{% endblock %}
import flask
import os

app = flask.Flask(__name__)

{% block handlers %}
{% endblock %}
{% block initialization %}
{% endblock %}

{% if challenge.reset_uid %}
os.setuid(os.geteuid())
{% endif %}
{% if challenge.reset_path %}
os.environ["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
{% endif %}
app.secret_key = os.urandom(8)
{% if challenge.flask_host %}
app.config['SERVER_NAME'] = "{{challenge.flask_host}}:{{challenge.flask_port or 80}}"
{% endif %}
app.run("{{challenge.host_override or challenge.flask_host or "0.0.0.0"}}", {{challenge.flask_port}})
