# Ancast
AnCast metric for evaluating UMR semantic graphs.

## Usage

Place two AMR or UMR files for comparison, following the format in the `samples/` folder. Then, run the commands as specified in `runExperiment.sh`. The detailed comparison and scores for each sentence will be output to the corresponding csv file. The console output displays the micro average and F1 scores for all triples across sentences. If the UMR format is chosen, this metrics tool will also output scores for modality, temporal, and coreference aspects (to be published in an upcoming paper) and will calculate the total score for the document.