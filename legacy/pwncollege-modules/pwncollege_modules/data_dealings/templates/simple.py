#!/usr/bin/exec-suid -- /bin/python3 -I

import sys

{% if "b64encode" in challenge.all_mutators or "b64decode" in challenge.all_mutators%}
import base64
{% endif %}
{% if "urlencode" in challenge.all_mutators or "urldecode" in challenge.all_mutators%}
import urllib
{% endif %}

{% if "reverse" in challenge.all_mutators %}
def reverse_string(s):
	return s[::-1]
{% endif %}

{% if "binencode" in challenge.all_mutators %}
def encode_to_bits(s):
	return b"".join(format(c, "08b").encode('latin1') for c in s)
{% endif %}

{% if "bindecode" in challenge.all_mutators %}
def decode_from_bits(s):
	s = s.decode("latin1")
	assert set(s) <= { "0", "1" }, "non-binary characters found in bitstream!"
	assert len(s)%8 == 0, "must enter data in complete bytes (each byte is 8 bits)"
	return int.to_bytes(int(s, 2), length=len(s)//8, byteorder='big')
{% endif %}

{% macro mutate(what, mutators) %}
{% for mutator in mutators %}
{% if mutator == "reverse" %}
{{what}} = {{what}}[::-1]
{% elif mutator == "hexencode" %}
{{what}} = {{what}}.hex().encode('l1')
{% elif mutator == "hexdecode" %}
{{what}} = bytes.fromhex({{what}}.decode('l1'))
{% elif mutator == "binencode" %}
{{what}} = encode_to_bits({{what}})
{% elif mutator == "bindecode" %}
{{what}} = decode_from_bits({{what}})
{% elif mutator == "b64encode" %}
{{what}} = base64.b64encode({{what}})
{% elif mutator == "b64decode" %}
{{what}} = base64.b64decode({{what}}.decode('l1'))
{% elif mutator == "urlencode" %}
{{what}} = urllib.parse.quote({{what}}.decode('l1'))
{% elif mutator == "urldecode" %}
{{what}} = urllib.parse.unquote({{what}}.decode('l1'))
{% elif mutator == "utf-16-confusion-encode" %}
{{what}} = {{what}}.decode("utf-16")
{{what}} = {{what}}.encode("latin1")
{% elif mutator == "utf-16-confusion-decode" %}
{{what}} = {{what}}.decode("latin1")
{{what}} = {{what}}.encode("utf-16")
{% endif %}
{% endfor %}
{% endmacro %}

{% if challenge.input_method == "stdin" %}
print("Enter the password:")
entered_password = sys.stdin.buffer.read1(){%if challenge.strip%}.strip(){%endif+%}
{% elif challenge.input_method in [ "fixedfile", "argfile" ] %}
try:
	entered_password = open(
		{% if challenge.input_method == "fixedfile" %}
		"{{ challenge.input_filename }}"
		{% elif challenge.input_method == "argfile" %}
		sys.argv[1]
		{% endif %}, "rb"
	).read(){%if challenge.strip%}.strip(){%endif+%}
except FileNotFoundError:
	print("Input file not found...")
	sys.exit(1)
{% endif %}
{% if challenge.warn_newline %}
if b"\n" in entered_password:
	print("Password has newlines /")
	print("Editors add them sometimes /")
	print("Learn to remove them.")

{% endif %}
{% if challenge.reference_method == "hardcoded" and challenge.pw_type == "emoji" %}
correct_password = "{{ challenge.password.decode("utf-8") }}".encode("utf-8")
{% elif challenge.reference_method == "hardcoded" %}
correct_password = {{ challenge.password.__repr__() }}
{% elif challenge.reference_method == "fixedfile" %}
correct_password = open("{{ challenge.reference_filename }}").read()
{% endif %}

print(f"Read {len(entered_password)} bytes.")

{% if challenge.forbid_password %}
assert entered_password != correct_password
{% endif %}

{{ mutate("entered_password", challenge.input_mutators) }}
{{ mutate("correct_password", challenge.reference_mutators) }}

if entered_password == correct_password:
    print("Congrats! Here is your flag:")
    print(open("/flag").read().strip())
else:
	print("Incorrect!")
	sys.exit(1)
