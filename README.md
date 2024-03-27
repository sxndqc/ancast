# Ancast
AnCast metric for evaluating UMR semantic graphs.

## Usage

Place two AMR or UMR files for comparison, following the format in the `samples/` folder. Then, run the commands as specified in `runExperiment.sh`. The detailed comparison and scores for each sentence will be output to the corresponding csv file. The console output displays the micro average and F1 scores for all triples across sentences. If the UMR format is chosen, this metrics tool will also output scores for modality, temporal, and coreference aspects (to be published in an upcoming paper) and will calculate the total score for the document.

## Cite

Please cite this paper for now:

```bibtex
@inproceedings{sun2024ancast,
    title = "Anchor and Broadcast: An Eﬀicient Concept Alignment Approach for Evaluation of Semantic Graphs",
    author = "Sun, Haibo and Nianwen Xue ",
    booktitle = "Proceedings of the 2024 Joint International Conference on Computational Linguistics, Language Resources and Evaluation",
    month = may,
    year = "2024",
}
```