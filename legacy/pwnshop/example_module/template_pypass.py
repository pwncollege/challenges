#!/opt/pwn.college/python

if input("Password? ").strip() == "{{challenge.password}}":
    print(open("/flag").read())
else:
    print("Nope")
