{% extends "base/flask.py" %}

{% block handlers %}

@app.route("/{{challenge.endpoint}}", methods=["GET"])
@app.route("/{{challenge.endpoint}}/<path:path>", methods=["GET"])
def challenge(path="index.html"):
    requested_path = app.root_path + "/files/" + path{% if challenge.strip_dots %}.strip("/."){% endif %}

    {% if challenge.walkthrough %}print(f"DEBUG: {requested_path=}"){% endif %}

    try:
        return open(requested_path).read()
    except PermissionError:
        flask.abort(403, requested_path)
    except FileNotFoundError:
        flask.abort(404, f"No {requested_path} from directory {os.getcwd()}")
    except Exception as e:
        flask.abort(500, requested_path + ":" + str(e))

{% endblock %}
