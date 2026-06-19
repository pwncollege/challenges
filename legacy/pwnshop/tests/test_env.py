import pwnshop

def test_dockerenv():
	d = pwnshop.DockerEnvironment(image="ubuntu")
	d.start()
	assert d.process("echo -n hi", shell=True).read() == b"hi"
	assert d.process("echo -n bye", shell=True).read() == b"bye"
	assert d.system("exit 1") == 1
