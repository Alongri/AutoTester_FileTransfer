import re
import threading
import os
import logging


def find_and_replace_in_xml(xml_file, old_value, new_value):
    with open(xml_file, 'r', encoding='utf-8') as file:
        xml_content = file.read()
    updated_content = re.sub(re.escape(old_value), new_value, xml_content, flags=re.IGNORECASE)
    with open(xml_file, 'w', encoding='utf-8') as file:
        file.write(updated_content)


class ConvertLogic(threading.Thread):

    def __init__(self, ui, direction_repo, default_repository, new_value, completion_callback):
        threading.Thread.__init__(self)
        self.ui = ui
        self.direction_repo = direction_repo
        self.default_repository = default_repository
        self.new_value = new_value
        self.completion_callback = completion_callback

    def run(self):
        logging.info("Starting conversion process...")
        self.process_files(self.direction_repo, self.default_repository, self.new_value)
        logging.info("Conversion process completed.")
        self.completion_callback()

    def replace_remote_paths(self, directory):
        logging.debug(f"Scanning directory for files: {directory}")
        files_found = []
        for root, _, files in os.walk(directory):
            for filename in files:
                if filename.endswith('.atc') or filename.endswith('.attc') or filename.endswith('.atap'):
                    filepath = os.path.join(root, filename)
                    files_found.append(filepath)
        return files_found

    def process_files(self, dir_path, old_string, new_string):
        logging.debug(f"Processing files in directory: {dir_path}")
        array_of_files = self.replace_remote_paths(dir_path)

        for file_path in array_of_files:
            find_and_replace_in_xml(file_path, old_string, new_string)
        logging.debug("#################################################################")
        logging.debug("#############  XML processing complete for all files. ###########")
        logging.debug("#################################################################")

        first_level_subfolders = set()
        for file_path in array_of_files:
            folder = os.path.dirname(file_path)
            subfolder = os.path.relpath(folder, dir_path)
            if '\\' in subfolder:  # Check if subfolder has subfolders
                first_level_subfolder = subfolder.split('\\', 1)[0]
                first_level_subfolders.add(first_level_subfolder)

        for first_level_subfolder in first_level_subfolders:
            self.ui.process_result(f"Convert process finished: {os.path.join(dir_path, first_level_subfolder)}")
