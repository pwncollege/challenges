import pwnlib.tubes

from .env import Environment

class BareEnvironment(Environment):
	def start(self):
		pass

	def stop(self):
		pass

	def process(self, *args, user=None, **kwargs): #pylint:disable=unused-argument
		return pwnlib.tubes.process.process(*args, **kwargs)

	def read_file(self, filename, **kwargs): #pylint:disable=unused-argument
		return open(filename, "rb").read()

	def write_file(self, filename, contents, chown=None, **kwargs): #pylint:disable=unused-argument
		with open(filename, "wb") as o:
			o.write(contents)

	def install(self, what): #pylint:disable=unused-argument
		pass

	@property
	def hostname(self):
		return "localhost"
