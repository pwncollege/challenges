{% extends "base/base.c" %}

{% block includes %}
  {% if walkthrough %}
    {% include "stack_recon.c" %}
  {% endif %}
{% endblock %}

{% block globals %}
  {% include "babyfmt/sections/helpers.c" %}
  {% include "babyfmt/sections/vulnerability.c" %}
{% endblock %}

{% block main %}
	assert(argc > 0);

	// -----------------------------------------//

	{% include "babyfmt/sections/intro.c" %}

	// -----------------------------------------//

	{% include "babyfmt/sections/prologue.c" %}

	// -----------------------------------------//

	func();

	// -----------------------------------------//

	{% include "babyfmt/sections/epilogue.c" %}

{% endblock %}

