
import re
import os

def update_date_format(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.readlines()

    updated_content = []
    for line in content:
        updated_line = re.sub(r'(\d{4})/(\d{1,2})/(\d{1,2})', r'\1-\2-\3', line)
        updated_content.append(updated_line)

    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(updated_content)

def process_files_in_directory(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.csv'):  # Process CSV files
                file_path = os.path.join(root, file)
                update_date_format(file_path)

if __name__ == "__main__":
    directory = r"d:\Code\backtrader_Learn"  # Target directory
    process_files_in_directory(directory)
