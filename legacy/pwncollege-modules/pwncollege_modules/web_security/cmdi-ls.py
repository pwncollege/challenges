{% extends "base/flask.py" %}

{% block imports %}
import subprocess
{% endblock %}

{% block handlers %}

@app.route("/{{challenge.endpoint}}", methods=["GET"])
def challenge():
    arg = flask.request.args.get("{{challenge.parameter}}", "{{challenge.default_value}}"){% for char in (challenge.filtered_chars or []) %}.replace("{{char}}", ""){% endfor %}

    {% if challenge.command == "ls" -%}
    command = f"ls -l {{challenge.quote_character}}{arg}{{challenge.quote_character}}"
    {% elif challenge.command == "date" -%}
    command = f"TZ={arg} date"
    {% elif challenge.command == "touch" -%}
    command = f"touch {arg}"
    {% endif %}

    print(f"DEBUG: {command=}")
    result = subprocess.run(
        command,                    # the command to run
        shell=True,                 # use the shell to run this command
        stdout=subprocess.PIPE,     # capture the standard output
        stderr=subprocess.STDOUT,   # 2>&1
        encoding="latin"            # capture the resulting output as text
    ).stdout

    return f"""
        <html><body>
        {{ challenge.description }}
        <form action="/{{challenge.endpoint}}"><input type=text name={{challenge.parameter}}><input type=submit value=Submit></form>
        <hr>
        {% if challenge.hide_output -%}
        <b>Ran {command}!</b><br>
        {% else -%}
        <b>Output of {command}:</b><br>
        <pre>{result}</pre>
        {% endif -%}
        </body></html>
        """

{% endblock %}
