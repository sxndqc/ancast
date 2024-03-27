from param_fun import *                

class Metric:
    
    def __init__(self, name):
        self.name = name
        self.metrics = {
            "concept": {
            "good_sum": 0,
            "bad_quality_sum":0,
            "good_sum_count":0,
            "bad_quality_sum_count":0,
            "smatch_concept_sum": 0,
            "smatch_concept_sum_count":0
            },
            "relation": {
                "total": 0,
                "matched": 0
            },
            "lr":{
                "score": 0,
                "score_count": 0
            },
            "ulr":{
                "score": 0,
                "score_count": 0                
            },
            "wlr":{
                "score": 0,
                "score_count": 0                
            },
            "modal":{
                "score": 0,
                "score_count": 0                
            },
            "temporal":{
                "score": 0,
                "score_count": 0                
            },
            "coref":{
                "score": 0,
                "score_count": 0                
            }
        }   
        
    def log_and_inc_metric(self, Mt):
        for key1 in self.metrics:
            for key2 in self.metrics[key1]:
                self.metrics[key1][key2] += Mt.metrics[key1][key2]
        
    def log_and_inc(self, key1, key2, value, weight=1):
        assert key1 in self.metrics
        assert key2 in self.metrics[key1]
        self.metrics[key1][key2] += value
        self.metrics[key1][key2+"_count"] += weight
    
    def assign(self, key1, key2, value):
        self.metrics[key1][key2] = value
        
    def compute(self, type):
        if type == "smatch":
            return protected_divide(self.metrics["concept"]["smatch_concept_sum"] + self.metrics["relation"]["matched"] , self.metrics["concept"]["smatch_concept_sum_count"] + self.metrics["relation"]["total"])
        elif type == "concept with bad quality":
            return protected_divide((self.metrics["concept"]["good_sum"] + self.metrics["concept"]["bad_quality_sum"]) , (self.metrics["concept"]["good_sum_count"] + self.metrics["concept"]["bad_quality_sum_count"]))
        elif type == "concept qualified only":
            return protected_divide(self.metrics["concept"]["good_sum"] , self.metrics["concept"]["good_sum_count"] + self.metrics["concept"]["bad_quality_sum_count"])
            # unmatched is regarded as 0
        elif type == "relation":
            return protected_divide(self.metrics["relation"]["matched"], self.metrics["relation"]["total"])
        elif type == "good quality":
            return protected_divide(self.metrics["concept"]["good_sum_count"] , (self.metrics["concept"]["good_sum_count"] + self.metrics["concept"]["bad_quality_sum_count"]))
        elif type == "ulr":
            if self.metrics["ulr"]["score_count"] == 0:
                return self.compute("concept with bad quality")
            else:
                return protected_divide(self.metrics["ulr"]["score"], self.metrics["ulr"]["score_count"])
        elif type == "lr":
            if self.metrics["lr"]["score_count"] == 0:
                return self.compute("concept with bad quality")
            else:
                return self.metrics["lr"]["score"] / self.metrics["lr"]["score_count"]
        elif type == "wlr":
            if self.metrics["wlr"]["score_count"] == 0:
                return self.compute("concept with bad quality")
            else:
                return protected_divide(self.metrics["wlr"]["score"], self.metrics["wlr"]["score_count"])
        elif type == "modal":
            return protected_divide(self.metrics["modal"]["score"], self.metrics["modal"]["score_count"])
        elif type == "temporal":
            return protected_divide(self.metrics["temporal"]["score"], self.metrics["temporal"]["score_count"])
        elif type == "coref":
            return protected_divide(self.metrics["coref"]["score"], self.metrics["coref"]["score_count"])
        elif type == "document":
            return protected_divide(self.metrics["lr"]["score"] + self.metrics["modal"]["score"] + self.metrics["temporal"]["score"] + self.metrics["coref"]["score"], self.metrics["lr"]["score_count"]  + self.metrics["modal"]["score_count"] + self.metrics["temporal"]["score_count"] + self.metrics["coref"]["score_count"])
        else:
            return None
         
           