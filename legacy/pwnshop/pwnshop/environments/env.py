class Environment:
	work_dir = None

	def start(self):
		raise NotImplementedError()

	def stop(self):
		raise NotImplementedError()

	def install(self, what):
		raise NotImplementedError()

	def process(self, args, **kwargs):
		raise NotImplementedError()

	def read_file(self, filename):
		raise NotImplementedError()

	def write_file(self, filename, contents, chown=None, **kwargs):
		raise NotImplementedError()

	@property
	def hostname(self):
		raise NotImplementedError()

	#
	# Canned functionality
	#

	def __enter__(self):
		self.start()
		return self

	def __exit__(self, exc_type, value, tb):
		self.stop()

	def system(self, cmd, check_blank=False, **kwargs):
		p = self.process(
			argv=cmd,
			shell=kwargs.pop("shell", True),
			**kwargs
		)
		p.wait()
		if check_blank:
			assert not p.readall()
		return p.poll()

	def finished_process(self, *args, check=False, check_blank=False, **kwargs):
		p = self.process(*args, **kwargs)
		p.wait()
		if check_blank:
			assert not p.readall()
		if check:
			assert p.poll() == 0
		return p
