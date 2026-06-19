#!/opt/pwn.college/python

import termios
import random
import struct
import string
import sys
import os


class CIMG_NORMAL:
    MAGIC = b"cIMG"
    RENDER_FRAME =  struct.pack("<H", 1)
    RENDER_PATCH =  struct.pack("<H", 2)
    CREATE_SPRITE = struct.pack("<H", 3)
    RENDER_SPRITE = struct.pack("<H", 4)
    LOAD_SPRITE =   struct.pack("<H", 5)
    FLUSH =         struct.pack("<H", 6)
    SLEEP =         struct.pack("<H", 7)

class CIMG_1337(CIMG_NORMAL):
    MAGIC = b"CNNR"

class GraphicsEngine:
    def __init__(self, width, height, cimg_version=4, cimg_ops=CIMG_1337):
        self.num_sprites = 0
        self.ops = cimg_ops
        self.width = width
        self.height = height
        self.output = os.fdopen(1, 'wb', buffering=0)

        self.output.write(
            self.ops.MAGIC +
            struct.pack("<H", cimg_version) +
            bytes([width, height]) +
            b"\xff\xff\xff\xff"
        )

    def render_frame_monochrome(self, lines, r=0xff, g=0xc6, b=0x27):
        self.output.write(
            self.ops.RENDER_FRAME +
            b"".join(bytes([r, g, b, c]) for c in b"".join(lines))
        )

    def render_patch_monochrome(self, lines, x, y, r=0xff, g=0xc6, b=0x27):
        assert all(b >= 20 and b <= 0x7e for b in b"".join(lines))
        self.output.write(
            self.ops.RENDER_PATCH +
            bytes([x, y, len(lines[0]), len(lines)]) +
            b"".join(bytes([r, g, b, c]) for c in b"".join(lines))
        )

    def create_sprite(self, lines, num=None):
        if num is None:
            num = self.num_sprites
            self.num_sprites += 1

        self.output.write(
            self.ops.CREATE_SPRITE +
            bytes([num, len(lines[0]), len(lines)]) +
            b"".join(lines)
        )
        return num

    def render_sprite(self, num, x, y, tile_x=1, tile_y=1, r=0x8c, g=0x1d, b=0x40, t=" "):
        self.output.write(
            self.ops.RENDER_SPRITE + bytes([num, r, g, b, x, y, tile_x, tile_y, ord(t)])
        )

    def flush(self, clear=True):
        self.output.write(self.ops.FLUSH + bytes([clear]))

    def sleep(self, ms):
        self.output.write(self.ops.SLEEP + struct.pack("<I", ms))

    def blank(self):
        self.render_patch_monochrome([ b" "*self.width ]*self.height, 1, 1)
        self.flush()

    def animate_text(self, text, x, y, r=None, g=None, b=None, interval=20):
        for i,c in enumerate(text):
            self.render_patch_monochrome(
                [bytes([ord(c)])], x+i, y,
                r=random.randrange(128, 256) if r is None else r,
                g=random.randrange(128, 256) if g is None else g,
                b=random.randrange(128, 256) if b is None else b
            )
            self.flush()
            self.sleep(interval)

class InputEngine:
    # adapted from https://github.com/magmax/python-readchar/blob/master/readchar/_posix_read.py
    @staticmethod
    def readchar():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        term = termios.tcgetattr(fd)
        try:
            term[3] &= ~(termios.ICANON | termios.ECHO | termios.IGNBRK | termios.BRKINT)
            termios.tcsetattr(fd, termios.TCSAFLUSH, term)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def game():
    w = 70
    h = 20
    x = random.randrange(w)
    y = random.randrange(h)

    victory = False

    kb = InputEngine()
    screen = GraphicsEngine(w, h, cimg_ops=CIMG_NORMAL if "NOFLAG" in sys.argv else CIMG_1337)
    our_sprite = screen.create_sprite([ b"\\o/", b" ^ "])

    screen.render_frame_monochrome([ b"#"*(w) ]*(h), r=255, g=255, b=255)
    screen.render_patch_monochrome([ b" "*(w-2) ]*(h-2), 1, 1)
    screen.flush()

    screen.animate_text("WELCOME TO THE EPIC QUEST FOR THE FLAG", 4, 4)
    screen.animate_text("INSTRUCTIONS:", 4, 10)
    screen.animate_text("- w: UP", 4, 11)
    screen.animate_text("- a: LEFT", 4, 12)
    screen.animate_text("- s: DOWN", 4, 13)
    screen.animate_text("- d: RIGHT", 4, 14)
    screen.animate_text("- q: QUIT", 4, 15)
    screen.animate_text("- l: LOOK", 4, 16)
    screen.animate_text("YOUR GOAL: UNCOVER THE FLAG", 4, 17)
    screen.animate_text("PRESS ANY KEY TO BEGIN", 8, 18)
    if kb.readchar() in ("q", "\x03"):
        return

    screen.blank()

    try:
        if "NOFLAG" in sys.argv:
            flag = b"TEST"
        else:
            flag = open("/flag", "rb").read().strip()
    except FileNotFoundError:
        flag = b"ERROR: /flag NOT FOUND"
    except PermissionError:
        flag = b"ERROR: /flag permission denied"

    hidden_bytes = [ bytes([b]) for b in flag ][::-1]

    hidden_x = random.randrange(w)
    hidden_y = random.randrange(h)
    revealed_bytes = [ ]

    bomb_x = random.randrange(w)
    bomb_y = random.randrange(h)
    while bomb_x in (x, x+1, x+2) and bomb_y in (y, y+1):
        bomb_x = random.randrange(w)
        bomb_y = random.randrange(h)

    key = ""
    while True:
        # quit on q or ctrl-c
        if key == "q" or key == "\x03":
            break

        # move
        if key == "w": y = (y-1)%h
        if key == "a": x = (x-1)%w
        if key == "s": y = (y+1)%h
        if key == "d": x = (x+1)%w

        # check bomb
        if bomb_x in (x, x+1, x+2) and bomb_y in (y, y+1):
            screen.blank()
            screen.animate_text("~~~~~ BOOOOOOOOM ~~~~~~", x, y)
            break

        # uncover flag
        if hidden_bytes and key == "l" and hidden_x in (x, x+1, x+2) and hidden_y in (y, y+1):
            revealed_bytes.append([
                hidden_x, hidden_y,
                random.randrange(128, 256), random.randrange(128, 256), random.randrange(128, 256),
                hidden_bytes.pop()
            ])
            bomb_x = random.randrange(w)
            bomb_y = random.randrange(h)
            while bomb_x in (x, x+1, x+2) and bomb_y in (y, y+1):
                bomb_x = random.randrange(w)
                bomb_y = random.randrange(h)
            prev_hidden_x = hidden_x
            prev_hidden_y = hidden_y
            while hidden_x == prev_hidden_x and hidden_y == prev_hidden_y:
                hidden_x = (bomb_x+random.randrange(w-1))%w
                hidden_y = (bomb_y+random.randrange(h-1))%h

        # render everyone
        screen.blank()
        correct_bytes = ''
        for rx,ry,r,g,b,c in revealed_bytes:
            screen.render_patch_monochrome([c], rx, ry, r=r, g=g, b=b)
            correct_bytes += str(c.decode())
        if hidden_bytes:
            screen.render_patch_monochrome(
                [b"?"], hidden_x, hidden_y,
                r=random.randrange(256), g=random.randrange(256), b=random.randrange(256)
            )
        else:
            try:
                while True:
                    screen.animate_text("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", 10, hidden_y)
                    screen.animate_text("!!! CONGRATULATIONS, YOU DID IT !!!", 10, hidden_y + 1)
                    screen.animate_text(correct_bytes, 10, hidden_y + 2)
                    screen.animate_text("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", 10, hidden_y + 1)
            except KeyboardInterrupt:
                print(flag.decode(), file=sys.stderr)  # Print decoded flag to stderr
                break

        screen.render_patch_monochrome([b"B"], bomb_x, bomb_y)
        screen.render_sprite(our_sprite, x, y)
        screen.flush()

        key = kb.readchar()

if __name__ == "__main__":
    game()
