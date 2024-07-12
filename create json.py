import json

# Dictionary
data = {
    'Region Dispute Count': 0,
    'Trade Count': {
        'Allied States of America': 0,
        'Capitalism Works!': 0,
        'Mississippi Trade Co.': 0,
        'Threads of Azj-Kahet': 0,
        'Doofenshmirtz Evil Incorporated': 0,
        'Would You Like Fries With That?': 0,
        'Peener Pee-Pee Land': 0,
        'Skibidi Supremacy': 0,
    }
}

# Write dictionary to JSON file
file_path = input("Enter file name: ")
with open(file_path, "w") as json_file:
    json.dump(data, json_file, indent=4)

print("JSON file created successfully.")