from word import *
import random
random.seed(13681)
   
class Sentence:
    
    # @timer_decorator
    def __init__(self, sent, semantic_text, alignment, sent_num, format, parse_tags = {"explicit"}):
        self.text = sent
        self.invalid = False
        self.parse_tags = parse_tags
        self.head = None # Word()
        self.sent_num = sent_num
        self.alignment = None
        self.var2node = None # dict()
        self.umr_text = semantic_text
        self.semantic_text = semantic_text
        self.alignment = alignment # dict()
        try:
            self.head, self.var2node = self.parse(semantic_text, format)
        except Exception as e:
            print(f"Ignoring Sentence {self.sent_num} because {e} \n Content: {self.text}")
            self.invalid = True
        if get_reify and not self.invalid:
            self.var2node = self.reify()

    
    def reify(self):
        """
        Reification has a semantic closeness chain:
        have-polarity-91 is the most close to the core semantic of the verb
        ``He didn't run for 5 times, so he didn't pass yesterday.''
        :cause should be added to have-polarity-91 instead of qualified;
        have-polarity-91 should also have "5 times" as lower level
        
        (p / pass
            :ARG0 (h / he)
            :polarity -
            :temporal (y / yesterday)
            :cause (r / run
                :ARG0 h
                :frequency 5
                :polarity -))
        
        actually goes to, which is
        
        ``That he did not run for 5 times causes his yesterday's failure to pass. ''
        
        (h1 / have-cause-91
            :ARG1 (ht / have-temporal-91
                :ARG1 (h2 / have-polarity-91
                    :ARG1 (p / pass
                        :ARG0 (h / he))
                    :ARG2 -)
                :ARG2 (y / yesterday))
            :ARG2 (h3 / have-polarity-91
                :ARG1 (h4 / have-frequency-91
                    :ARG1 (r / run)
                    :ARG2 5)
                :ARG2 - ))
                
        but it can also be:
        
        ``That he did not run for 5 times causes his failure, which happened yesterday.''
                
        (h1 / have-cause-91
            :ARG1 (h2 / have-polarity-91
                :ARG1 (p / pass
                    :ARG0 (h / he))
                :ARG2 -)
                :ARG1-of (ht / have-temporal-91
                    :ARG2 (y / yesterday)))
            :ARG2 (h3 / have-polarity-91
                :ARG1 (h4 / have-frequency-91
                    :ARG1 (r / run)
                    :ARG2 5)
                :ARG2 - ))
                
        But the sentence is slightly ambiguous, which can also be 
        ``For 5 times, he did not run, so yesterday he failed / so he failed, which happened yesterday.''    
        
        This is the related to semantics.
        
        ``He did not watch the movie for 3 hours yesterday.''
        ``He has not wached a movie for 3 years.''
        
        The former one, hierarchical: have-temporal-91 (yesterday) -> have-polarity-91(did not) -> have-duration-91(3 hours)
        The latter one, hierarchical: have-duration-91 (3 years) -> have-polarity-91(has not) 
        
        Well, from James' point of view, the order of a tree matters, and the type of nodes also matter, so only events and states are concatenatable, and that all "decendant nodes" should be computed before hand.
        
        """
        def load_reification_relations(file_name):
            f = open(file_name, "r")
            return eval(f.readline().strip())

        reification_relations = load_reification_relations(get_absolute_path("utils",'reification_relations.txt'))
        arrived = set()
        q = [self.head]
        new_var2node = {}
        
        hcnt = 1
        
        while q:
            c = q.pop(0)
            arrived.add(c)
            new_var2node[c.var] = c
            all_relations_of_c = list(c.relations.values())
            for rs in all_relations_of_c:
                for r in rs:
                    target = r[c][0]
                    if target not in arrived:
                        if isinstance(target, Word) and (target not in q):
                            q.append(target)
                        if r.name in reification_relations.keys():
                            rconcept = "-".join(reification_relations[r.name].split("-")[:-1])
                            rsense   = int(reification_relations[r.name].split("-")[-1])
                            while ("h"+str(hcnt) in self.var2node.keys()) or ("h"+str(hcnt) in new_var2node.keys()):
                                hcnt += 1
                            new_node = Word(raw_name = rconcept, var = "h"+str(hcnt), sense_id = rsense)
                            
                            new_node[("ARG1", {"reified", "explicit"})] = r.predicate
                            new_node[("ARG2", {"reified", "explicit"})] = r.argument
                            
                            arrived.add(new_node)
                            r.tags.add("unreified")
                            new_var2node["h"+str(hcnt)] = new_node
                        else:
                            continue
                            
        
        return new_var2node
    
    # @timer_decorator
    def parse(self, semantic_text, format):

        void_var = defaultdict(list)
        var2node = {}
        
        sense_re = re.compile(r"-[0-9]{2}")

        def parse_brackets(text, i):
            result = []
            
            bracket_match = False
            
            while i < len(text):
                if text[i] == '(':
                    cur_node, i = parse_var_content(text, i + 1)
                    result.append(cur_node)
                elif text[i] == ')':
                    i += 1
                    bracket_match = True
                    break
                else:
                    i += 1
            try:
                assert len(result) == 1, f"Multiple heads identified in semantic graph in sentence {self.sent_num}!"
            except AssertionError as error:
                print(f"Format Error: {error.args[0]}")
                raise
            try:
                assert bracket_match, f"Brackets aren't matched, please check the format in semantic graph in {self.sent_num}!"
            except AssertionError as error:
                print(f"Format Error: {error.args[0]}")
                raise
            
            return cur_node, i
        
        # @timer_decorator
        def parse_var_content(text, i):

            head = re.search(r'([a-z0-9_\-]+\s*\/\s*[^)\s]+)', text[i:]).group(1)   # 右括号或空格前所有字符
            var , txt = head.split("/")
            var = var.strip()
            txt = txt.strip()
            
            sense_pos_match = sense_re.search(txt)
            
            if sense_pos_match:
                pos = sense_pos_match.span()
                sense_id = int(txt[pos[0]+1:pos[1]])
                real_name = txt[:pos[0]]
            else:
                
                sense_id = 0               
                real_name = txt
            
            i += len(head) 

            this_node = Word(raw_name = real_name, var = var, sense_id = sense_id) 
            
            try:
                assert var not in var2node, "Duplicated variable declaration, ignoring new declaration." 
                var2node[var] = this_node 
            except AssertionError as e:
                warnings.warn(str(e), category=RuntimeWarning)

            # early-reentrancy
            if var in void_var.keys():
                for node, rel in void_var[var]:
                    node[(rel, self.parse_tags.copy())] = this_node
                del void_var[var]
                
            while (i < len(text)) and (text[i] != ')'):
                if text[i] == ':':
                    voided_var = False
                    
                    space_1 = text.find(' ', i)
                    tab_1   = text.find('\t', i)
                    
                    end = space_1 if space_1 != -1 else tab_1
                    relation = text[i + 1:end]
                    i = end
                    
                    while (text[i] == ' ') or (text[i] == '\t'):
                        i += 1

                    if text[i] == '(':
                        sub_node, end = parse_brackets(text, i)
                        
                        
                    elif text[i] == '"':
                        
                        end = text.find('"', i+1)
                        text_part = text[i+1:end]
                        
                        # this is an ill-formed scene where variables are quoted
                        
                        if text_part in var2node.keys():
                            sub_node = var2node[text_part]
                            print(f"Quoted reentrancy handled in sentence {self.sent_num}")
                        else:
                            sub_node = Attribute(text_part, quoted=True)
                    else:
                        
                        firstspace = text.find(' ', i)
                        firstspace = 1e10 if firstspace == -1 else firstspace
                        firsttab = text.find('\t', i)
                        firsttab = 1e10 if firsttab == -1 else firsttab
                        firstline = text.find('\n', i)
                        firstline = 1e10 if firstline == -1 else firstline
                        
                        next_space = min(firstline, firsttab, firstspace)
                        next_right_bracket = text.find(')', i)

                        if next_right_bracket==-1:
                            next_right_bracket = 1e10
                        
                        end = min(next_space, next_right_bracket)

                        tt = text[i:end].strip()
                        
                        if tt in var2node.keys():
                            
                            # if it is a valid re-entrancy
                            
                            sub_node = var2node[tt]
                            
                        elif (re.fullmatch(r"s[0-9]+[a-z]+[0-9]*", tt) and (format == "umr")) or \
                             ((format == "amr") and (tt not in {"imperative", "expressive"}) and (not re.fullmatch(r"^[0-9.:+-]+$", tt))):
                            
                            # handling of early reentrancy, where the variable is not declared yet
                            
                            void_var[tt].append((this_node, relation))
                            voided_var = True

                        else:
                            # attributes are not quoted.
                            sub_node = Attribute(tt)
                            
                    i = end
    
                    if not voided_var:
                        this_node[(relation, self.parse_tags.copy())] = sub_node
                    
                else:
                    if re.match(r"[a-z0-9]", text[i]):
                        print(text[i-5:i+5])
                        raise RuntimeError(f"a colon is missing in {self.sent_num}.")
                    
                    i += 1
                    
            return this_node, i
        
        if len(void_var)>0:
            for v in void_var.keys():
                print(v + " is not specified!")
                
                # Leave the unspecified variable out for now 
        
        return parse_brackets(semantic_text, 0)[0], var2node # [1] is "i"
    
    def generate_umr_text(self, random_head=False):
        
        if random_head:
            head = random.choice(list(self.var2node.values()))
        else:
            head = self.head

        return f"# ::id {self.sent_num}\n# ::snt {self.text}\n{ head.generate_umr(level = 0, sent_var = '', var_list = {head.var}, rel_set = set()) }\n\n"