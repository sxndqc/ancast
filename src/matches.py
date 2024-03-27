from sentence import *
from metric import *

class Match:
    
    def __init__(self, umr0, umr1):
        self.umr0 = umr0
        self.umr1 = umr1
        self.var2idx = None
        
    def draw_matrix(self, matrices):
        
        row_names = [self.umr0.var2node[self.var2idx[0][i]] for i in range(matrices[0].shape[0])]
        col_names = [self.umr1.var2node[self.var2idx[1][i]] for i in range(matrices[0].shape[1])]

        
        ncols = (len(matrices) + 1) // 2
        
        fig, axes = plt.subplots(nrows=2, ncols=ncols, figsize=(15, 8))
       
        for i, matrix in enumerate(matrices):
            im = axes[(i) // ncols, (i) % ncols].imshow(matrix, cmap='viridis', interpolation='none', vmin=0, vmax=1)
            axes[(i) // ncols, (i) % ncols].set_title(f"Iteration {i+1}")
            axes[(i) // ncols, (i) % ncols].set_xticks(range(len(col_names)))
            axes[(i) // ncols, (i) % ncols].set_xticklabels(col_names, rotation=90)
            axes[(i) // ncols, (i) % ncols].set_yticks(range(len(row_names)))
            axes[(i) // ncols, (i) % ncols].set_yticklabels(row_names)

        cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
        fig.colorbar(im, cax=cbar_ax)

        plt.tight_layout()
        plt.subplots_adjust(right=0.9)  
        plt.show()
     
    def translate_match(self, match_list, var):
        if var in match_list.keys():
            return match_list[var]
        elif var == "TOP":
            return "TOP"
        else:
            return var # if it is an Attribute, all attributes should be stored in lower case 
    
    def structural_count(self):
        
        vlist0 = self.umr0.var2node
        vlist1 = self.umr1.var2node
        
        set0 = set()
        set1 = set()
        
        for node in vlist0.values():
            set0 = set0 | node.get_relations()
        for node in vlist1.values():
            set1 = set1 | node.get_relations()
            
        if use_smatch_top:
            set0.add(("TOP", "TOP", self.var2idx[0][0]))
            set1.add(("TOP", "TOP", self.var2idx[1][0]))
        
        # translate 0-1 and compare overlap, all vars in 0 are guaranteed to be translated
        
        translated_set0 = set()
        
        for r in set0:
            translated_set0.add((self.translate_match(self.match_list01, r[0]), r[1], self.translate_match(self.match_list01,r[2])))
        
        translated_set1 = set()
        for r in set1:
            translated_set1.add((self.translate_match(self.match_list10, r[0]), r[1], self.translate_match(self.match_list10, r[2])))
        
        return len(translated_set1 & set0), len(set0), len(translated_set0 & set1), len(set1)
    
    @staticmethod
    def gname(umr, v):
        if v in umr.var2node.keys():
            return f"{v} / {str(umr.var2node[v])}"
        else:
            try:
                assert v[:4] == "NULL", "Unmatched nodes not mapped to NULL!"
            except AssertionError as e:
                print(e.args[0])
                raise
            return "null"
    
    @staticmethod
    def transform_alignment(umr):
        for x in umr.var2node.keys():
            if x in umr.alignment:
                pair_text = umr.alignment[x]
                pair = [0, 0]
                if (pair_text[0] == "0") or (pair_text[0] == "-"):
                    pair = [0, 0]
                else:
                    pair = pair_text.split("-")
                    if "undefined" in pair:
                        pair = [0, 0]
                    pair[0] = int(pair[0])
                    pair[1] = int(pair[1])
                umr.alignment[x] = pair
            else:
                umr.alignment[x] = [0,0]
                
    @staticmethod
    def transform_mapping(match_list, var2node):
        t = {}
        for key in match_list.keys():
            if match_list[key] != "null":
                t[var2node[0][key]] = var2node[1][match_list[key]]
            else:
                t[var2node[0][key]] = "null"
        return t
    
    @staticmethod
    def enhance_with_rel_label(idx, maxima, umr_idx,  var2idx, umr0, umr1):
        
        """
        Used to select the most likely pairs based on relation label similarity, when they have the same non-relational similarity.
        """
        
        max_sim = -1
        arg_max_sim = None
        label_sim = np.zeros(maxima.shape)
        umr_this = umr0 if umr_idx == 0 else umr1
        umr_that = umr1 if umr_idx == 0 else umr0
        
        rel_set_this = Match.get_rel_set(idx, var2idx[umr_idx], umr_this.var2node)
        for k, ii in enumerate(maxima):
            rel_set_that = Match.get_rel_set(ii, var2idx[1 - umr_idx], umr_that.var2node)
            temp_s = jaccard_sim(rel_set_this, rel_set_that)
            label_sim[k] = temp_s
            
        max_label_sim = np.amax(label_sim)
        if np.count_nonzero(label_sim == max_label_sim) > 1:
            return None, np.where(label_sim == max_label_sim)[0]
        else:
            return maxima[np.argmax(label_sim)], np.where(label_sim == max_label_sim)[0]
    
    @staticmethod
    def get_rel_set(idx, var2idx, var2node):
        return set(var2node[var2idx[idx]].relations.keys())

class Match_resolution(Match):
    
    # @timer_decorator
    def __init__(self, umr0, umr1, Cneighbor):
        
        super().__init__(umr0, umr1)
        # get name matrix for evaluation and anchors for iterative neighbor information
        self.Cneighbor = Cneighbor
        self.Mt01 = Metric("01")
        self.Mt10 = Metric("10")
        
        self.initial_sim, self.var2idx, self.anchors, self.name_idt = self.get_global_match(self.umr0, self.umr1, USE_ALIGNMENT)
        
        self.N_Matrices, self.outmatrix = self.get_neighbor_matrix()
        
        self.match_list01, self.match_list10, self.quality_list01, self.quality_list10 = self.iterate_anchor_and_match(self.anchors, add_asymmetric_relations=True)
        
        _, _, _, self.smatch_format_score = self.get_structural_plain_count()
        
        self.lbd_p, self.lbd_r, self.lbd_fscore, self.ulbd_fscore, self.wlbd_fscore = self.weighted_relational_overlap()
        
    def get_structural_plain_count(self):
        
        overlap0, all0, overlap1, all1 = self.structural_count()
        
        self.Mt01.assign("relation", "matched", overlap0)
        self.Mt01.assign("relation", "total",   all0)
        self.Mt10.assign("relation", "matched", overlap1)
        self.Mt10.assign("relation", "total",   all1)

        self.gp01 = self.Mt01.compute("good quality")
        self.gp10 = self.Mt10.compute("good quality")

        self.match_score01 = self.Mt01.compute("concept with bad quality")
        self.match_score10 = self.Mt01.compute("concept with bad quality")
        
        self.concept_match_fscore = protected_divide((self.match_score01 * self.match_score10 * 2) , (self.match_score01 + self.match_score10))
    
        precision = self.Mt01.compute("relation")
        recall = self.Mt10.compute("relation")
    
        if precision + recall > 0:
            sm_fscore = 2 * precision * recall / (precision + recall)
        else:
            sm_fscore = 0.0

        psm = self.Mt01.compute("smatch") 
        rsm = self.Mt10.compute("smatch")
        smatch_format_score = protected_divide(psm * rsm * 2, (psm + rsm))
        
        return precision, recall, sm_fscore, smatch_format_score

    def get_global_match(self, umr0, umr1, anchor_with_alignment = False):
        
        vlist0 = umr0.var2node
        vlist1 = umr1.var2node
        
        Match.transform_alignment(umr0)
        Match.transform_alignment(umr1)
        
        anchors = np.zeros((len(vlist0), len(vlist1)))
        initial_sim = np.zeros((len(vlist0), len(vlist1)))
        name_idt = np.zeros((len(vlist0), len(vlist1)))
        
        var2idx = ({},{})
        
        name_duplicate_0 = defaultdict(lambda: 0)
        name_duplicate_1 = defaultdict(lambda: 0)
        
        for v0 in vlist0:
            name_duplicate_0[vlist0[v0].name] += 1
        for v1 in vlist1:
            name_duplicate_1[vlist1[v1].name] += 1
        
        for i, v0 in enumerate(vlist0):
            for j, v1 in enumerate(vlist1):
                
                var2idx[0][v0] = i
                var2idx[1][v1] = j
                var2idx[0][i] = v0
                var2idx[1][j] = v1
                
                node0 = umr0.var2node[v0]
                node1 = umr1.var2node[v1]
                
                # sense check
                
                if (node0.sense_id == node1.sense_id):
                    sense_sim = 1
                else:
                    sense_sim = 0
                    
                # attribute check
                
                v0rel_attr = vlist0[v0]['ATTRIBUTES']
                v1rel_attr = vlist1[v1]['ATTRIBUTES']
                
                # "ops" would be combined into string, other attributes compared separately
                n = 0
                s = 0
                op0 = []
                for rel in v0rel_attr.keys():
                    if rel[:2] == "op":
                        op0.append(v0rel_attr[rel])
                        continue
                    if rel in v1rel_attr.keys():
                        n += 1
                        s += (v0rel_attr[rel] == v1rel_attr[rel])
                
                op1 = []
                for rel in v1rel_attr.keys():
                    if rel[:2] == "op":
                        op1.append(v1rel_attr[rel])
                        
                op0 = "".join(op0)
                op1 = "".join(op1)
                
                # final initial similarity and name similarity
                this_name_sim = name_sim(node0.name+op0, node1.name+op1, sense_sim)
                
                other_attr = s / n if n > 0 else 0
                ot_at_co = 1 if n > 0 else 0            # 不应该是attributes不一样就不算，而是没有的话就不算
                
                initial_sim[i, j] = (this_name_sim  + other_attr) / (1 + ot_at_co)
                name_idt[i, j] = (this_name_sim == 1) and (sense_sim == 1)
                # anchors
                
                # alignment
                if anchor_with_alignment:
                    min_low = min(umr0.alignment[v0][0], umr1.alignment[v1][0])
                    max_low = max(umr0.alignment[v0][0], umr1.alignment[v1][0])
                    min_high = min(umr0.alignment[v0][1], umr1.alignment[v1][1])
                    max_high = max(umr0.alignment[v0][1], umr1.alignment[v1][1])
                    
                    maximum_overlap = min_high - max_low + 1
                    maximum_range = max_high - min_low + 1
                     
                    if min_low == 0:
                        align_sim = 0                      
                    elif maximum_overlap <= 0:
                        align_sim = 1e-2                    
                    else:
                        align_sim = maximum_overlap / maximum_range # alignment可以用

                    if align_sim == 1:
                        anchors[i, j] = 1
                
                else:
                    # if both of them only appear once in the original sentence, then they are unique and anchored
                    
                    if (node0.name == node1.name) and (node0.name in umr0.text.lower()) and (node1.name in umr1.text.lower()) and (name_duplicate_0[node0.name] == 1) and (name_duplicate_1[node1.name] == 1):
                        anchors[i, j] = 1
                
        return initial_sim, var2idx, anchors, name_idt
    
    # @timer_decorator
    def get_neighbor_matrix(self,predarguRatherthanfocuschild = True, two_layer_neighbor = True):
        
        if predarguRatherthanfocuschild:
            node_idx = 2
        else:
            node_idx = 1
        
        vlist0 = self.umr0.var2node
        vlist1 = self.umr1.var2node
        
        Ain_umr0 = np.zeros((len(vlist0), len(vlist0)))
        Ain_umr1 = np.zeros((len(vlist1), len(vlist1)))
        
        Aout_umr0 = np.zeros((len(vlist0), len(vlist0)))
        Aout_umr1 = np.zeros((len(vlist1), len(vlist1)))
        
        for v0 in vlist0:
            v0idx = self.var2idx[0][v0]
            neighbors_v0 = vlist0[v0]['ALL']
            v0nb_idxes_out = [self.var2idx[0][node[0].var] for node in neighbors_v0 if (type(node[0]) == Word) and node[node_idx]]
            v0nb_idxes_in = [self.var2idx[0][node[0].var] for node in neighbors_v0 if (type(node[0]) == Word) and not node[node_idx]]
            
            Aout_umr0[v0idx][v0nb_idxes_out] = 1
            Ain_umr0[v0idx][v0nb_idxes_in]   = 1

        for v1 in vlist1.keys():
            v1idx = self.var2idx[1][v1]
            neighbors_v1 = vlist1[v1]['ALL']
            v1nb_idxes_out = [self.var2idx[1][node[0].var] for node in neighbors_v1 if (type(node[0]) == Word) and node[node_idx]]
            v1nb_idxes_in = [self.var2idx[1][node[0].var] for node in neighbors_v1 if (type(node[0]) == Word) and not node[node_idx]]
            Aout_umr1[v1idx][v1nb_idxes_out] = 1
            Ain_umr1[v1idx][v1nb_idxes_in]   = 1
                
        # adding grandparent, grandson, and sibling information
        # grandparent and grandson is square of matrix
        # in matrix A, out matrix B, then with grand informaion (A^2 + A) and (B^2 + B)
        # siblings are (AB + BA) - I (excluding itself)
        # matrix is very elegant, except that >1 need to be 1
        
        outmatrix = Aout_umr0, Aout_umr1
        
        if separate_1and2:
            M0 = np.ones(Aout_umr0.shape) - np.eye(len(vlist0)) # J - I
            M1 = np.ones(Aout_umr1.shape) - np.eye(len(vlist1))
                    
            Aout_umr0_2hop = np.matmul(Aout_umr0, Aout_umr0) * M0
            Aout_umr1_2hop = np.matmul(Aout_umr1, Aout_umr1) * M1
            Ain_umr0_2hop  = np.matmul(Ain_umr0, Ain_umr0)   * M0
            Ain_umr1_2hop  = np.matmul(Ain_umr1, Ain_umr1)   * M1
        
            Aout_umr0_2hop[Aout_umr0 > 1] = 1
            Aout_umr1_2hop[Aout_umr1 > 1] = 1
            Ain_umr0_2hop[Ain_umr0 > 1] = 1
            Ain_umr1_2hop[Ain_umr1 > 1] = 1
            
            return (Aout_umr0, Aout_umr0_2hop, Aout_umr1, Aout_umr1_2hop, Ain_umr0, Ain_umr0_2hop, Ain_umr1, Ain_umr1_2hop, 1, 1), outmatrix
            
        else:
            M0 = np.ones(Aout_umr0.shape) - np.eye(len(vlist0)) # J - I
            M1 = np.ones(Aout_umr1.shape) - np.eye(len(vlist1))
                    
            Aout_umr0 = (np.matmul(Aout_umr0, Aout_umr0) + Aout_umr0) * M0
            Aout_umr1 = (np.matmul(Aout_umr1, Aout_umr1) + Aout_umr1) * M1
            Ain_umr0  = (np.matmul(Ain_umr0, Ain_umr0)   +  Ain_umr0) * M0
            Ain_umr1  = (np.matmul(Ain_umr1, Ain_umr1)   +  Ain_umr1) * M1
        
            Aout_umr0[Aout_umr0 > 1] = 1
            Aout_umr1[Aout_umr1 > 1] = 1
            Ain_umr0[Ain_umr0 > 1] = 1
            Ain_umr1[Ain_umr1 > 1] = 1
        
            s_Aout_umr0 = Aout_umr0.sum(axis = 1)[:, np.newaxis] # how many 1 & 2-hop neighbors in total
            s_Aout_umr1 = Aout_umr1.sum(axis = 1)[np.newaxis, :]
            s_Ain_umr0 =  Ain_umr0.sum(axis = 1)[:, np.newaxis]
            s_Ain_umr1 =  Ain_umr1.sum(axis = 1)[np.newaxis, :]
            
            
            denom_out = np.minimum(s_Aout_umr0, s_Aout_umr1)   #  1 & 5 neighbors v. 2 & 2 neighbors, the former should be lower.
            denom_in  = np.minimum(s_Ain_umr0, s_Ain_umr1)
            denom_out[denom_out==0] = np.inf
            denom_in[denom_in==0]   = np.inf
            
            C_out = np.maximum(s_Aout_umr0, s_Aout_umr1) / denom_out
            C_in = np.maximum(s_Ain_umr0, s_Ain_umr1) / denom_in
            C_out[C_out==0] = np.inf
            C_in[C_in==0]  = np.inf

            return (Aout_umr0, Aout_umr1, Ain_umr0, Ain_umr1, C_out, C_in), outmatrix

    # @timer_decorator
    def incorporate_neighborhood_information(self, initial_sim, anchors, Cneighbor=1 ,  max_iterations = 50, tolerance=1e-4, alpha = 2e-1, beta = 1e-3):

        if separate_1and2:
            Aout_umr0_1hop, Aout_umr0_2hop, Aout_umr1_1hop, Aout_umr1_2hop, Ain_umr0_1hop, Ain_umr0_2hop, Ain_umr1_1hop, Ain_umr1_2hop, C_out, C_in = self.N_Matrices
        else:
            Aout_umr0, Aout_umr1, Ain_umr0, Ain_umr1, C_out, C_in = self.N_Matrices

        newsim = anchors.copy() # note that initial_sim_matrix is not necessarily a symmetric matrix!

        matrices = [newsim]
        
        for its in range(max_iterations):
            prevsim = newsim.copy()
            if separate_1and2:
            
                Sout = (Aout_umr0_1hop @ prevsim) @ Aout_umr1_1hop.T + (Aout_umr0_2hop @ prevsim) @ Aout_umr1_2hop.T
                Sin  = (Ain_umr0_1hop  @ prevsim) @  Ain_umr1_1hop.T + (Ain_umr0_2hop  @ prevsim) @  Ain_umr1_2hop.T
            
            else:
                
                Sout = (Aout_umr0 @ prevsim) @ Aout_umr1.T / C_out
                Sin  = (Ain_umr0  @ prevsim) @  Ain_umr1.T / C_in
            
            newsim = np.sqrt((Sout + 1) * (Sin + 1) - 1) # + Ssib
           
            newsim_max = np.amax(newsim)
            if newsim_max > 0:
                newsim = newsim / newsim_max 
           
            newsim = newsim * Cneighbor
            
            newsim = np.maximum(newsim, anchors)

            if np.allclose(prevsim, newsim, atol=tolerance):
                break
            
            if its % 5 == 0:
                matrices.append(newsim)

        if verbose:
            print(f"Converge in {its} rounds.")
        
        decimal = int(round(-np.log10(tolerance)))
        return np.around((newsim +beta) * (initial_sim + alpha), decimals = decimal), newsim, matrices

    # @timer_decorator
    def greedy_match_list(self, final_sim, unmatched_list_01, unmatched_list_10, final_match_01, final_match_10, quality_list01, quality_list10):
        
        
        sub_matrix = final_sim[np.ix_(unmatched_list_01, unmatched_list_10)]

        order_max_to_min_01 = final_sim.argsort(axis=1)[:, ::-1]
        order_max_to_min_10 = final_sim.argsort(axis=0).T[:, ::-1]
        
        match_list_01 = {}
        match_list_10 = {}
        matched_place_01 = np.zeros(len(order_max_to_min_01), dtype=np.int64)
        matched_place_10 = np.zeros(len(order_max_to_min_10), dtype=np.int64)
        
        for i in unmatched_list_01:
            match_list_01[i] = order_max_to_min_01[i][matched_place_01[i]]
        for i in unmatched_list_10:
            match_list_10[i] = order_max_to_min_10[i][matched_place_10[i]]

        cnt = 0
        while match_list_01 and match_list_10:
            
            cnt += 1
            index_of_unmatch_01 = {unmatched_list_01[i]:i for i in range(len(unmatched_list_01))}
            index_of_unmatch_10 = {unmatched_list_10[j]:j for j in range(len(unmatched_list_10))}
            
            for i, idx in enumerate(match_list_01.keys()):
                
                match_list_01[idx] = order_max_to_min_01[idx][matched_place_01[idx]]
                
                while match_list_01[idx] not in unmatched_list_10:
                # while self.var2idx[1][match_list_01[idx]] in final_match_10.keys():
                    matched_place_01[idx] += 1
                    if matched_place_01[idx] < len(order_max_to_min_01[idx]):
                        match_list_01[idx] = order_max_to_min_01[idx][matched_place_01[idx]]
                    else:
                        break
                
                # if there is a tied maximum, go look at their relation labels
                
                try:
                    maxima = np.where((sub_matrix[i] == sub_matrix[i, index_of_unmatch_10[match_list_01[idx]]])>0)[0]
                except:
                    print(sub_matrix[i], "\n", match_list_01[idx], "\n", index_of_unmatch_10[match_list_01[idx]])

                if len(maxima) != 1:
                    vfunc = np.vectorize(lambda x: unmatched_list_10[x])
                    mapped_maxima = vfunc(maxima)
                    tgt, wheres = Match.enhance_with_rel_label(idx, mapped_maxima, 0, self.var2idx, self.umr0, self.umr1)
                    if tgt:
                        assert tgt in match_list_10.keys() # otherwise implementation error, tgt must be in mapped maxima
                    else:
                        # tied, possibly two relations are both 0
                        tgt = mapped_maxima[wheres[0]] # $wheres$ only select from those maximums
                    match_list_01[idx] = tgt
                    if cnt>500:
                        print(f"{i}-{idx}", wheres)
                    matched_place_01[idx] = max(matched_place_01[idx] - len(maxima), 0)
                    # it's possible that another choice is skipped
                    
            for j, idx in enumerate(match_list_10.keys()):
                
                match_list_10[idx] = order_max_to_min_10[idx][matched_place_10[idx]]
                
                while match_list_10[idx] not in unmatched_list_01:
                # while self.var2idx[0][match_list_10[idx]] in final_match_01.keys():
                    matched_place_10[idx] += 1
                    if matched_place_10[idx] < len(order_max_to_min_10[idx]):
                        match_list_10[idx] = order_max_to_min_10[idx][matched_place_10[idx]]
                    else:
                        break 
                    
                maxima = np.where((sub_matrix[:, j] == sub_matrix[index_of_unmatch_01[match_list_10[idx]], j])>0)[0]

                if len(maxima) != 1:
                    vfunc = np.vectorize(lambda x: unmatched_list_01[x])
                    mapped_maxima = vfunc(maxima)
                    tgt, wheres = Match.enhance_with_rel_label(idx, mapped_maxima, 1, self.var2idx, self.umr0, self.umr1)
                    if tgt:
                        assert tgt in match_list_01.keys() # otherwise implementation error, tgt must be in mapped maxima
                    else:
                        tgt = mapped_maxima[wheres[0]]
                    if cnt>500:
                        print(f"{j}-||{idx}", wheres)
                    match_list_10[idx] = tgt           
                    matched_place_10[idx] = max(matched_place_10[idx] - len(maxima), 0)
                    # it's possible that another choice is skipped
            
            key_pairs_to_delete = set()

            for idx01, idx10 in match_list_01.items():
                if (idx10 in match_list_10.keys()) and (match_list_10[idx10] == idx01):
                    assert self.var2idx[0][idx01] not in final_match_01.keys()
                    assert self.var2idx[1][idx10] not in final_match_10.keys()
                    
                    final_match_01[self.var2idx[0][idx01]] = self.var2idx[1][idx10]
                    quality_list01[self.var2idx[0][idx01]] = -1
                    self.Mt01.log_and_inc("concept", "bad_quality_sum", self.initial_sim[idx01, idx10])
                    self.Mt01.log_and_inc("concept", "smatch_concept_sum", (self.name_idt[idx01, idx10] == 1) )
                    final_match_10[self.var2idx[1][idx10]] = self.var2idx[0][idx01]
                    quality_list10[self.var2idx[1][idx10]] = -1
                    self.Mt10.log_and_inc("concept", "bad_quality_sum", self.initial_sim[idx01, idx10])
                    self.Mt10.log_and_inc("concept", "smatch_concept_sum", (self.name_idt[idx01, idx10] == 1) )
                    
                    key_pairs_to_delete.add((idx01, idx10))
            # the rest of them move to secondary match
            
            row_to_delete = []
            col_to_delete = []
            
            for p0, p1 in key_pairs_to_delete:
                
                del match_list_01[p0]
                del match_list_10[p1]
                
                row_to_delete.append(index_of_unmatch_01[p0])
                col_to_delete.append(index_of_unmatch_10[p1])
                unmatched_list_01.remove(p0)
                unmatched_list_10.remove(p1)    
                
            sub_matrix = np.delete(sub_matrix, row_to_delete, axis=0)
            sub_matrix = np.delete(sub_matrix, col_to_delete, axis=1)
                
            if cnt > 500:
                # to select a maximum based on relation match, it also must conform with relation maximum
                raise ValueError(values+"\n\n"+str(match_list_01)+"\n\n"+str(match_list_10)+"\n\n"+self.umr0.semantic_text+"\n\n"+self.umr1.semantic_text)
            
                    
        # for the rest unmatched
        for idx in match_list_01.keys():
            final_match_01[self.var2idx[0][idx]] = "NULL"+ self.var2idx[0][idx]
            quality_list01[self.var2idx[0][idx]] = -2
            self.Mt01.log_and_inc("concept", "bad_quality_sum", 0.0)
            self.Mt01.log_and_inc("concept", "smatch_concept_sum", 0.0 )
        for idx in match_list_10.keys():
            final_match_10[self.var2idx[1][idx]] = "NULL"+ self.var2idx[1][idx]
            quality_list10[self.var2idx[1][idx]] = -2
            self.Mt10.log_and_inc("concept", "bad_quality_sum", 0.0)
            self.Mt10.log_and_inc("concept", "smatch_concept_sum", 0.0)
        
        # assert len(final_match_01) == len(final_match_10)
            
        return final_match_01, final_match_10
    
    # @timer_decorator
    def get_new_anchor(self, final_sim):

        new_anchor = np.zeros(final_sim.shape)
        max_row = np.argmax(final_sim, axis=1)
        max_row_value = np.amax(final_sim, axis=1)
        max_col = np.argmax(final_sim, axis=0)
        max_col_value = np.amax(final_sim, axis=0)

        set01 = set()
        for i in range(new_anchor.shape[0]):
            max_pos = (final_sim[i]==max_row_value[i])
            maxima = np.where(max_pos > 0)[0]
            if np.count_nonzero(max_pos) == 1:
                set01.add((i, max_row[i]))
            else:
                tgt , wheres= Match.enhance_with_rel_label(i, maxima, 0, self.var2idx, self.umr0, self.umr1)
                if tgt:
                    set01.add((i, tgt))
        for j in range(new_anchor.shape[1]):
            max_pos = (final_sim[:, j] == max_col_value[j])
            maxima = np.where(max_pos > 0)[0]
            if np.count_nonzero(max_pos) == 1:
                if (max_col[j], j) in set01:
                    new_anchor[max_col[j], j] = 1
            else:
                tgt , wheres = Match.enhance_with_rel_label(j, maxima, 1, self.var2idx, self.umr0, self.umr1)
                if tgt:
                    if (tgt, j) in set01:
                       new_anchor[tgt, j] = 1
        
        return new_anchor
    
    def get_expedient_match(self, num, final_sim, givenv0):
        if givenv0:
            return np.argmax(final_sim, axis=1)[num]
        else:
            return np.argmax(final_sim, axis=0)[num]
    
    # @timer_decorator    
    def iterate_anchor_and_match(self, initial_anchors, max_iteration = 5, add_asymmetric_relations = True):
        
        # broadcast anchor
        
        # using anchors to enhance similarity information, reduce the similarity without any matched neighbors
        # anchors will broadcast, so even no anchors it would be fine

        match_list01 = {}
        quality_list01 = {}
        match_list10 = {}
        quality_list10 = {}
        
        anchors = initial_anchors.copy()
    
        c = np.where(anchors > 0) 
        quality_level = 0
        for i01, i10 in zip(c[0], c[1]):
            v01 = self.var2idx[0][i01]
            v10 = self.var2idx[1][i10]
            if v01 not in match_list01.keys():
                match_list01[v01] = v10
                quality_list01[v01] = quality_level
                self.Mt01.log_and_inc("concept","good_sum", self.initial_sim[i01, i10])
                self.Mt01.log_and_inc("concept", "smatch_concept_sum", (self.name_idt[i01, i10] == 1) )
            if v10 not in match_list10.keys():
                match_list10[v10] = v01
                quality_list10[v10] = quality_level
                self.Mt10.log_and_inc("concept","good_sum", self.initial_sim[i01, i10])
                self.Mt10.log_and_inc("concept","smatch_concept_sum", (self.name_idt[i01, i10] == 1))
        
        for quality_level in range(1, max_iteration+1):
        
            old_anchors = anchors
        
            final_sim, broadcasted_anchor, matrices = self.incorporate_neighborhood_information(self.initial_sim, old_anchors, self.Cneighbor)
        
            anchors = self.get_new_anchor(final_sim)
            
            new_spots = anchors - old_anchors
            
            if np.any(new_spots < 0):                            # although a rare case, but in case old anchor vanish
                to_remove = np.where(new_spots < 0)
                for i01, i10 in zip(to_remove[0], to_remove[1]):
                    del match_list01[self.var2idx[0][i01]]
                    del match_list10[self.var2idx[1][i10]]
                    del quality_list01[self.var2idx[0][i01]]
                    del quality_list10[self.var2idx[1][i10]]
            
            c = np.where(anchors > 0)
            if np.any(new_spots>0):
                for i01, i10 in zip(c[0], c[1]):
                    if self.var2idx[0][i01] not in match_list01.keys():
                        match_list01[self.var2idx[0][i01]] = self.var2idx[1][i10]
                        quality_list01[self.var2idx[0][i01]] = quality_level
                        self.Mt01.log_and_inc("concept","good_sum", self.initial_sim[i01, i10])
                        self.Mt01.log_and_inc("concept", "smatch_concept_sum", (self.name_idt[i01, i10] == 1) )
                    if self.var2idx[1][i10] not in match_list10.keys():
                        match_list10[self.var2idx[1][i10]] = self.var2idx[0][i01]
                        quality_list10[self.var2idx[1][i10]] = quality_level
                        self.Mt10.log_and_inc("concept","good_sum", self.initial_sim[i01, i10])
                        self.Mt10.log_and_inc("concept", "smatch_concept_sum", (self.name_idt[i01, i10] == 1) )
            else:
                break

        unmatched_list01 = []
        unmatched_list10 = []

        if add_asymmetric_relations:
            for v in self.umr0.var2node.keys():
                if v not in match_list01.keys():
                    unmatched_list01.append(self.var2idx[0][v])

            for v in self.umr1.var2node.keys():
                if v not in match_list10.keys():
                    unmatched_list10.append(self.var2idx[1][v])
             
        match_list01, match_list10 = self.greedy_match_list(final_sim, unmatched_list01, unmatched_list10, match_list01, match_list10, quality_list01, quality_list10)        
   
        return match_list01, match_list10, quality_list01, quality_list10
    
    # @timer_decorator
    def weighted_relational_overlap(self):
        
        def dictify(set2):
            rdict = defaultdict(set)
            for r in set2:
                rdict[(r[0], r[2])].add(r[1])
            return rdict
        
        def calculate_offsprings(edge_matrix):
            offspring_num = defaultdict(lambda: 0)
            for i in range(len(edge_matrix)):
                offspring_num[i] = get_argcnt(edge_matrix, i)
            return offspring_num
        
        def var2name(var, vlist):
            if var in vlist.keys():
                return vlist[var].name, vlist[var].sense_id
            else:
                return var, 0
            
        Aout0, Aout1 = self.outmatrix

        offspring_cnt = (calculate_offsprings(Aout0) , calculate_offsprings(Aout1))
        
        def off_num(num, var):
            if var in self.var2idx[num].keys():
                return offspring_cnt[num][self.var2idx[num][var]]
            else:
                return 0
            
        def calculate_lrs(rel_dict_me, rel_dict_you, vlist_me, vlist_you, Mt, this_idx, match_list_me):
            for (rel_pred, rel_arg), rel_label_set in rel_dict_me.items():
                # relation must be in pred-arg order
                tr_pred, tr_arg = self.translate_match(match_list_me, rel_pred), self.translate_match(match_list_me, rel_arg)
                this_sum_1 = len(rel_label_set)
                this_sum_weight_no1 = rel_weight(off_num(this_idx, rel_arg), off_num(this_idx, rel_pred))   # rel_pair[1] is the argument
                if (tr_pred, tr_arg) in rel_dict_you.keys():
                    target_label_set = rel_dict_you[(tr_pred, tr_arg)]
                    tr_pred_name, tr_pred_sense = var2name(tr_pred, vlist_you)
                    tr_arg_name,  tr_arg_sense = var2name(tr_arg, vlist_you)
                    rel_pred_name, rel_pred_sense = var2name(rel_pred, vlist_me)
                    rel_arg_name, rel_arg_sense = var2name(rel_arg, vlist_me)
                    rel_overlap = rel_label_set_comp(rel_label_set, target_label_set)
                    
                    # do a test
                    rel_unlabeled_overlap = min(len(target_label_set), len(rel_label_set)) # 如果这边关系太多，肯定有不对，如果这边关系少，那肯定都对
                    
                    rel_weighted_overlap = rel_overlap * this_sum_weight_no1
                    name_sim_pred = name_sim(tr_pred_name, rel_pred_name, (tr_pred_sense == rel_pred_sense))
                    name_sim_arg  = name_sim(tr_arg_name, rel_arg_name, (tr_arg_sense == rel_arg_sense))                    
                    
                    Mt.log_and_inc("lr", "score", (name_sim_pred + name_sim_arg) / 2 * rel_overlap, this_sum_1)      # 0 是名字全对，关系全部不对的情况
                    Mt.log_and_inc("ulr", "score",(name_sim_pred + name_sim_arg) / 2 * rel_unlabeled_overlap, this_sum_1) 
                    Mt.log_and_inc("wlr", "score", (name_sim_pred + name_sim_arg) / 2 * rel_weighted_overlap, this_sum_1 * this_sum_weight_no1) 
                else:
                    Mt.log_and_inc("lr", "score", 0, this_sum_1)    
                    Mt.log_and_inc("ulr", "score", 0, this_sum_1 )
                    Mt.log_and_inc("wlr", "score", 0, this_sum_1 * this_sum_weight_no1 )        
        
        vlist0 = self.umr0.var2node
        vlist1 = self.umr1.var2node
        
        set0 = set()
        set1 = set()
        
        for node in vlist0.values():
            set0 = set0 | node.get_relations()
        for node in vlist1.values():
            set1 = set1 | node.get_relations()
            
        rel_dict0 = dictify(set0)
        rel_dict1 = dictify(set1)
        
        calculate_lrs(rel_dict0, rel_dict1, vlist0, vlist1, self.Mt01, 0, self.match_list01)
        calculate_lrs(rel_dict1, rel_dict0, vlist1, vlist0, self.Mt10, 0, self.match_list10)
        
        s0 = self.Mt01.compute("lr")
        s1 = self.Mt10.compute("lr")
        s2 = self.Mt01.compute("ulr")
        s3 = self.Mt10.compute("ulr")
        s4 = self.Mt01.compute("wlr")
        s5 = self.Mt10.compute("wlr")
        
        return s0, s1, protected_divide(2*s0*s1, s0+s1), protected_divide(2*s2*s3, s2+s3), protected_divide(2*s4*s5, s4+s5)  
         