from node import *

class Word():

    def __init__(self, raw_name, var, sense_id = 0):

        self.raw_name = raw_name
        self.name = raw_name.lower()
        self.var = var
        self.sense_id = sense_id
        self.relations = defaultdict(list)
        
        if self.name in vocab:
            try:
                self.sense = vocab[self.name][sense_id]
            except KeyError:
                # where a noun and a verb has the same surface form whereas the verb's propbank does not consider its noun form
                add_vocab(vocab= vocab, name= self.name, sense_id = self.sense_id, sense= {})
                self.sense = {}
            self.v = vocab
        elif self.name in abstract_vocab:
            try:
                self.sense = abstract_vocab[self.name][sense_id]
            except KeyError:
                # sometimes there are errors in annotating, like have-degree-91, which should be 92.
                add_vocab(vocab= abstract_vocab, name= self.name, sense_id = self.sense_id, sense= {})
                self.sense = {}
            self.v = abstract_vocab
        else:
            self.sense = {}
            add_vocab(vocab = vocab, name= self.name, sense_id= self.sense_id, sense= {})
            self.v = vocab
            if SENSE_ADD_DEBUG_PRINT:
                print("Adding %s No registered sense, please initialize!"%(self.name))

        # don't know its rel yet
        
        for rel in self.v[self.name][sense_id].keys():
            # set them to implicit-argument
            self[(rel, {"implicit"})] = IMPLICIT
            
        self.sub_vars = {}
        
    def labels():

        raise NotImplementedError

# ********************************* relational operations **************************

    def __getitem__(self, rel_str):
        
        if rel_str == "ATTRIBUTES":
            rs = []
            for r in self.relations.keys():
                rs += self.relations[r] 
            
            rel2attr = {}
            
            for r in rs:
                if isinstance(r.argument, Attribute) and (r.tags <= allowed_tags):
                    rel2attr[r.name] = str(r.argument)
                
            # allow possible duplicated attributes
                
            return rel2attr
        
        elif rel_str == "ALL":
            rs = []
            for r in self.relations.keys():
                rs += self.relations[r]   
        else:
            rs = self.relations[rel_str]
        
        nodes = []
            
        for r in rs:
            if r.tags <= allowed_tags:
                nodes.append(r[self])
            
        return nodes

    def __setitem__(self, rel_and_tag, node):
    
        # r will be saved in reverse relation, but when output will be transformed

        rel, tags = rel_and_tag        
        r = Relation(raw_name = rel, from_node= self, to_node = node, tags = tags) # alias = )

        self.relations[rel].append(r)

        if (type(node) == Word):
            node.relations[reverse(rel)].append(r)

    def __delitem__(self, rel):
        del self.relations[rel]

    def set_multiple_node_for_one_relation(self, rel: str, nodes: list):
        for node, is_down_direction in nodes:
            self[(rel, {"explicit"})] = node
            
    def __repr__(self):
        return self.name

# ********************************* this place above *******************************************************

    def to_str(self, sent_var):

        if (self.sense_id > 0): #(len(self.v[self.name].keys())>1) or :
            return "(" + sent_var + self.var + " / " + self.name + "-{:02d}".format(self.sense_id)
        else:
            return "(" + sent_var + self.var + " / " + self.name

    def generate_umr(self, level, sent_var, var_list, rel_set, follow_old = False):

        s = []
        s.append(self.to_str(sent_var))   # "(" + self.var_name + " / " + self.name+"-0"+str(self.sense_id))
        for rel, rs in self.relations.items():

            for r in rs:
                
                node, is_down_direction, parapredicate = r[self]
                
                if follow_old and (not is_down_direction):
                    continue

                if not (r.tags <= allowed_tags):
                    continue

                if (type(node) == Attribute):  
                    s.append(" "*4 * (level + 1)+":"+rel + " "*4 + node.generate_umr())
                    continue

                r_solid = r.solidate() # the two directional relations
                if (r_solid in rel_set):
                    continue
                else:
                    rel_set.add(r_solid)

                if (node.var not in var_list):
                    var_list.add(node.var)
                    s.append(" "*4 * (level + 1)+":"+rel + " "*4 + node.generate_umr(level + 1, sent_var, var_list, rel_set))
                    # var_list.pop(), don't pop, as all previous variable should be referred.
                else:
                    s.append(" "*4 * (level + 1)+":"+rel + " "*4 + sent_var + node.var)
        
        s[-1] += ")"

        return "\n".join(s)
    
    def get_relations(self):

        rel_set = set()

        for rs in self.relations.values():
            for r in rs:
                if r.tags <= allowed_tags: 
                    rel_set.add(r.solidate())
        
        return rel_set

class Relation:

    # registered = []

    def __init__(self, raw_name, from_node, to_node, tags, alias = None):

        """
        Things to do when initilizing an instance.
        """
        
        name = raw_name.lower()
        self.raw_name = raw_name
        self.name = reverse(name) if is_reverse(name) else name  # 也就是说name肯定是predicate 到 argument的
        self.tags = tags
        
        self.role = alias
        self.vector = None
        self.focus = from_node
        self.child = to_node
        
        self.parapredicate = False if is_reverse(name) else True # 顺磁性，意思是pred-argu关系和focus-child关系一致
        
        if self.parapredicate:
            self.predicate, self.argument = self.focus, self.child
        else:
            self.predicate, self.argument = self.child, self.focus         

        if (type(to_node)==Word) and (type(from_node) == Word):
            self.between_var = True
        else:
            self.between_var = False

    def history(self):
        pass

    def __getitem__(self, node):
        """
        >>> node = Word()
        >>> self[node] = (another_node, "whether another_node is a child", "whether another_node is an argument")

        ______|_A->B__|__B-of->A__|
        r[A]  |       |           |
        ______|_B_T_T_|__B_F_T____|
        r[B]  |       |           |
        ______|_A_F_F_|__A_T_F____|
        

        """
        
        if node == self.focus:
            return (self.child, True, self.parapredicate ^ False)
        elif node == self.child:
            return (self.focus, False, self.parapredicate ^ True)
        
        
    def solidate(self):

        
        head = self.predicate
        tail = self.argument
        rel = self.name
        
        if self.between_var:
            return (head.var, rel, tail.var)
        else:
            if rel != "mod-of":
                try:
                    return (head.var, rel, str(tail))
                except AttributeError as e:
                    warnings.warn(f"Illegal head {head}, treated as string.",  category=RuntimeWarning)
            else:
                try:
                    return (str(head), rel, tail.var)
                except AttributeError as e:
                    warnings.warn(f"Illegal node {tail}, treated as string.",  category=RuntimeWarning)
                

