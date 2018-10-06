import re
import random
import string

def randomword(length):
   letters = string.ascii_lowercase
   return ''.join(random.choice(letters) for i in range(length))


def repl(name):
    return "<string>%s</string>" % randomword(len(name[1]))

with open("in.xml", "r") as f:
    with open("out.xml", "w") as o:
        for line in f:
            if "<key>Name</key>" in line:
                line = re.sub(r'<string>(.*?)</string>', repl, line)
            o.write(line)
