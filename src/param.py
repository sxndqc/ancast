print_sentence_processing=False
Cneighbor=1
separate_1and2 = False
USE_ALIGNMENT = False
verbose = False         # converge details
sense_coefficient = 0.1
SENSE_ADD_DEBUG_PRINT = False
use_smatch_top = True
get_reify = False
if get_reify:
    allowed_tags = {"explicit", "reified"}
else:
    allowed_tags = {"explicit"}