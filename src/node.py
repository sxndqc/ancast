from collections import defaultdict
from param_fun import *

class Attribute(object):

    attributes = set()

    def __init__(self, raw_name, quoted=False):

        self.raw_name = raw_name
        self.name = raw_name.lower()
        self.quoted = quoted
        Attribute.attributes.add(self.name)

    def __repr__(self):
        if self.name[0] == self.name[-1] == '"':
            return self.name[1:-1]
        else:
            return self.name

    def generate_umr(self):

        if self.quoted:
            return f'"{self.name}"'
        else:
            return self.name 

# ------------ constant --------------

IMPLICIT = Attribute("implicit-argument")