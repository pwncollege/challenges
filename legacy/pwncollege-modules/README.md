# modules for pwncollege

```
apt install python3-dev python3-pip build-essential libcapstone-dev libseccomp-dev libssl-dev docker
pip install pwnshop
cd pwncollege_modules

# individual shenanigans
pwnshop list
pwnshop render BabyMemBasicBufferOverflow
pwnshop verify BabyMemBasicBufferOverflow
pwnshop build BabyMemBasicBufferOverflow -o babymem-basic-bo

# actual deployment
pwnshop apply ~/pwncollege/introduction-to-cybersecurity-dojo/reverse-engineering/pwnshop.yml

# concurrent builds
pwnshop apply ~/pwncollege/introduction-to-cybersecurity-dojo/reverse-engineering/pwnshop.yml --mp
```
