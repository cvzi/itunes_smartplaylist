""" Remove names from library file and replace with random strings"""
import re
import random
import string
import os

def randomword(length):
   letters = string.ascii_lowercase
   return ''.join(random.choice(letters) for i in range(length))


def repl(name):
    return "<string>%s</string>" % randomword(len(name[1]))
    
if __name__ == '__main__':
    if not os.path.isfile("in.xml"):
        print("Missing input file: `in.xml`")
        quit(2)
    
    if os.path.isfile("out.xml"):
        print("Output file already exists: `out.xml`")
        quit(3)
    
    with open("in.xml", "r") as f:
        with open("out.xml", "w") as o:
            for line in f:
                if "<key>Name</key>" in line:
                    line = re.sub(r'<string>(.*?)</string>', repl, line)
                o.write(line)

