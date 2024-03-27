import sys
import os
import cProfile

src_dir = os.path.abspath(os.path.dirname(__file__))
if src_dir not in sys.path:
    sys.path.append(src_dir)

from document import *
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", type=str, nargs="+", help="One csv file, or two text files, one for test and one for gold.")
    parser.add_argument("--format",  "-f", required=True,       dest="format",  type=str, nargs=1, help="amr or umr?")
    parser.add_argument("--output",  "-o", required=True,       dest="output_csv",  type =str, nargs=1, help="output_to_csv")
    
    args = parser.parse_args()
    
    # args = parser.parse_args(["inputs/umrs/chinese/manual.csv", "--output", "inputs/umrs/chinese/csvs/manualoutput.csv", "--format", "umr"])
    
    format = args.format[0]
    assert format in {"amr", "umr"}
        
    D = DocumentMatch(format)

    if len(args.files) > 1:
        D.read_document(args.files[:2], args.output_csv[0])
    else:
        D.read_document(args.files[0],  args.output_csv[0])

if __name__ == "__main__":
    main()
