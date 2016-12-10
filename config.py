def parse_config(file):
    with open(file, mode='r') as f:
        lines = f.readlines()
        for line in lines:
            if line[0] == "#":
                continue  # this is a comment
