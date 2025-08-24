import os

input_dir = "./"
output_file = "combined_py.txt"

with open(output_file, 'w', encoding='utf-8') as outfile:

        for fname in os.listdir(input_dir):
            filepath = os.path.join(input_dir, fname)
            if os.path.isfile(filepath):
                if fname.endswith(".py") and not fname.startswith("write") :
                    with open(filepath, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        outfile.write(f'=== {filepath} ===\n')  # Optional file boundary
                        outfile.write(content + "\n\n")
        print(input_dir+"store")
        for fname in os.listdir(input_dir+"store"):
            filepath = os.path.join(input_dir + "store", fname)
            
            if os.path.isfile(filepath):
                #print(filepath)
                if fname.endswith(".py") and not fname.startswith("write") :
                    print(filepath)
                    with open(filepath, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        outfile.write(f'=== {filepath} ===\n')  # Optional file boundary
                        outfile.write(content + "\n\n")
        