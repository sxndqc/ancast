import time
import numpy as np
from param import *
import warnings
import re
import os
    
def string_sim(str1a, str2a):
    
    str1 = str1a.lower()
    str2 = str2a.lower()
    
    if (str1 not in str2) and (str2 not in str1):
        return 0.0
    elif str1 in str2:
        return len(str1) / len(str2)
    elif str2 in str1:
        return len(str2) / len(str1)
    else:
        raise NotImplementedError

def jaccard_sim(set1, set2):
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    jaccard_index = len(intersection) / len(union) if union else 0
    return jaccard_index
    
def name_sim(str1, str2, sense_sim):

    return string_sim(str1, str2) * (1 + sense_coefficient * (sense_sim - 1))

def rel_weight(a, b):
    return np.sqrt(a*b) + 1

def get_argcnt(edge_matrix, node):
    node_set = set()
    q = [node]
    while q:
        c = q.pop(0)
        nexts = np.where(edge_matrix[c] > 0)
        for i in nexts[0].tolist():
            if (i not in node_set):
                node_set.add(i)
                q.append(i)
    return len(node_set)
    
def get_children(edge_matrix, from_node, to_node):
    # traverse, one node counted twice
    from_node_set = set()
    to_node_set = set()
    q = [from_node]
    while q:
        c = q.pop(0)
        nexts = np.where(edge_matrix[c] > 0)
        for i in nexts:
            if (i not in from_node_set) and (i != to_node):
                from_node_set.add(i)
                q.append(i)
        q = [from_node]
    q = [to_node]
    while q:
        c = q.pop(0)
        nexts = np.where(edge_matrix[c] > 0)
        for i in nexts:
            if (i not in to_node_set):
                to_node_set.add(i)
                q.append(i)
    return len(from_node_set), len(to_node_set)

def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        print(f"{func.__qualname__} uses {duration:.5f}")
        return result
    return wrapper

def protected_divide(a, b):
    if b==0:
        return 0.0
    else:
        return a / b
    
def parse_alignment(alignment_text):
    ras = {}
    if not alignment_text:
        return ras
    als = alignment_text.strip().split("\n")    
    for l in als:
        if "alignment" in l:
            continue
        v, al = l.strip().split(":")
        ras[v] = al.strip()
    return ras
    
# ================== vocabulary operations =====================
 
def add_vocab(vocab, name, sense_id, sense):

    if name not in vocab.keys():
        vocab[name] = {}
    
    if sense_id in vocab[name].keys():
        if vocab[name][sense_id] != sense:
            print(name)
            print("Original ", vocab[name])
            print("New ",sense)
            sense_id += 10
        
    vocab[name][sense_id] = sense

# def add_abstract_vocab(name, all_sense):
    
#     if name not i
    
#     if name not in abstract_vocab.keys():
#         abstract_vocab[name] = all_sense
#     else:
#         print(name+" already added!")  
# there is -92 sense，not all identical

def dump_vocab(vocab, filename):
    with open(filename, "w") as f:
        f.write(str(vocab))

def load_vocab(filename, vocab):
    with open(filename, "r") as f:
        l = f.readline()
        vocab = eval(l)

def dump_abstract_vocab(abstract_vocab, filename):
    with open(filename, "w") as f:
        f.write(str(abstract_vocab))

def load_abstract_vocab(filename):
    with open(filename, "r") as f:
        return eval(f.readline().strip())

def rel_hash(word1, rel, word2):
    return word1.var+"-"+rel+"-"+word2.var, word2.var+"-"+reverse(rel)+"-"+word1.var

def get_absolute_path(subdir, file_name):
    current_dir_path = os.path.dirname(os.path.abspath(__file__))
    subdir_path = os.path.join(current_dir_path, subdir)
    file_path = os.path.join(subdir_path, file_name)
    return file_path

vocab = {}

if get_reify:
    abstract_vocab = load_abstract_vocab(get_absolute_path("utils", 'abstract_vocab.txt'))
else:
    abstract_vocab = {}
# ======================== relation ===========================

def load_reverse(file):
    with open(file, "r") as f:
        l = []
        for line in f:
            l.append(line.strip)
        l = "".join(l)
        reverse_list = eval(l)

def reverse(rel):
    if rel[-3:] == "-of":
        return rel[:-3]
    else:
        return rel + "-of"

    # return reverse_list[rel]

def is_reverse(rel):
    if rel == "mod":        # mod is "domain-of"
        return True
    elif rel == "mod-of":
        return False
    elif rel[-3:] == "-of":
        return True
    else:
        return False
    
# ================= for label match =================

def rel_label_set_comp(rel_label_set, target_label_set):
    """
    For possible fine-grained match.
    """
    set_a = rel_label_set
    set_b = target_label_set
    return len(set_a & set_b) # simply count fully equal labels