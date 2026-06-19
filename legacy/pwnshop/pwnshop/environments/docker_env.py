import tempfile
import pwnlib.tubes.process
import docker
import shlex
import os

from .env import Environment

class docker_process(pwnlib.tubes.process.process):
	def __init__(
		self, argv=None,
		container_name=None, user=None, work_dir=None, suffix="",
		shell=False, executable=None, cwd=None, env=None, aslr=None, setuid=None, alarm=None,
		**kwargs
	):
		assert container_name is not None, "must provide container name" # don't want to mess up the arg order everyone is used to
		assert aslr is None, "docker_process doesn't support aslr kwarg"
		assert executable is None, "docker_process doesn't support executable kwarg"
		assert setuid is None, "docker_process doesn't support setuid kwarg"
		assert not alarm or not shell, "alarm is not supported with shell=True"

		work_dir = work_dir or tempfile.mkdtemp()
		self.container_name = container_name


		docker_cmd = [
			"docker", "exec", *(["-u", str(user)] if user is not None else []), "-i", "-w", cwd or work_dir, self.container_name, "/bin/bash"
		]
		super().__init__(docker_cmd, **kwargs)

		env = env or { }
		for k,v in env.items():
			kstr = k.decode('latin1') if type(k) is bytes else k
			with open(f"{work_dir}/.pwnshop-env-var", "wb") as o:
				o.write(v.encode('latin1') if type(v) is str else v)
			self.sendline(f"read {kstr} < {work_dir}/.pwnshop-env-var; export {kstr}; echo")
			self.readline()
			os.unlink(f"{work_dir}/.pwnshop-env-var")

		assert not self.clean()

		self.sendline("echo PWNSHOP-PID:$$")
		self.readuntil("PWNSHOP-PID:")
		self.actual_pid = int(self.readline().strip())

		if alarm:
			self.sendline(f"( sleep {alarm}; kill -ALRM {self.actual_pid} ) &")

		self.sendline("echo PWNSHOP-READY")
		if shell:
			actual_cmd = "exec bash -c " + shlex.quote(argv)
		else:
			actual_cmd = "exec " + shlex.join(argv)
		self.sendline(actual_cmd + suffix)
		self.readuntil("PWNSHOP-READY\n")

	def kill(self):
		pwnlib.tubes.process.process(f"docker exec -u root {self.container_name} kill -9 -- -{self.actual_pid}", shell=True).readall()

	def __exit__(self, *args, **kwargs):
		super().__exit__(*args, **kwargs)
		self.kill()

class DockerEnvironment(Environment):
	def __init__(self, image, work_dir=None):
		self.image = image
		self.container = None
		self.work_dir = work_dir or tempfile.mkdtemp(prefix='pwnshop-')

	def start(self):
		if self.container:
			return

		client = docker.from_env()
		if ":" in self.image:
			img, tag = self.image.split(':')
		else:
			img, tag = self.image, "latest"
		#client.images.pull(img, tag=tag)

		#TODO: container life is context manager
		self.container = client.containers.run(
			img + ':' + tag,
			'sleep 300',
			user="0",
			auto_remove=True,
			detach=True,
			cap_add=["SYS_PTRACE"],
			security_opt=["seccomp=unconfined"],
			sysctls={"net.ipv4.ip_unprivileged_port_start": 1024},
			network_mode="bridge",
			ulimits = [ docker.types.Ulimit(name='core', soft=-1, hard=-1) ],
			volumes = {
				"/tmp": {"bind": "/tmp", "mode": "rw"},
				self.work_dir : {'bind': self.work_dir, 'mode': 'rw'},
				self.work_dir+"/" : {'bind': "/challenge", 'mode': 'rw'}
			}
		)

		ret, _ = self.container.exec_run(
			"/bin/bash -c 'echo 127.0.0.1 challenge.localhost "
			"hacker.localhost >> /etc/hosts'",
			user="root"
		)
		assert ret == 0

		self.container.reload()
		return self.container

	def stop(self):
		if self.container:
			self.container.kill()
		self.container = None

	def install(self, what):
		self.start()

		pkg_regex = "^(" + "|".join(what) + ")$"
		p = self.finished_process(
			f"""dpkg -l | cut -f3 -d" " | grep -E '{pkg_regex}'""",
			user="root",
			shell=True
		)
		missing = set(what) - set(p.readall().decode().strip().split("\n"))

		if missing:
			self.finished_process(
				"apt-get update",
				shell=True, check=True, user="root"
			)
			pkgs = " ".join(missing)
			p = self.finished_process(
				f"apt-get install -y {pkgs}",
				shell=True, user="root"
			)
			if p.poll() != 0:
				print("DEPENDENCY INSTALL ERROR:")
				print(p.readall().decode('latin1'))
			#p.readall()
			assert p.poll() == 0

	def process(self, *args, **kwargs):
		stdout_fds = kwargs.pop("stdout_fds", ())
		redirects = ""
		for fd in stdout_fds:
			redirects += f" {fd}>&1" #pylint:disable=consider-using-join

		suffix = kwargs.pop("suffix", "") + redirects
		return docker_process(*args, container_name=self.container.name, suffix=suffix, **kwargs)

	@property
	def hostname(self):
		return self.container.attrs['NetworkSettings']['IPAddress']

	def write_file(self, filename, contents, chown=None, **kwargs):
		assert type(contents) is bytes, "file contents must be bytes"
		t = tempfile.mktemp(dir=self.work_dir)
		with open(t, "wb") as o:
			o.write(contents)
		assert self.system(f"mv {t} {filename}", **kwargs) == 0
		if chown:
			assert self.system(f"chown {chown} {filename}", **kwargs) == 0

	def read_file(self, filename, **kwargs):
		t = tempfile.mktemp(dir=self.work_dir)
		assert self.system(f"cp {filename} {t}", **kwargs) == 0
		r = open(t, "rb").read()
		assert self.system(f"rm {t}") == 0
		return r
