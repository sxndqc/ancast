def strinset(node1, node2, rel):
    if rel in {"r", "dn", "dp"}:
        return str(node1)+"|"+str(node2)+"|"+rel
    elif rel == "up":
        return str(node2)+"|"+str(node1)+"|"+"dn"
    elif rel in {"sv", "sn", "o"}:
        if node1 < node2:
            return str(node1)+"|"+str(node2)+"|"+rel
        else:
            return str(node2)+"|"+str(node1)+"|"+rel
    else:
        raise TypeError

def comprel(rel1, rel2):
    if   (rel1 == "r") and (rel2 == "r"):
        return "r", False
    elif (rel1 == "r") and (rel2 == "dn"):
        return "r", False
    elif (rel1 == "up") and (rel2 == "r"):
        return "r", False
    elif (rel1 == "up") and (rel2 == "up"):
        return "up", False
    elif (rel1 == "dn") and (rel2 == "dn"):
        return "dn", False
    elif (rel1 == "sv") and (rel2 == "sv"):
        return "sv", False
    elif (rel1 == "sn") and (rel2 == "sn"):
        return "sn", False
    elif (rel1 in {"sn", "sv"}) and (rel2 == "dn"):
        return "dn", False
    elif (rel1 in {"sn", "sv"}) and (rel2 == "up"):
        return "up", False
    elif (rel1 == "dn") and (rel2 in {"sn", "sv"}):
        return "dn", False
    elif (rel1 == "up") and (rel2 in {"sn", "sv"}):
        return "up", False
    elif (rel1 == "sn") and (rel2 == "sv"):
        return "sn", True
    elif (rel1 == "sv") and (rel2 == "sn"):
        return "sv", True
    elif (rel1 == "ref"):          # at begining and accept every relation include overlap and depends-on
        return rel2, False
    else:
        return None, False

def disjoint_head(fa, i):
    if i not in fa.keys():
        fa[i] = i
        return i
    else:
        while fa[fa[i]] != fa[i]:
            fa[i] = fa[fa[i]]
        return fa[i]

def get_cluster(graph):
    
    """
    The existence of non-transitivity makes it necessary to start a DFS from every node, for example, a coref go to superset and go to another subset, this does not hold for transitive anymore, but it is a cluster. The cluster is a method to avoid repetitive counting of any nodes.
    If a node does not have a cluster yet, it will be assigned a new cluster. As long as it reaches an existing cluster, its current cluster will be assimilated by the existing cluster, and the cluster size will increase by one, and this node will be assigned to that existing cluster.
    But we'll leave this step to the final step. Now each node will form a separate cluster itself.
    
    There is also another problem with dealing with cycles: if there are cycles, if the relation is not the same as before, then there is inconsistency.
    """
    
    node2cluster = {}
    stack = []
    fa = {}
    whole_set = set()
    inconsistant_pairs = set()
    circular_nodes = set()
    wrong_coref_triples = set()
    
    for start_node in graph.keys():
        
        stack.append((start_node, "ref"))
        this_cluster = set()
        visited_nodes = set()
        if start_node not in fa:          # init
            fa[start_node] = start_node
        else:
            fa[start_node] = disjoint_head(fa, start_node)
        while stack:
            now, nowrel = stack.pop()
            visited_nodes.add(now)
            # all nodes visited should be marked as visited, including terminal nodes
            for next_node, next_rel in graph[now]:
                # the trick here is to refresh the disjoint head of all nodes to the new one
                fa[disjoint_head(fa, next_node)] = fa[start_node]                         # we must change its head, not itself. Any connected node will be considered in the same cluster, but not necessarily transitive
                updated_rel = comprel(nowrel, next_rel)
                if updated_rel[1]:
                    wrong_coref_triples.add((start_node, now, next_node))
                if updated_rel[0]:                                                     # ensure that the next node is viable from current standing
                    # it should be that: visited nodes relations are recorded but not added to stack
                    if (next_node not in visited_nodes):
                        this_cluster.add(strinset(start_node, next_node, updated_rel[0]))   # add to the relations                    
                        if next_node in graph.keys():                        # if a node is the final node of a chain
                            stack.append((next_node, updated_rel[0])) # later it will also be added
                        else:
                            visited_nodes.add(next_node)
                    else: 
                        # next_node visited, need to check whether contradictory
                        if (start_node != next_node):
                            if (strinset(start_node, next_node, updated_rel[0]) not in this_cluster): 
                            # print(f"Inconsistency detected in node pair {start_node} and {next_node}")
                                inconsistant_pairs.add((start_node, next_node))
                                this_cluster.add(strinset(start_node, next_node, updated_rel[0]))
                                # or else they should have the same relationship
                        else:
                            if updated_rel[0] not in {"sn", "sv", "ref"}:
                                # print(f"Circular relations in node {start_node}!")   
                                circular_nodes.add((start_node, ))
                                this_cluster.add(strinset(start_node, next_node, updated_rel[0]))

            # the reason why we need to loop through all nodes is some nodes after "overlap" or "depends-on" are neither in visited_nodes nor updated, and if they are used next time, their information should serve as gold, which is hazadous; if they are not looped through, ultimately they need also be updated

        node2cluster[start_node] = [this_cluster, visited_nodes] 
    
    for node in fa.keys():
        if fa[fa[node]] != fa[node]:
            fa[node] = disjoint_head(fa, node)  
    
    for node in graph.keys():
        whole_set.update(node2cluster[node][0])
        if fa[node] != node:
            node2cluster[fa[node]][0].update(node2cluster[node][0])
            node2cluster[fa[node]][1].update(node2cluster[node][1])
            del node2cluster[node]

    return node2cluster.values(), whole_set, inconsistant_pairs, circular_nodes, wrong_coref_triples

if __name__ == "__main__":
    
    edges = {
    1: [(5, "up"), (3, "sn"), (2, "sn")],
    3: [(1, "sn"), (6, "dn")],
    6: [(3, "up"), (5, "sn")],
    5: [(4, "sn"), (6, "sn"), (1, "dn")],
    2: [(1, "sn")], 
    4: [(9, "up"), (5, "sn")],
    9: [(4, "dn")]
    }

    clusters = get_cluster(edges)
    for cluster in clusters:
        print(cluster)

