#!/opt/pwn.college/python

import os
import sys
from collections import namedtuple

{% set pixel_size = 1 %}
{% if not challenge.color -%}
Pixel = namedtuple("Pixel", ["ascii"])
{% else -%}
Pixel = namedtuple("Pixel", ["r", "g", "b", "ascii"])
{% set pixel_size = 4 %}
{% endif %}

def main():
    if len(sys.argv) >= 2:
        path = sys.argv[1]
        assert path.endswith(".cimg"), "ERROR: file has incorrect extension"
        file = open(path, "rb")
    else:
        file = sys.stdin.buffer

    {% set header_size = 4
        + (challenge.version_bitwidth // 8 if challenge.version else 0)
        + (challenge.width_bitwidth // 8 if challenge.width else 0)
        + (challenge.height_bitwidth // 8 if challenge.height else 0) -%}
    header = file.read1({{ header_size }})
    assert len(header) == {{ header_size }}, "ERROR: Failed to read header!"

    {% if challenge.magic_chars -%}
    assert header[:4] == b"{{ challenge.magic_chars }}", "ERROR: Invalid magic number!"
    {% elif challenge.magic_int -%}
    assert int.from_bytes(header[:4], "little") == {{ "0x%x" | format(challenge.magic_int) }}, "ERROR: Invalid magic number!"
    {% endif %}
    {% set file_cursor = 4 %}

    {% if challenge.version -%}
    assert int.from_bytes(header[{{ file_cursor }}:{{ file_cursor + challenge.version_bitwidth // 8}}], "little") == {{ challenge.version }}, "ERROR: Invalid version!"
    {% set file_cursor = file_cursor + challenge.version_bitwidth // 8 %}
    {% endif %}

    {% if challenge.width -%}
    width = int.from_bytes(header[{{ file_cursor }}:{{ file_cursor + challenge.width_bitwidth // 8 }}], "little")
    {% if challenge.width is not true -%}
    assert width == {{ challenge.width }}, "ERROR: Incorrect width!"
    {% endif -%}
    {% set file_cursor = file_cursor + challenge.width_bitwidth // 8 %}
    {% endif %}

    {% if challenge.height -%}
    height = int.from_bytes(header[{{ file_cursor }}:{{ file_cursor + challenge.height_bitwidth // 8 }}], "little")
    {% if challenge.height is not true -%}
    assert height == {{ challenge.height }}, "ERROR: Incorrect height!"
    {% endif %}
    {% set file_cursor = file_cursor + challenge.height_bitwidth // 8 %}
    {% endif %}

    {% if challenge.width and challenge.height -%}
    data = file.read1(width * height {% if pixel_size != 1 %} * {{ pixel_size }}{% endif %})
    assert len(data) == width * height {% if pixel_size != 1 %} * {{ pixel_size }}{% endif %}, "ERROR: Failed to read data!"

    {% if not challenge.color -%}
    pixels = [Pixel(character) for character in data]
    {% else -%}
    pixels = [Pixel(*data[i:i+{{ pixel_size }}]) for i in range(0, len(data), {{ pixel_size }})]
    {% endif %}
    {% endif %}

    {% if challenge.assert_ascii -%}
    invalid_character = next((pixel.ascii for pixel in pixels if not (0x20 <= pixel.ascii <= 0x7e)), None)
    assert invalid_character is None, f"ERROR: Invalid character {invalid_character:#04x} in data!"
    {% endif %}

    {% if challenge.display -%}
    {% if not challenge.color -%}
    framebuffer = ("".join(bytes(pixel.ascii for pixel in pixels[row_start:row_start+width]).decode() + "\n"
                   for row_start in range(0, len(pixels), width)))
    {% else -%}
    ansii_escape = lambda pixel: f"\x1b[38;2;{pixel.r:03};{pixel.g:03};{pixel.b:03}m{chr(pixel.ascii)}\x1b[0m"
    framebuffer = ("".join("".join(ansii_escape(pixel) for pixel in pixels[row_start:row_start+width]) + ansii_escape(Pixel(0, 0, 0, ord("\n")))
                           for row_start in range(0, len(pixels), width)))
    {% endif -%}
    print(framebuffer)
    {% endif %}

    {% if challenge.check_num_nonspace -%}
    nonspace_count = sum(1 for pixel in pixels if chr(pixel.ascii) != ' ')
    if nonspace_count != {{ challenge.check_num_nonspace }}:
        return
    {% endif %}

    {% if challenge.check_asu_maroon -%}
    asu_maroon = (0x8c, 0x1d, 0x40)
    if any((pixel.r, pixel.g, pixel.b) != asu_maroon for pixel in pixels):
        return
    {% endif %}

    {% if challenge.win_function -%}
    with open("/flag", "r") as f:
        flag = f.read()
        print(flag)
    {% endif %}


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(e, file=sys.stderr)
        sys.exit(-1)
