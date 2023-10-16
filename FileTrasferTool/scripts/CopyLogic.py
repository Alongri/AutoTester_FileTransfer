import xml.etree.ElementTree as ET
from tkinter import messagebox
import os
import shutil
import glob


def selected_radioButton_option(response):
    if response == 0:  # Ask each time
        return True
    elif response == 1:  # Skip all
        return False
    elif response == 2:  # Overwrite All
        return None


def copy_deeper_procedures(start_path, visited=None):
    if visited is None:
        visited = set()

    stack = [start_path]
    list_of_procedures = set()
    list_of_exceptions = set()

    while stack:
        path = stack.pop()
        try:
            if path not in visited:
                tree = ET.parse(path)
                procedure_elements = tree.findall('.//procedure')
                for include_elem in procedure_elements:
                    include_path = include_elem.get('path')
                    list_of_procedures.add(include_path)
                    stack.append(include_path)
                visited.add(path)
        except Exception as e:
            list_of_exceptions.add(f"'{path}':{repr(e)}")
        except ET.ParseError as e:
            list_of_exceptions.add(f"'{path}': {repr(e)}")

    return list_of_procedures, list_of_exceptions


def overwrite_campaign(campaign, tests, procedures):
    overwrite = messagebox.askquestion("Project Folder Exists",
                                       "Project folder already exists. Do you want to overwrite it?")
    if overwrite.lower() == 'yes':
        if os.path.exists(campaign):
            shutil.rmtree(campaign)
        if os.path.exists(tests):
            shutil.rmtree(tests)
        if os.path.exists(procedures):
            shutil.rmtree(procedures)
        return True
    else:
        return


def overwrite_test(destination_file, test_name_to_copy):
    overwrite = messagebox.askquestion("Test Exists",
                                       f"Test with name {test_name_to_copy} already exists. Do you want to overwrite it?")
    if overwrite.lower() == 'yes':
        os.remove(destination_file)
        return True
    else:
        return


def overwrite_procedure(destination_file, procedure_name_to_copy):
    overwrite = messagebox.askquestion("Procedure Exists",
                                       f"Procedure with name {procedure_name_to_copy} already exists. Do you want to overwrite it?")
    if overwrite.lower() == 'yes':
        os.remove(destination_file)
        return True
    else:
        return


def copy_campaign(campaign_path, project_name, where_to_copy):
    campaign = f"{where_to_copy}\\AutoTester_Campaigns\\{project_name}"
    tests = f"{where_to_copy}\\AutoTester_TestCases\\{project_name}"
    procedures = f"{where_to_copy}\\AutoTester_Procedures\\{project_name}"
    # ---------------OVERWRITE OPTION-------------------------
    if os.path.exists(campaign) or os.path.exists(tests) or os.path.exists(procedures):
        result = overwrite_campaign(campaign, tests, procedures)
        if result is None:
            return
    # -------------------------------------------------------------------

    # Create the new folder
    os.mkdir(campaign)
    os.mkdir(tests)
    os.mkdir(procedures)

    visited = set()
    list_of_tests = set()
    list_of_procedures = set()
    list_of_exceptions = set()
    list_of_copy_files = set()
    try:
        tree = ET.parse(campaign_path)
        root = tree.getroot()
        titles = root.findall('testCases/testCase')
        for title in titles:
            file_attribute = title.get('file')
            list_of_tests.add(file_attribute)
    except ET.ParseError as e:
        list_of_exceptions.add(f"'{campaign_path}': {repr(e)}")

    # Check duplicates of tests
    filenames = [os.path.basename(test) for test in list_of_tests]
    filename_to_path = {filename: test for filename, test in zip(filenames, list_of_tests)}
    unique_filenames = list(set(filenames))
    updated_list_of_tests = [filename_to_path[filename] for filename in unique_filenames]

    # Copy the test files
    for test in updated_list_of_tests:
        try:
            shutil.copy(test, tests)
            list_of_copy_files.add(f'{test} copied to {tests}')
        except Exception as e:
            list_of_exceptions.add(f"'{test}': {repr(e)}")

    for test in updated_list_of_tests:
        try:
            tree = ET.parse(test)
            for proc in tree.findall('.//procedure'):
                path_attribute = proc.get('path')
                list_of_procedures.add(path_attribute)
                new_procedures, list_of_exceptions = copy_deeper_procedures(path_attribute, visited)
                list_of_procedures.update(new_procedures)
        except ET.ParseError as e:
            list_of_exceptions.add(f"'{test}': {repr(e)}")

    # Copy procedures that located in campaign file
    try:
        tree = ET.parse(campaign_path)
        for proc in tree.findall('.//procedure'):
            path_attribute = proc.get('path')
            list_of_procedures.add(path_attribute)
            copy_deeper_procedures(path_attribute)
    except ET.ParseError as e:
        list_of_exceptions.add(f"'{campaign_path}': {repr(e)}")

    # Check duplicates of procedures
    filenames = [os.path.basename(procedure) for procedure in list_of_procedures]
    filename_to_path = {filename: procedure for filename, procedure in zip(filenames, list_of_procedures)}
    unique_filenames = list(set(filenames))
    updated_list_of_procedures = [filename_to_path[filename] for filename in unique_filenames]

    # Copy the procedure files
    for procedure in updated_list_of_procedures:
        try:
            shutil.copy(procedure, procedures)
            list_of_copy_files.add(f'{procedure} copied to {procedures}')
        except Exception as e:
            list_of_exceptions.add(f"'{procedure}': {repr(e)}")

    # Copy the campaign file
    shutil.copy(campaign_path, campaign)
    list_of_copy_files.add(f'{campaign_path} copied to {campaign}')

    """
    replacing all the tests,procedures in this Campaign
    """

    # replacement of the location of the tests in the campaign file
    campaign_filename = os.path.basename(campaign_path)
    new_campaign_path = f"{campaign}\\{campaign_filename}"
    try:
        tree = ET.parse(new_campaign_path)
        root = tree.getroot()
        titles = root.findall('testCases/testCase')
        for title in titles:
            file_attribute = title.get('file')
            index = file_attribute.rfind("\\")
            tests_location_before = file_attribute[:index]
            replacer = file_attribute.replace(tests_location_before, tests)
            title.set('file', replacer)
        tree.write(new_campaign_path, encoding='utf-8', xml_declaration=True)
    except ET.ParseError as e:
        list_of_exceptions.add(f"'{new_campaign_path}': {repr(e)}")

    # replacement of the location of the procedures in tests files
    tests_path = glob.glob(os.path.join(tests, '*.attc'))
    for file_name in tests_path:
        try:
            tree = ET.parse(file_name)
            procedure_elements = tree.findall('.//procedure')
            for proc in procedure_elements:
                path_attribute = proc.get('path')
                index = path_attribute.rfind("\\")
                procedure_location_before = path_attribute[:index]
                replacer = path_attribute.replace(procedure_location_before, procedures)
                proc.set('path', replacer)
            tree.write(file_name, encoding='utf-8', xml_declaration=True)
        except ET.ParseError as e:
            list_of_exceptions.add(f"'{file_name}': {repr(e)}")

    # replacement of the location of the procedures in procedures files
    procedure_path = glob.glob(os.path.join(procedures, '*.atap'))
    for file_name in procedure_path:
        try:
            tree = ET.parse(file_name)
            root = tree.getroot()
            procedure_elements = tree.findall('.//procedure')
            if len(procedure_elements) > 0:
                for proc in procedure_elements:
                    path_attribute = proc.get('path')
                    index = path_attribute.rfind("\\")
                    procedure_location_before = path_attribute[:index]
                    replacer = path_attribute.replace(procedure_location_before, procedures)
                    proc.set('path', replacer)
            tree.write(file_name, encoding='utf-8', xml_declaration=True)
            path_attribute = root.get("path")
            index = path_attribute.rfind("\\")
            procedure_location_before = path_attribute[:index]
            replacer = path_attribute.replace(procedure_location_before, procedures)
            root.set("path", replacer)
            tree.write(file_name, encoding='utf-8', xml_declaration=True)
        except ET.ParseError as e:
            list_of_exceptions.add(f"'{file_name}': {repr(e)}")

    # replace all procedures in the campaign
    tree = ET.parse(new_campaign_path)
    procedure_elements = tree.findall('.//procedure')
    if len(procedure_elements) > 0:
        try:
            for proc in procedure_elements:
                path_attribute = proc.get('path')
                index = path_attribute.rfind("\\")
                procedure_location_before = path_attribute[:index]
                replacer = path_attribute.replace(procedure_location_before, procedures)
                proc.set('path', replacer)
            tree.write(new_campaign_path, encoding='utf-8', xml_declaration=True)
        except ET.ParseError as e:
            list_of_exceptions.add(f"'{new_campaign_path}': {repr(e)}")

    return list_of_exceptions, list_of_copy_files


def copy_test(test_path, project_name, where_to_copy, response):
    test = f"{where_to_copy}\\AutoTester_TestCases\\{project_name}"
    procedures = f"{where_to_copy}\\AutoTester_Procedures\\{project_name}"
    test_name_to_copy = os.path.basename(test_path)
    destination_test_file = os.path.join(test, test_name_to_copy)
    destination_test_file = destination_test_file.replace("/", "\\")
    # ---------------OVERWRITE OPTION-------
    if os.path.exists(destination_test_file):
        result = overwrite_test(destination_test_file, test_name_to_copy)
        if result is None:
            return
    # --------------------------------------
    if not os.path.exists(test):
        result = messagebox.askquestion("Warning", "This project not exists. Are you sure you want to proceed?",
                                        icon='warning')
        if result.lower() == 'yes':
            os.mkdir(test)
            os.mkdir(procedures)
        else:
            return

    list_of_procedures = set()
    list_of_exceptions = set()
    list_of_copy_files = set()
    newly_copied_procedures = []
    visited = set()
    shutil.copy(test_path, test)
    list_of_copy_files.add(f'{test_path} copied to {test}')
    try:
        tree = ET.parse(destination_test_file)
        for proc in tree.findall('.//procedure'):
            path_attribute = proc.get('path')
            list_of_procedures.add(path_attribute)
            new_procedures, list_of_exceptions = copy_deeper_procedures(path_attribute, visited)
            list_of_procedures.update(new_procedures)
    except ET.ParseError as e:
        list_of_exceptions.add(f"'{destination_test_file}': {repr(e)}")

    # Check duplicates of procedures
    filenames = [os.path.basename(procedure) for procedure in list_of_procedures]
    filename_to_path = {filename: procedure for filename, procedure in zip(filenames, list_of_procedures)}
    unique_filenames = list(set(filenames))
    updated_list_of_procedures = [filename_to_path[filename] for filename in unique_filenames]

    # Copy the procedure files

    for procedure in updated_list_of_procedures:
        try:
            procedure_name_to_copy = os.path.basename(procedure)
            destination_proc_file = os.path.join(procedures, procedure_name_to_copy)
            if os.path.exists(destination_proc_file):
                response = selected_radioButton_option(response)
                if response is None:
                    os.remove(destination_proc_file)
                    shutil.copy(procedure, procedures)
                    list_of_copy_files.add(f'{procedure} copied to {procedures}')
                    newly_copied_procedures.append(destination_proc_file)
                elif response:
                    overwrite_procedure(destination_proc_file, procedure_name_to_copy)
                    shutil.copy(procedure, procedures)
                    list_of_copy_files.add(f'{procedure} copied to {procedures}')
                    newly_copied_procedures.append(destination_proc_file)
            else:
                shutil.copy(procedure, procedures)
                list_of_copy_files.add(f'{procedure} copied to {procedures}')
                newly_copied_procedures.append(destination_proc_file)

        except Exception as e:
            list_of_exceptions.add(f"'{procedure}': {repr(e)}")
        except ET.ParseError as e:
            list_of_exceptions.add(f"'{procedure}': {repr(e)}")

    """
    replacing all procedures in this Test
    """

    # replacement of the location of the procedures in test file
    test_filename = os.path.basename(test_path)
    new_test_path = f"{test}\\{test_filename}"
    try:
        tree = ET.parse(new_test_path)
        procedure_elements = tree.findall('.//procedure')
        for proc in procedure_elements:
            path_attribute = proc.get('path')
            index = path_attribute.rfind("\\")
            procedure_location_before = path_attribute[:index]
            replacer = path_attribute.replace(procedure_location_before, procedures)
            replacer = replacer.replace("/", "\\")
            proc.set('path', replacer)
        tree.write(new_test_path, encoding='utf-8', xml_declaration=True)
    except ET.ParseError as e:
        list_of_exceptions.add(f"'{new_test_path}': {repr(e)}")

    # replacement of the location of the procedures in procedures file
    for file_name in newly_copied_procedures:
        try:
            tree = ET.parse(file_name)
            root = tree.getroot()
            procedure_elements = tree.findall('.//procedure')
            if len(procedure_elements) > 0:
                for proc in procedure_elements:
                    path_attribute = proc.get('path')
                    index = path_attribute.rfind("\\")
                    procedure_location_before = path_attribute[:index]
                    replacer = path_attribute.replace(procedure_location_before, procedures)
                    replacer = replacer.replace("/", "\\")
                    proc.set('path', replacer)
                tree.write(file_name, encoding='utf-8', xml_declaration=True)
            path_attribute = root.get("path")
            index = path_attribute.rfind("\\")
            procedure_location_before = path_attribute[:index]
            replacer = path_attribute.replace(procedure_location_before, procedures)
            replacer = replacer.replace("/", "\\")
            root.set("path", replacer)
            tree.write(file_name, encoding='utf-8', xml_declaration=True)
        except ET.ParseError as e:
            list_of_exceptions.add(f"'{new_test_path}': {repr(e)}")

    return list_of_exceptions, list_of_copy_files


def copy_procedure(procedure_path, project_name, where_to_copy, response):
    procedure = f"{where_to_copy}\\AutoTester_Procedures\\{project_name}"
    procedure_name_to_copy = os.path.basename(procedure_path)
    destination_procedure_file = os.path.join(procedure, procedure_name_to_copy)
    destination_procedure_file = destination_procedure_file.replace("/", "\\")
    # ---------------OVERWRITE OPTION-------
    if os.path.exists(destination_procedure_file):
        result = overwrite_procedure(destination_procedure_file, procedure_name_to_copy)
        if result is None:
            return
    # --------------------------------------
    if not os.path.exists(procedure):
        result = messagebox.askquestion("Warning", "This project not exists. Are you sure you want to proceed?",
                                        icon='warning')
        if result.lower() == 'yes':
            os.mkdir(procedure)
        else:
            return

    list_of_procedures = set()
    list_of_exceptions = set()
    list_of_copy_files = set()
    newly_copied_procedures = []
    visited = set()
    shutil.copy(procedure_path, procedure)
    list_of_copy_files.add(f'{procedure_path} copied to {procedure}')
    try:
        tree = ET.parse(destination_procedure_file)
        for proc in tree.findall('.//procedure'):
            path_attribute = proc.get('path')
            list_of_procedures.add(path_attribute)
            new_procedures, list_of_exceptions = copy_deeper_procedures(path_attribute, visited)
            list_of_procedures.update(new_procedures)
    except ET.ParseError as e:
        list_of_exceptions.add(f"'{destination_procedure_file}': {repr(e)}")

    # Check duplicates of procedures
    filenames = [os.path.basename(procedure) for procedure in list_of_procedures]
    filename_to_path = {filename: procedure for filename, procedure in zip(filenames, list_of_procedures)}
    unique_filenames = list(set(filenames))
    updated_list_of_procedures = [filename_to_path[filename] for filename in unique_filenames]

    for proc in updated_list_of_procedures:
        try:
            procedure_name_to_copy = os.path.basename(proc)
            destination_proc_file = os.path.join(procedure, procedure_name_to_copy)
            if os.path.exists(destination_proc_file):
                response = selected_radioButton_option(response)
                if response is None:
                    os.remove(destination_proc_file)
                    shutil.copy(proc, procedure)
                    list_of_copy_files.add(f'{proc} copied to {procedure}')
                    newly_copied_procedures.append(destination_proc_file)
                elif response:
                    overwrite_procedure(destination_proc_file, procedure_name_to_copy)
                    shutil.copy(proc, procedure)
                    list_of_copy_files.add(f'{proc} copied to {procedure}')
                    newly_copied_procedures.append(destination_proc_file)
            else:
                shutil.copy(proc, procedure)
                list_of_copy_files.add(f'{proc} copied to {procedure}')
                newly_copied_procedures.append(destination_proc_file)

        except Exception as e:
            list_of_exceptions.add(f"'{procedure}': {repr(e)}")
        except ET.ParseError as e:
            list_of_exceptions.add(f"'{procedure}': {repr(e)}")

    """
    replacing all procedures in this Procedure
    """
    try:
        tree = ET.parse(destination_procedure_file)
        root = tree.getroot()
        root.set('path', destination_procedure_file)
        procedure_elements = tree.findall('.//procedure')
        for proc in procedure_elements:
            path_attribute = proc.get('path')
            index = path_attribute.rfind("\\")
            procedure_location_before = path_attribute[:index]
            replacer = path_attribute.replace(procedure_location_before, procedure)
            replacer = replacer.replace("/", "\\")
            proc.set('path', replacer)
        tree.write(destination_procedure_file, encoding='utf-8', xml_declaration=True)
    except ET.ParseError as e:
        list_of_exceptions.add(f"'{destination_procedure_file}': {repr(e)}")

    # replacement of the location of the procedures in procedures file
    for file_name in newly_copied_procedures:
        try:
            tree = ET.parse(file_name)
            root = tree.getroot()
            procedure_elements = tree.findall('.//procedure')
            if len(procedure_elements) > 0:
                for proc in procedure_elements:
                    path_attribute = proc.get('path')
                    index = path_attribute.rfind("\\")
                    procedure_location_before = path_attribute[:index]
                    replacer = path_attribute.replace(procedure_location_before, procedure)
                    replacer = replacer.replace("/", "\\")
                    proc.set('path', replacer)
                tree.write(file_name, encoding='utf-8', xml_declaration=True)
            path_attribute = root.get("path")
            index = path_attribute.rfind("\\")
            procedure_location_before = path_attribute[:index]
            replacer = path_attribute.replace(procedure_location_before, procedure)
            replacer = replacer.replace("/", "\\")
            root.set("path", replacer)
            tree.write(file_name, encoding='utf-8', xml_declaration=True)
        except ET.ParseError as e:
            list_of_exceptions.add(f"'{file_name}': {repr(e)}")

    return list_of_exceptions, list_of_copy_files
