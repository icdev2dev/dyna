import os

input_dir = "../dyna/src"
output_file = "combined.txt"

with open(output_file, 'w', encoding='utf-8') as outfile:
    for root, _, files in os.walk(input_dir):
        for fname in files:
            if fname.endswith(".svelte") or fname.endswith(".js"):
                filepath = os.path.join(root, fname)
                with open(filepath, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    outfile.write(f'=== {filepath} ===\n')  # Optional file boundary
                    outfile.write(content + "\n\n")