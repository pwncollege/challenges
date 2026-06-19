#!/usr/bin/exec-suid -- /bin/python3 -I

import requests
import pwnshop
import urllib
import struct
import base64
import time
import pwn
import os

INPUT_METHODS = [ "stdin", "fixedfile", "argfile" ]

VALID_EMOJI = ['😃', '😄', '😁', '😆', '😅', '😂', '😉', '😊', '😇', '😍', '😘', '😚', '😋', '😜', '😝', '😐', '😶', '😏', '😒', '😌', '😔', '😪', '😷', '😵', '😎', '😲', '😳', '😨', '😰', '😥', '😢', '😭', '😱', '😖', '😣', '😞', '😓', '😩', '😫', '😤', '😡', '😠', '😈', '👿', '💀', '💩', '👹', '👺', '👻', '👽', '👾', '😺', '😸', '😹', '😻', '😼', '😽', '🙀', '😿', '😾', '🙈', '🙉', '🙊', '💌', '💘', '💝', '💖', '💗', '💓', '💞', '💕', '💟', '💔', '💛', '💚', '💙', '💜', '💋', '💯', '💢', '💥', '💫', '💦', '💨', '💬', '💭', '💤', '👋', '✋', '👌', '👈', '👉', '👆', '👇', '👍', '👎', '✊', '👊', '👏', '🙌', '👐', '🙏', '💅', '💪', '👂', '👃', '👀', '👅', '👄', '👶', '👦', '👧', '👱', '👨', '👩', '👴', '👵', '🙍', '🙎', '🙅', '🙆', '💁', '🙋', '🙇', '👮', '💂', '👷', '👸', '👳', '👲', '👰', '👼', '🎅', '💆', '💇', '🚶', '🏃', '💃', '👯', '🏇', '🏂', '🏄', '🚣', '🏊', '🚴', '🚵', '🛀', '👭', '👫', '👬', '💏', '💑', '👤', '👥', '👪', '👣', '🐵', '🐒', '🐶', '🐕', '🐩', '🐺', '🐱', '🐈', '🐯', '🐅', '🐆', '🐴', '🐎', '🐮', '🐂', '🐃', '🐄', '🐷', '🐖', '🐗', '🐽', '🐏', '🐑', '🐐', '🐪', '🐫', '🐘', '🐭', '🐁', '🐀', '🐹', '🐰', '🐇', '🐻', '🐨', '🐼', '🐾', '🐔', '🐓', '🐣', '🐤', '🐥', '🐦', '🐧', '🐸', '🐊', '🐢', '🐍', '🐲', '🐉', '🐳', '🐋', '🐬', '🐟', '🐠', '🐡', '🐙', '🐚', '🐌', '🐛', '🐜', '🐝', '🐞', '💐', '🌸', '💮', '🌹', '🌺', '🌻', '🌼', '🌷', '🌱', '🌲', '🌳', '🌴', '🌵', '🌾', '🌿', '🍀', '🍁', '🍂', '🍃', '🍄', '🍇', '🍈', '🍉', '🍊', '🍋', '🍌', '🍍', '🍎', '🍏', '🍐', '🍑', '🍒', '🍓', '🍅', '🍆', '🌽', '🌰', '🍞', '🍖', '🍗', '🍔', '🍟', '🍕', '🍳', '🍲', '🍱', '🍘', '🍙', '🍚', '🍛', '🍜', '🍝', '🍠', '🍢', '🍣', '🍤', '🍥', '🍡', '🍦', '🍧', '🍨', '🍩', '🍪', '🎂', '🍰', '🍫', '🍬', '🍭', '🍮', '🍯', '🍼', '🍵', '🍶', '🍷', '🍸', '🍹', '🍺', '🍻', '🍴', '🔪', '🌍', '🌎', '🌏', '🌐', '🗾', '🌋', '🗻', '🏠', '🏡', '🏢', '🏣', '🏤', '🏥', '🏦', '🏨', '🏩', '🏪', '🏫', '🏬', '🏭', '🏯', '🏰', '💒', '🗼', '🗽', '🌁', '🌃', '🌄', '🌅', '🌆', '🌇', '🌉', '🎠', '🎡', '🎢', '💈', '🎪', '🚂', '🚃', '🚄', '🚅', '🚆', '🚇', '🚈', '🚉', '🚊', '🚝', '🚞', '🚋', '🚌', '🚍', '🚎', '🚐', '🚑', '🚒', '🚓', '🚔', '🚕', '🚖', '🚗', '🚘', '🚙', '🚚', '🚛', '🚜', '🚲', '🚏', '🚨', '🚥', '🚦', '🚧', '🚤', '🚢', '💺', '🚁', '🚟', '🚠', '🚡', '🚀', '⏳', '⏰', '🕛', '🕧', '🕐', '🕜', '🕑', '🕝', '🕒', '🕞', '🕓', '🕟', '🕔', '🕠', '🕕', '🕡', '🕖', '🕢', '🕗', '🕣', '🕘', '🕤', '🕙', '🕥', '🕚', '🕦', '🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘', '🌙', '🌚', '🌛', '🌜', '🌝', '🌞', '🌟', '🌠', '🌌', '🌀', '🌈', '🌂', '🔥', '💧', '🌊', '🎃', '🎄', '🎆', '🎇', '✨', '🎈', '🎉', '🎊', '🎋', '🎍', '🎎', '🎏', '🎐', '🎑', '🎀', '🎁', '🎫', '🏆', '🏀', '🏈', '🏉', '🎾', '🎳', '🎣', '🎽', '🎿', '🎯', '🔫', '🎱', '🔮', '🎮', '🎰', '🎲', '🃏', '🎴', '🎭', '🎨', '👓', '👔', '👕', '👖', '👗', '👘', '👙', '👚', '👛', '👜', '👝', '🎒', '👞', '👟', '👠', '👡', '👢', '👑', '👒', '🎩', '🎓', '💄', '💍', '💎', '🔇', '🔈', '🔉', '🔊', '📢', '📣', '📯', '🔔', '🔕', '🎼', '🎵', '🎶', '🎤', '🎧', '📻', '🎷', '🎸', '🎹', '🎺', '🎻', '📱', '📲', '📞', '📟', '📠', '🔋', '🔌', '💻', '💽', '💾', '💿', '📀', '🎥', '🎬', '📺', '📷', '📹', '📼', '🔍', '🔎', '💡', '🔦', '🏮', '📔', '📕', '📖', '📗', '📘', '📙', '📚', '📓', '📒', '📃', '📜', '📄', '📰', '📑', '🔖', '💰', '💴', '💵', '💶', '💷', '💸', '💳', '💹', '📧', '📨', '📩', '📤', '📥', '📦', '📫', '📪', '📬', '📭', '📮', '📝', '💼', '📁', '📂', '📅', '📆', '📇', '📈', '📉', '📊', '📋', '📌', '📍', '📎', '📏', '📐', '🔒', '🔓', '🔏', '🔐', '🔑', '🔨', '💣', '🔧', '🔩', '🔗', '🔬', '🔭', '📡', '💉', '💊', '🚪', '🚽', '🚿', '🛁', '🚬', '🗿', '🏧', '🚮', '🚰', '🚹', '🚺', '🚻', '🚼', '🚾', '🛂', '🛃', '🛄', '🛅', '🚸', '🚫', '🚳', '🚭', '🚯', '🚱', '🚷', '📵', '🔞', '🔃', '🔄', '🔙', '🔚', '🔛', '🔜', '🔝', '🔯', '⛎', '🔀', '🔁', '🔂', '⏩', '⏪', '🔼', '⏫', '🔽', '⏬', '🎦', '🔅', '🔆', '📶', '📳', '📴', '➕', '➖', '➗', '❓', '❔', '❕', '💱', '💲', '🔱', '📛', '🔰', '✅', '❌', '❎', '➰', '➿', '🔟', '🔠', '🔡', '🔢', '🔣', '🔤', '🆎', '🆑', '🆒', '🆓', '🆔', '🆕', '🆖', '🆗', '🆘', '🆙', '🆚', '🈁', '🈶', '🉐', '🈹', '🈲', '🉑', '🈸', '🈴', '🈳', '🈺', '🈵', '🔴', '🔵', '🔶', '🔷', '🔸', '🔹', '🔺', '🔻', '💠', '🔘', '🔳', '🔲', '🏁', '🚩', '🎌', '⛢', '⛤', '⛥', '⛦']
assert all(len(_e)==1 for _e in VALID_EMOJI)

class PasswordCheckerBase(pwnshop.PythonChallenge):
    TEMPLATE_PATH = "templates/simple.py"
    input_mutators = [ ]
    reference_mutators = [ ]
    input_method = "stdin"
    reference_method = "hardcoded"
    strip = False
    warn_newline = False
    pw_type = "letters"
    forbid_password = False

    reference_mutator_depth = 0
    reference_mutator_options = [ ]
    input_mutator_depth = 0
    input_mutator_options = [ ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.password = self.mutate(
            self._generate_password(),
            self.reference_mutators, invert=True
        )

        if self.input_method == "random":
            self.input_method = self.random.choice(INPUT_METHODS)

        if self.input_method == "fixedfile":
            self.input_filename = self.random_word(4)

        if self.reference_mutator_depth:
            self.reference_mutators = self.random.sample(
                self.reference_mutator_options,
                self.reference_mutator_depth
            )
        if self.input_mutator_depth:
            self.input_mutators = self.random.sample(
                self.input_mutator_options,
                self.input_mutator_depth
            )

        # this logic doesn't exist
        assert self.pw_type != "emoji" or not self.reference_mutators

    def _generate_password(self):
        if self.pw_type == "letters":
            return self.random_word(8).encode('l1')
        elif self.pw_type == "emoji":
            return " ".join(self.random.sample(VALID_EMOJI, 4)).encode("utf-8")
        elif self.pw_type == "highbyte":
            return bytes([ self.random.randrange(0x80, 0xff) ])
        elif self.pw_type == "highbytes":
            return bytes([
                self.random.randrange(0x80, 0xff) for _ in range(8)
            ])
        elif self.pw_type == "bytes":
            return self.random.randbytes(8)
        else:
            raise NotImplementedError()

    @property
    def all_mutators(self):
        return set(self.input_mutators + self.reference_mutators)

    @staticmethod
    def mutate(word, mutators, invert=False):
        assert type(word) is bytes

        if invert:
            mutators = reversed(mutators)

        for m in mutators:
            if invert and "decode" in m:
                m = m.replace("decode", "encode")
            elif invert and "encode" in m:
                m = m.replace("encode", "decode")

            if m == "hexdecode":
                word = bytes.fromhex(word.decode('l1').replace(" ",""))
            if m == "hexencode":
                word = word.hex().encode('l1')
            if m == "binencode":
                word = b"".join(format(c, "08b").encode('latin1') for c in word)
            if m == "bindecode":
                word = int.to_bytes(int(word, 2), length=len(word)//8)
            if m == "b64encode":
                word = base64.b64encode(word)
            if m == "b64decode":
                word = base64.b64decode(word)
            if m == "urlencode":
                word = urllib.parse.quote(word.decode('l1')).encode('l1')
            if m == "urldecode":
                word = urllib.parse.unquote(
                    word.encode('l1'), encoding='l1'
                ).encode('l1')
            if m == "reverse":
                word = word[::-1]
            if m == "utf-16-confusion-encode":
                word = word.decode("utf-16").encode("latin1")
            if m == "utf-16-confusion-decode":
                word = word.decode("latin1").encode("utf-16")

        assert type(word) is bytes
        return word

    def communicate(self, inp, **kwargs):
        if self.input_method == "stdin":
            with self.run_challenge(**kwargs) as process:
                process.send(inp)
                return process.readall()
        elif self.input_method == "fixedfile":
            with open(self.input_filename, "wb") as o:
                o.write(inp)
            with self.run_challenge(**kwargs) as process:
                r = process.readall()
            os.unlink(self.input_filename)
            return r
        elif self.input_method == "argfile":
            with open("asdf", "wb") as o:
                o.write(inp)
            with self.run_challenge(argv=["asdf"], **kwargs) as process:
                r = process.readall()
                os.unlink("asdf")
                return r

    def verify(self, **kwargs):
        assert self.flag in self.communicate(self.mutate(self.mutate(
            self.password, self.reference_mutators
        ), self.input_mutators, invert=True), **kwargs)

        assert self.flag not in self.communicate(b"asdf", **kwargs)

    def render(self, *args, **kwargs):
        assert type(getattr(self, "password", b"")) is bytes
        return super().render(*args, **kwargs)

#class PasswordCheckerBytes(PasswordCheckerSvH):
#   input_method = "argfile"
#   reference_method = "hardcoded"
#   pw_type = "bytes"
#
#class PasswordCheckerHex(PasswordCheckerSvH):
#   reference_mutators = [ "hexdecode" ]
#
#class PasswordCheckerHexInput(PasswordCheckerSvH):
#   input_mutators = [ "hexdecode" ]
#
#class PasswordCheckerHexReverse(PasswordCheckerSvH):
#   reference_mutators = [ "hexdecode", "reverse" ]
#
#class PasswordCheckerHexReverseNibbles(PasswordCheckerSvH):
#   reference_mutators = [ "reverse", "hexdecode" ]
#
#class PasswordCheckerHexInputReverseNibbles(PasswordCheckerSvH):
#   input_mutators = [ "reverse", "hexdecode" ]
