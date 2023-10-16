import datetime
import queue
import sys
import tkinter
import tkinter as tk
from PIL import Image
import json
from tkinter import messagebox
from tkinter import filedialog
import customtkinter
import git
from git import Repo
from git.remote import RemoteProgress
from ConvertLogic import ConvertLogic
from CopyLogic import copy_campaign
from CopyLogic import copy_test
from CopyLogic import copy_procedure
from CopyLogic import selected_radioButton_option
import subprocess
import threading
import os
import time
import logging


version = "12"


class TextRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)  # Scroll to the end of the text

    def flush(self):
        pass


class ErrorPopupHandler(logging.Handler):
    def __init__(self, app):
        super().__init__()
        self.app = app

    def emit(self, record):
        error_message = self.format(record)
        self.app.show_error_message(error_message)


class AboutWindow(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("About")
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 900
        window_height = 600
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.attributes('-topmost', True)

        title = "AutoTester FileTransfer Tool"

        description = (
            "This tool offers a convenient solution for transferring AutoTester files between Git repositories.\n\n"
            "Whether you're looking to move files between branches, in your local branch, or transfer them from\n\n"
            "your local machine to a Git repository, this tool streamlines the process.\n\n"
            "With its intuitive GUI, you can easily select, copy, and manage your AutoTester files."

        )
        features_title = "Features"
        features = (
            "- Transfer files between Git branches.\n\n"
            "- Transfer files in your branch.\n\n"
            "- Upload files from your local machine to a Git repository.\n\n"
            "- Manage your AutoTester files efficiently and effortlessly.\n"
        )
        created = "Created By: Alon Gritsovsky"
        version_number = f"Version {version}"

        title_label = customtkinter.CTkLabel(self, text=title, font=("Baskerville Old Face", 25, 'bold'))
        title_label.pack(pady=(10, 10))

        self.description_label = customtkinter.CTkLabel(self, text=description,
                                                        font=("Times", 20), anchor="w", justify="left")
        self.description_label.pack(pady=(20, 10), padx=10)

        self.features_title_label = customtkinter.CTkLabel(self, text=features_title,
                                                           font=("Times", 20, 'bold'), anchor="w", justify="left")
        self.features_title_label.pack(pady=(20, 10), padx=30, anchor="w")

        self.features_label = customtkinter.CTkLabel(self, text=features,
                                                     font=("Times", 20,), anchor="w", justify="left")
        self.features_label.pack(padx=20, pady=(20, 10), anchor="w")

        self.created_label = customtkinter.CTkLabel(self, text=created,
                                                    font=("Times", 20,), anchor="w", justify="left")
        self.created_label.pack(padx=20, pady=(20, 10), anchor="w")

        self.version_label = customtkinter.CTkLabel(self, text=version_number,
                                                    font=("Times", 20, 'bold'), anchor="center")
        self.version_label.pack(padx=20, pady=(20, 10), anchor="center")


class CloneProgress(RemoteProgress):
    def __init__(self, gui_instance):
        super().__init__()
        self.gui_instance = gui_instance

    def update(self, *args):
        message = self._cur_line.strip()
        self.gui_instance.update_textbox(message)
        logging.debug(message)


customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class App(customtkinter.CTk):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = queue.Queue()
        self.running = False
        self.start_time = None
        self.title(f"AutoTester FileTransfer {version}")
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 1200
        window_height = 800
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        """
        create the TAB view 
        """

        self.tabview = customtkinter.CTkTabview(self, width=240, height=630)
        self.tabview.grid(row=0, column=1, padx=(30, 30), pady=(20, 20), sticky="nsew")
        self.tabview.add("Copy from local branch")
        self.tabview.add("Copy from remote branch")
        self.tabview.add("Settings")
        self.tabview.tab("Copy from local branch").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Copy from remote branch").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Settings").grid_columnconfigure(0, weight=1)

        """
        SIDEBAR ELEMENTS
        """
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

        # --------------------------------------NAME OF THE PROGRAM LABEL-------------------------------
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="AutoTester\nFileTransfer",
                                                 font=customtkinter.CTkFont(weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        font_tuple = ("Baskerville Old Face", 26)
        self.logo_label.configure(font=font_tuple)
        # -------------------------------------------------------------------------------------------------

        # ----------------------------------------SIDEBAR BUTTONS----------------------------------------

        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, text="Settings",
                                                        font=customtkinter.CTkFont(size=12, weight="bold"), width=170,
                                                        height=30)
        self.sidebar_button_1.grid(row=4, column=0, padx=20, pady=10)
        self.sidebar_button_2 = customtkinter.CTkButton(self.sidebar_frame, text="Copy from local branch",
                                                        font=customtkinter.CTkFont(size=12, weight="bold"), width=170,
                                                        height=30)
        self.sidebar_button_2.grid(row=2, column=0, padx=20, pady=10)
        self.sidebar_button_3 = customtkinter.CTkButton(self.sidebar_frame, text="Copy from remote branch",
                                                        font=customtkinter.CTkFont(size=12, weight="bold"), width=170,
                                                        height=30)
        self.sidebar_button_3.grid(row=3, column=0, padx=20, pady=10)
        self.sidebar_button_4 = customtkinter.CTkButton(self.sidebar_frame, text="About",
                                                        command=self.open_about_window,
                                                        font=customtkinter.CTkFont(size=12, weight="bold"), width=170,
                                                        height=30)
        self.sidebar_button_4.grid(row=6, column=0, padx=20, pady=10)
        self.sidebar_button_5 = customtkinter.CTkButton(self.sidebar_frame, text="Log Report",
                                                        command=self.open_logs_folder,
                                                        font=customtkinter.CTkFont(size=12, weight="bold"), width=170,
                                                        height=30)
        self.sidebar_button_5.grid(row=5, column=0, padx=20, pady=10)

        # -------------------------------------------------------------------------------------------------

        # ----------------------------------------------LOGO-----------------------------------------------
        image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "images")
        self.logo_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "autotester.ico")),
                                                 size=(80, 80))
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, image=self.logo_image, text="")
        self.logo_label.grid(row=1, column=0, padx=20, pady=10)

        # --------------------------------------------------------------------------------------------
        """"
        TAB 1: Settings
        """
        # ----------------------------------Appearance Mode-------------------------------------------------
        self.appearance_mode_label = customtkinter.CTkLabel(self.tabview.tab("Settings"), text="Appearance Mode:",
                                                            anchor="w")
        self.appearance_mode_label.grid(row=0, column=0, padx=(30, 30), pady=(20, 10), sticky='wn')
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.tabview.tab("Settings"),
                                                                       values=["Light", "Dark", "System"], width=170,
                                                                       height=30,
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=0, column=0, padx=(100, 20), pady=(20, 10), sticky='n')
        # -------------------------------------------------------------------------------------------------

        # ---------------------------------------UI SCALING--------------------------------------------
        self.scaling_label = customtkinter.CTkLabel(self.tabview.tab("Settings"), text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=0, column=0, padx=(30, 30), pady=(80, 40), sticky='wn')
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(self.tabview.tab("Settings"),
                                                               values=["80%", "90%", "100%", "110%", "120%"], width=170,
                                                               height=30,
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=0, column=0, padx=(100, 20), pady=(80, 10), sticky='n')
        # -------------------------------------------------------------------------------------------------

        # ---------------------------------------DEFAULT PATH--------------------------------------------
        self.default_path_label = customtkinter.CTkLabel(self.tabview.tab("Settings"), text="Set default target path:",
                                                         anchor="w")
        self.default_path_label.grid(row=2, column=0, padx=(30, 30), pady=(0, 10), sticky='w')

        self.default_path_to_copy_entry = customtkinter.CTkEntry(self.tabview.tab("Settings"))
        self.default_path_to_copy_entry.grid(row=2, column=0, padx=(180, 20), pady=(0, 10), sticky="ew")

        # -------------------------------------------------------------------------------------------------
        # ------------------------------------BROWSE BUTTONS-------------------------------------------
        self.browse_button_1_settings = customtkinter.CTkButton(self.tabview.tab("Settings"),
                                                                command=self.browse_1_settings,
                                                                border_width=2, text_color=("gray10", "#DCE4EE"),
                                                                text="BROWSE",
                                                                font=customtkinter.CTkFont(size=12, weight="bold"))
        self.browse_button_1_settings.grid(row=2, column=2, padx=(0, 30), pady=(0, 10), sticky="ew")
        # -------------------------------------------------------------------------------------------------

        # ---------------------------------------DEFAULT GIT URL REPOSITORY--------------------------------------------
        self.default_url_https_link_label = customtkinter.CTkLabel(self.tabview.tab("Settings"),
                                                                   text="Set default url https link:",
                                                                   anchor="w")
        self.default_url_https_link_label.grid(row=3, column=0, padx=(30, 30), pady=(10, 10), sticky='w')
        self.default_url_https_link_entry = customtkinter.CTkEntry(self.tabview.tab("Settings"))
        self.default_url_https_link_entry.grid(row=3, column=0, padx=(180, 20), pady=(20, 20), sticky="ew")

        # -------------------------------------------------------------------------------------------------

        # ---------------------------------------DEFAULT GIT REPOSITORY--------------------------------------------
        self.default_git_repository_label = customtkinter.CTkLabel(self.tabview.tab("Settings"),
                                                                   text="Set default repository:",
                                                                   anchor="w")
        self.default_git_repository_label.grid(row=4, column=0, padx=(30, 30), pady=(20, 10), sticky='wn')
        self.default_git_repository_entry = customtkinter.CTkEntry(self.tabview.tab("Settings"))
        self.default_git_repository_entry.grid(row=4, column=0, padx=(180, 20), pady=(20, 20), sticky="ew")

        # -------------------------------------------------------------------------------------------------

        # ---------------------------------------SAVE BUTTON---------------------------------------------
        self.save_settings_button = customtkinter.CTkButton(self.tabview.tab("Settings"), text="Save",
                                                            text_color=("gray10", "#DCE4EE"), border_width=2,
                                                            font=customtkinter.CTkFont(size=12, weight="bold"),
                                                            command=self.on_save_settings,
                                                            width=170, height=30)
        self.save_settings_button.grid(row=6, column=2, padx=(0, 30), pady=(50, 20), sticky="ew")
        # -------------------------------------------------------------------------------------------------
        # ----------------------------------------------SETTING ICON-----------------------------------------------
        image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "images")
        self.setting_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "setting.png")),
                                                    size=(70, 70))
        self.setting_label = customtkinter.CTkLabel(self.tabview.tab("Settings"), image=self.setting_image, text="")
        self.setting_label.grid(row=0, column=2, padx=20, pady=(20, 20), sticky="n")
        # --------------------------------------------------------------------------------------------

        # ----------------------------------------------RADIO BUTTONS----------------------------------------
        self.radiobutton_frame = customtkinter.CTkFrame(self.tabview.tab("Settings"))
        self.radiobutton_frame.grid(row=5, column=0, padx=(20, 30), pady=(30, 70), sticky="nsew")
        self.radio_var = tkinter.IntVar(value=0)
        self.label_radio_group = customtkinter.CTkLabel(master=self.radiobutton_frame,
                                                        text="Operation during procedures duplicates:")
        self.label_radio_group.grid(row=0, column=0, columnspan=1, padx=10, pady=10, sticky="")
        self.radio_button_1 = customtkinter.CTkRadioButton(master=self.radiobutton_frame, variable=self.radio_var,
                                                           text="Ask each one what to do",
                                                           value=0)
        self.radio_button_1.grid(row=1, column=0, pady=10, padx=20, sticky="wn")
        self.radio_button_2 = customtkinter.CTkRadioButton(master=self.radiobutton_frame, variable=self.radio_var,
                                                           text="Skip if duplicated",
                                                           value=1)
        self.radio_button_2.grid(row=2, column=0, pady=10, padx=20, sticky="wn")
        self.radio_button_3 = customtkinter.CTkRadioButton(master=self.radiobutton_frame, variable=self.radio_var,
                                                           text="Overwrite if duplicated",
                                                           value=2)
        self.radio_button_3.grid(row=3, column=0, pady=10, padx=20, sticky="wn")

        # --------------------------------------------------------------------------------------------
        """"
        TAB 2: Copy from local repository
        """
        # ----------------------------------Copy files in local repository LABEL----------------------------------
        self.label = customtkinter.CTkLabel(self.tabview.tab("Copy from local branch"),
                                            text="Copy files in local repository",
                                            font=customtkinter.CTkFont(size=12, weight="bold"))
        self.label.grid(row=0, column=0, padx=(30, 30), pady=(5, 0), sticky='w')
        # -------------------------------------------------------------------------------------------------

        # -------------------------------------CHOOSE TYPE OF FILE LABEL---------------------------------------
        self.label = customtkinter.CTkLabel(self.tabview.tab("Copy from local branch"), text="Select type of file",
                                            font=customtkinter.CTkFont(size=12, weight="bold"))
        self.label.grid(row=1, column=0, padx=(30, 30), pady=(30, 10), sticky='w')
        # -------------------------------------------------------------------------------------------------

        # ------------------------------------CHOOSE TYPE OF FILE------------------------------------
        self.select_type_tab2 = customtkinter.CTkOptionMenu(self.tabview.tab("Copy from local branch"),
                                                            dynamic_resizing=False,
                                                            values=["Campaign", "Test", "Procedure"],
                                                            command=self.clear_entry_boxes_local)
        self.select_type_tab2.grid(row=1, column=0, padx=20, pady=(30, 10))

        # -------------------------------------------------------------------------------------------------

        # -----------------------------------PROJECT NAME-------------------------------------------
        self.project_entry_local = customtkinter.CTkEntry(self.tabview.tab("Copy from local branch"),
                                                          placeholder_text="Project name")
        self.project_entry_local.grid(row=4, column=0, columnspan=1, padx=(30, 30), pady=(20, 30), sticky="nsew")
        # -------------------------------------------------------------------------------------------------

        # ----------------------------------FROM WHERE TO COPY------------------------------------------
        self.from_dir_entry_local = customtkinter.CTkEntry(self.tabview.tab("Copy from local branch"),
                                                           placeholder_text="Copy from directory")
        self.from_dir_entry_local.grid(row=2, column=0, columnspan=1, padx=(30, 30), pady=(50, 10), sticky="nsew")
        # -------------------------------------------------------------------------------------------------
        # ----------------------------------WHERE TO COPY------------------------------------------
        self.to_dir_entry_local = customtkinter.CTkEntry(self.tabview.tab("Copy from local branch"),
                                                         placeholder_text="Copy to directory")
        self.to_dir_entry_local.grid(row=3, column=0, columnspan=1, padx=(30, 30), pady=(20, 10), sticky="nsew")
        # -------------------------------------------------------------------------------------------------

        # ------------------------------------BROWSE BUTTONS-------------------------------------------
        self.browse_button_1_tab2 = customtkinter.CTkButton(self.tabview.tab("Copy from local branch"),
                                                            command=self.browse_1_tab2, border_width=2,
                                                            text_color=("gray10", "#DCE4EE"), text="BROWSE",
                                                            font=customtkinter.CTkFont(size=12, weight="bold"))
        self.browse_button_1_tab2.grid(row=2, column=1, padx=(30, 30), pady=(50, 10), sticky="nsew")
        # -------------------------------------------------------------------------------------------------
        self.browse_button_2_tab2 = customtkinter.CTkButton(self.tabview.tab("Copy from local branch"), border_width=2,
                                                            command=self.browse_2_tab2,
                                                            text_color=("gray10", "#DCE4EE"), text="BROWSE",
                                                            font=customtkinter.CTkFont(size=12, weight="bold"))
        self.browse_button_2_tab2.grid(row=3, column=1, padx=(30, 30), pady=(20, 10), sticky="nsew")
        # -------------------------------------------------------------------------------------------------
        # ------------------------------------PROGRESS BAR---------------------------------------------
        self.progressbar_2 = customtkinter.CTkProgressBar(self.tabview.tab("Copy from local branch"))
        self.progressbar_2.grid(row=7, column=0, padx=(20, 10), pady=(10, 10), sticky="ew")
        self.progressbar_2.configure(mode="determinate")
        self.progressbar_2.stop()
        # ------------------------------------------------------------------------------------------------
        # -------------------------------------COPY BUTTON------------------------------------------------
        self.copy_button = customtkinter.CTkButton(self.tabview.tab("Copy from local branch"), border_width=2,
                                                   text_color=("gray10", "#DCE4EE"), text="COPY",
                                                   font=customtkinter.CTkFont(size=12, weight="bold"),
                                                   command=self.copy_process)
        self.copy_button.grid(row=4, column=1, padx=(30, 30), pady=(20, 30), sticky="nsew")
        # -------------------------------------------------------------------------------------------------
        # --------------------------------TEXT BOX----------------------------------------------------------
        self.textbox = customtkinter.CTkTextbox(self.tabview.tab("Copy from local branch"), width=300, height=250,
                                                fg_color="#343638")
        self.textbox.grid(row=6, column=0, padx=(20, 10), pady=(70, 0), sticky="nsew")

        # -------------------------------------------------------------------------------------------------
        # ----------------------------------Timer LABEL----------------------------------
        self.label_timer_1 = customtkinter.CTkLabel(self.tabview.tab("Copy from local branch"), text="00:00:00",
                                                    font=customtkinter.CTkFont(size=12, weight="bold"))
        self.label_timer_1.grid(row=7, column=1, padx=(20, 10), pady=(10, 10), sticky='w')

        # -------------------------------------------------------------------------------------------------
        """"
        TAB 3: Copy from remote repository
        """
        # ----------------------------------Clone using HTTPS LABEL----------------------------------
        self.label = customtkinter.CTkLabel(self.tabview.tab("Copy from remote branch"), text="Clone using HTTPS",
                                            font=customtkinter.CTkFont(size=12, weight="bold"))
        self.label.grid(row=0, column=0, padx=(30, 30), pady=(5, 0), sticky='w')
        # -------------------------------------------------------------------------------------------------
        # ----------------------------------URL ENTRY-----------------------------------------------------
        self.url_entry = customtkinter.CTkEntry(self.tabview.tab("Copy from remote branch"),
                                                placeholder_text="Repository to Clone")
        self.url_entry.grid(row=1, column=0, columnspan=1, padx=(30, 30), pady=(10, 10), sticky="nsew")
        # -------------------------------------------------------------------------------------------------
        # ----------------------------------DESTINATION ENTRY-----------------------------------------------------
        self.destination_entry = customtkinter.CTkEntry(self.tabview.tab("Copy from remote branch"),
                                                        placeholder_text="Destination")
        self.destination_entry.grid(row=2, column=0, columnspan=1, padx=(30, 30), pady=(10, 10), sticky="nsew")
        # -------------------------------------------------------------------------------------------------
        # ----------------------------------branch OPTION LABEL----------------------------------
        self.label = customtkinter.CTkLabel(self.tabview.tab("Copy from remote branch"),
                                            text="Select branch:",
                                            font=customtkinter.CTkFont(size=12, weight="bold"))
        self.label.grid(row=4, column=0, padx=(30, 30), pady=(20, 10), sticky='w')
        # -------------------------------------------------------------------------------------------------

        # ---------------------------------------branch OPTION--------------------------------
        self.select_branch_tab3 = customtkinter.CTkOptionMenu(self.tabview.tab("Copy from remote branch"),
                                                              dynamic_resizing=False,
                                                              values=["master"], command=self.checkout_branch)
        self.select_branch_tab3.grid(row=4, column=0, padx=(30, 200), pady=(20, 10))
        # -------------------------------------------------------------------------------------------------

        # ------------------------------------PROGRESS BAR-------------------------------------------
        self.progressbar_1 = customtkinter.CTkProgressBar(self.tabview.tab("Copy from remote branch"))
        self.progressbar_1.grid(row=10, column=0, padx=(20, 10), pady=(10, 10), sticky="ew")
        # -----------------------------------------------------------------------------------------------
        # ------------------------------------BROWSE BUTTON----------------------------------------------
        self.browse_button_2_tab3 = customtkinter.CTkButton(self.tabview.tab("Copy from remote branch"),
                                                            command=self.browse_2_tab3, border_width=2,
                                                            text_color=("gray10", "#DCE4EE"), text="BROWSE",
                                                            font=customtkinter.CTkFont(size=12, weight="bold"))
        self.browse_button_2_tab3.grid(row=2, column=1, padx=(30, 30), pady=(10, 10), sticky="nsew")
        # -----------------------------------------------------------------------------------------------
        self.browse_button_3_tab3 = customtkinter.CTkButton(self.tabview.tab("Copy from remote branch"),
                                                            command=self.browse_3_tab3, border_width=2,
                                                            text_color=("gray10", "#DCE4EE"), text="BROWSE",
                                                            font=customtkinter.CTkFont(size=12, weight="bold"))
        self.browse_button_3_tab3.grid(row=6, column=1, padx=(30, 30), pady=(10, 10), sticky="nsew")
        # -------------------------------------------------------------------------------------------------
        self.browse_button_4_tab3 = customtkinter.CTkButton(self.tabview.tab("Copy from remote branch"),
                                                            command=self.browse_4_tab3, border_width=2,
                                                            text_color=("gray10", "#DCE4EE"), text="BROWSE",
                                                            font=customtkinter.CTkFont(size=12, weight="bold"))
        self.browse_button_4_tab3.grid(row=7, column=1, padx=(30, 30), pady=(10, 10), sticky="nsew")
        # -------------------------------------------------------------------------------------------------

        # -----------------------------------SUBDIRECTORY-------------------------------------------
        self.subdir_entry = customtkinter.CTkEntry(self.tabview.tab("Copy from remote branch"),
                                                   placeholder_text="Subdirectory to create")
        self.subdir_entry.grid(row=3, column=0, columnspan=1, padx=(30, 30), pady=(10, 10), sticky="nsew")
        # -------------------------------------------------------------------------------------------------

        # --------------------------------------CLONE BUTTON------------------------------------------------
        self.clone_button = customtkinter.CTkButton(self.tabview.tab("Copy from remote branch"),
                                                    command=self.cloning_process_start, border_width=2,
                                                    text_color=("gray10", "#DCE4EE"), text="CLONE",
                                                    font=customtkinter.CTkFont(size=12, weight="bold"))
        self.clone_button.grid(row=3, column=1, padx=(30, 30), pady=(10, 10), sticky="n")
        # -------------------------------------------------------------------------------------------------

        # --------------------------------------TYPE OF FILE LABEL----------------------------------------------
        self.label = customtkinter.CTkLabel(self.tabview.tab("Copy from remote branch"), text="Select file type:",
                                            font=customtkinter.CTkFont(size=12, weight="bold"))
        self.label.grid(row=5, column=0, padx=(30, 30), pady=(20, 10), sticky='w')
        # -------------------------------------------------------------------------------------------------

        # ---------------------------------------TYPE OF FILE CHOOSE OPTION--------------------------------
        self.select_type_tab3 = customtkinter.CTkOptionMenu(self.tabview.tab("Copy from remote branch"),
                                                            dynamic_resizing=False,
                                                            values=["Campaign", "Test", "Procedure"],
                                                            command=self.clear_entry_boxes_remote)
        self.select_type_tab3.grid(row=5, column=0, padx=(30, 200), pady=(20, 10))
        # -------------------------------------------------------------------------------------------------

        # -----------------------------------FROM WHERE TO COPY-------------------------------------------
        self.from_dir_entry_remote = customtkinter.CTkEntry(self.tabview.tab("Copy from remote branch"),
                                                            placeholder_text="Copy from directory")
        self.from_dir_entry_remote.grid(row=6, column=0, columnspan=1, padx=(30, 30), pady=(10, 10), sticky="nsew")
        # -------------------------------------------------------------------------------------------------
        # -----------------------------------WHERE TO COPY-------------------------------------------
        self.to_dir_entry_remote = customtkinter.CTkEntry(self.tabview.tab("Copy from remote branch"),
                                                          placeholder_text="Copy to directory")
        self.to_dir_entry_remote.grid(row=7, column=0, columnspan=1, padx=(30, 30), pady=(10, 10), sticky="nsew")
        # -------------------------------------------------------------------------------------------------

        # -----------------------------------PROJECT NAME-------------------------------------------
        self.project_entry_remote = customtkinter.CTkEntry(self.tabview.tab("Copy from remote branch"),
                                                           placeholder_text="Project name")
        self.project_entry_remote.grid(row=8, column=0, columnspan=1, padx=(30, 30), pady=(20, 20), sticky="nsew")
        # -------------------------------------------------------------------------------------------------

        # -------------------------------------COPY BUTTON------------------------------------
        self.copy_button = customtkinter.CTkButton(self.tabview.tab("Copy from remote branch"), border_width=2,
                                                   text_color=("gray10", "#DCE4EE"), text="COPY",
                                                   font=customtkinter.CTkFont(size=12, weight="bold"),
                                                   command=self.copy_process)
        self.copy_button.grid(row=8, column=1, padx=(30, 30), pady=(20, 20), sticky="nsew")
        # -------------------------------------------------------------------------------------------------
        # --------------------------------TEXT BOX----------------------------------------------------------
        self.textbox_2 = customtkinter.CTkTextbox(self.tabview.tab("Copy from remote branch"), width=300, height=190,
                                                  fg_color="#343638")
        self.textbox_2.grid(row=9, column=0, padx=(20, 10), pady=(10, 0), sticky="nsew")
        # -------------------------------------------------------------------------------------------------
        # ----------------------------------Timer LABEL----------------------------------
        self.label_timer = customtkinter.CTkLabel(self.tabview.tab("Copy from remote branch"), text="00:00:00",
                                                  font=customtkinter.CTkFont(size=12, weight="bold"))
        self.label_timer.grid(row=10, column=1, padx=(20, 10), pady=(10, 10), sticky='w')

        # -------------------------------------------------------------------------------------------------
        # ---------------------------DEFAULT VALUES--------------------------------------
        self.appearance_mode_optionemenu.set("System")
        self.scaling_optionemenu.set("100%")
        self.select_type_tab3.configure(state="disabled")
        self.browse_button_3_tab3.configure(state="disabled")
        self.browse_button_4_tab3.configure(state="disabled")
        self.from_dir_entry_remote.configure(state="disabled")
        self.to_dir_entry_remote.configure(state="disabled")
        self.select_branch_tab3.configure(state="disabled")
        self.copy_button.configure(state="disabled")
        self.textbox.configure(state="disabled")
        self.textbox_2.configure(state="disabled")
        self.project_entry_remote.configure(state="disabled")
        self.sidebar_button_1.configure(command=self.switch_to_local_repo_tab)
        self.sidebar_button_2.configure(command=self.switch_to_copy_local_tab)
        self.sidebar_button_3.configure(command=self.switch_to_copy_remote_tab)
        self.progressbar_1.configure(progress_color='')
        self.progressbar_1.configure(mode="determinate")
        self.progressbar_1.stop()
        self.progressbar_2.configure(progress_color='')
        self.progressbar_2.configure(mode="determinate")
        self.progressbar_2.stop()
        self.label_timer.configure(state="disabled")

        # ---------------------------------------------------------------------------------

        # --------------------------JSON DEFAULTS SETTINGS---------------------------------

        folder_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources")
        os.makedirs(folder_path, exist_ok=True)
        settings_file_path = os.path.join(folder_path, "settings.json")
        loaded_settings = self.load_settings_from_json(settings_file_path)
        self.update_program_state(loaded_settings)

    @staticmethod
    def load_settings_from_json(file_path):
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as file:
                    return json.load(file)
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON data in file: {file_path}")
        else:
            # Create default settings dictionary
            settings_dict = {
                "appearance_mode": "System",
                "ui_scaling": "100",
                "default_path_to_copy": "",
                "default_url_https_link": "",
                "default_radio_button_value": 0,
                "default_git_repository": "C:\\QA\\autotester_tools"
            }

            # Write default settings to the JSON file
            try:
                with open(file_path, 'w') as file:
                    json.dump(settings_dict, file, indent=4)
            except Exception as e:
                print(f"Error: Unable to create the JSON file: {file_path}. Reason: {e}")

        return {
            "appearance_mode": "System",
            "ui_scaling": "100",
            "default_path_to_copy": "",
            "default_url_https_link": "",
            "default_radio_button_value": 0,
            "default_git_repository": "C:\\QA\\autotester_tools"

        }

    def update_program_state(self, settings):
        # Update your program's state with the loaded settings
        self.appearance_mode_optionemenu.set(settings["appearance_mode"])
        self.scaling_optionemenu.set(settings["ui_scaling"])

        self.default_path_to_copy_entry.delete(0, "end")
        self.default_path_to_copy_entry.insert(0, settings["default_path_to_copy"])

        self.default_git_repository_entry.delete(0, "end")
        self.default_git_repository_entry.insert(0, settings["default_git_repository"])

        self.default_url_https_link_entry.delete(0, "end")
        self.default_url_https_link_entry.insert(0, settings["default_url_https_link"])
        if self.default_url_https_link_entry.get() != "":
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, settings["default_url_https_link"])

        if self.default_url_https_link_entry.get() == "":
            self.url_entry.delete(0, "end")
            self.url_entry.configure(placeholder_text="Repository to Clone")

        if self.default_path_to_copy_entry.get() != "":
            self.to_dir_entry_remote.configure(state="normal")
            self.to_dir_entry_remote.delete(0, "end")
            self.to_dir_entry_remote.insert(0, settings["default_path_to_copy"])
            self.to_dir_entry_remote.configure(state="disabled")
            self.to_dir_entry_local.delete(0, "end")
            self.to_dir_entry_local.insert(0, settings["default_path_to_copy"])

        if self.default_path_to_copy_entry.get() == "":
            self.to_dir_entry_remote.configure(state="normal")
            self.to_dir_entry_remote.delete(0, "end")
            self.to_dir_entry_remote.configure(placeholder_text="Copy to directory")
            self.to_dir_entry_remote.configure(state="disabled")
            self.to_dir_entry_local.delete(0, "end")
            self.to_dir_entry_local.configure(placeholder_text="Copy to directory")

        self.radio_var.set(settings["default_radio_button_value"])
        selected_radioButton_option(settings["default_radio_button_value"])

        customtkinter.set_appearance_mode(settings["appearance_mode"])
        customtkinter.set_default_color_theme("blue")
        window_scaling = int(settings["ui_scaling"].replace("%", "")) / 100
        customtkinter.set_window_scaling(window_scaling)

    def on_save_settings(self):
        # Get the current settings from the UI
        appearance_mode = self.appearance_mode_optionemenu.get()
        ui_scaling = self.scaling_optionemenu.get()
        default_path = self.default_path_to_copy_entry.get()
        default_repository = self.default_git_repository_entry.get()
        default_url_https_link = self.default_url_https_link_entry.get()
        default_radio_button_value = self.radio_var.get()
        if default_repository == "":
            messagebox.showerror("Error", "Default git repository can not be empty")
            return
        folder_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources")
        os.makedirs(folder_path, exist_ok=True)
        settings_file_path = os.path.join(folder_path, "settings.json")
        messagebox.showinfo("Save", "Settings was saved")

        settings_dict = {
            "appearance_mode": appearance_mode,
            "ui_scaling": ui_scaling,
            "default_path_to_copy": default_path,
            "default_url_https_link": default_url_https_link,
            "default_radio_button_value": default_radio_button_value,
            "default_git_repository": default_repository
        }

        with open(settings_file_path, 'w') as json_file:
            json.dump(settings_dict, json_file, indent=4)

        # Update the program's state with the saved settings
        self.update_program_state(settings_dict)

    # ----------------------------------------------------------------------------------------
    def open_about_window(self):
        AboutWindow(self)

    def clear_entry_boxes_local(self, result):
        # Clear the contents of the entry boxes
        self.from_dir_entry_local.delete(0, 'end')
        self.from_dir_entry_local.configure(placeholder_text="Copy from directory")
        self.project_entry_local.delete(0, 'end')
        self.project_entry_local.configure(placeholder_text="Project name")
        default_path = self.default_path_to_copy_entry.get()
        if not default_path:
            self.to_dir_entry_local.delete(0, 'end')
            self.to_dir_entry_local.configure(placeholder_text="Copy to directory")

    def clear_entry_boxes_remote(self, result):
        # Clear the contents of the entry boxes
        self.from_dir_entry_remote.delete(0, 'end')
        self.from_dir_entry_remote.configure(placeholder_text="Copy from directory")
        self.project_entry_remote.delete(0, 'end')
        self.project_entry_remote.configure(placeholder_text="Project name")
        default_path = self.default_path_to_copy_entry.get()
        if not default_path:
            self.to_dir_entry_remote.delete(0, 'end')
            self.to_dir_entry_remote.configure(placeholder_text="Copy to directory")

    def switch_to_copy_local_tab(self):
        self.tabview.set("Copy from local branch")

    def switch_to_copy_remote_tab(self):
        self.tabview.set("Copy from remote branch")

    def switch_to_local_repo_tab(self):
        self.tabview.set("Settings")

    def browse_2_tab3(self):
        folder_path = customtkinter.filedialog.askdirectory()
        if folder_path:
            folder_path_with_backslashes = folder_path.replace("/", "\\")
            self.destination_entry.delete(0, tk.END)
            self.destination_entry.insert(0, folder_path_with_backslashes)

    def browse_3_tab3(self):
        selected_option = self.select_type_tab3.get()
        if selected_option == "Campaign":
            files_filter = [("ATC Files", "*.atc")]
        elif selected_option == "Test":
            files_filter = [("ATTC Files", "*.attc")]
        elif selected_option == "Procedure":
            files_filter = [("ATAP Files", "*.atap")]
        else:
            files_filter = []
        file_path = filedialog.askopenfilename(filetypes=files_filter)
        if file_path:
            file_path_with_backslashes = file_path.replace("/", "\\")
            self.from_dir_entry_remote.delete(0, tk.END)
            self.from_dir_entry_remote.insert(0, file_path_with_backslashes)

    def browse_4_tab3(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            folder_path_with_backslashes = folder_path.replace("/", "\\")
            self.to_dir_entry_remote.delete(0, tk.END)
            self.to_dir_entry_remote.insert(0, folder_path_with_backslashes)

    def browse_1_tab2(self):
        selected_option = self.select_type_tab2.get()
        if selected_option == "Campaign":
            files_filter = [("ATC Files", "*.atc")]
        elif selected_option == "Test":
            files_filter = [("ATTC Files", "*.attc")]
        elif selected_option == "Procedure":
            files_filter = [("ATAP Files", "*.atap")]
        else:
            files_filter = []
        file_path = filedialog.askopenfilename(filetypes=files_filter)
        if file_path:
            file_path_with_backslashes = file_path.replace("/", "\\")
            self.from_dir_entry_local.delete(0, tk.END)
            self.from_dir_entry_local.insert(0, file_path_with_backslashes)

    def browse_2_tab2(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            folder_path_with_backslashes = folder_path.replace("/", "\\")
            self.to_dir_entry_local.delete(0, tk.END)
            self.to_dir_entry_local.insert(0, folder_path_with_backslashes)

    def browse_1_settings(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            folder_path_with_backslashes = folder_path.replace("/", "\\")
            self.default_path_to_copy_entry.delete(0, tk.END)
            self.default_path_to_copy_entry.insert(0, folder_path_with_backslashes)

    def start_timer(self):
        self.clone_button.configure(state="disabled")
        self.running = True
        self.start_time = time.time()
        threading.Thread(target=self.update_timer).start()

    def stop_timer(self):
        self.running = False
        self.clone_button.configure(state="normal")

    def update_timer(self):
        current_tab_name = self.tabview.get()
        while self.running:
            elapsed_time = time.time() - self.start_time
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            milliseconds = int((elapsed_time - int(elapsed_time)) * 1000)
            time_str = f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
            if current_tab_name == "Copy from remote branch":
                self.label_timer.configure(text=time_str)
                time.sleep(0.1)
            elif current_tab_name == "Copy from local branch":
                self.label_timer_1.configure(text=time_str)
                time.sleep(0.1)

    @staticmethod
    def open_logs_folder():
        log_folder = "logs"
        os.makedirs(log_folder, exist_ok=True)
        os.startfile(log_folder)

    def show_error_message(self, message):
        messagebox.showerror("Error in Logs", "Something goes wrong, Take a look in log report")
        self.progressbar_2_stop()
        self.progressbar_1_stop()
        self.stop_timer()

    # --------------------------------CLONING PROCESS-----------------------------------------
    @staticmethod
    def check_git_in_path(path):
        try:
            git.Repo(path, search_parent_directories=True)
            return True
        except git.exc.InvalidGitRepositoryError:
            return False

    def cloning_process_start(self):
        # -----------------------------VARIABLES-------------------------------------------
        repo_url = self.url_entry.get()
        destination = self.destination_entry.get()
        subdir = self.subdir_entry.get()
        direction = f"{destination}\\{subdir}"
        logging.info(f"Direction to Clone:{direction}")
        # ---------------------------------------------------------------------------------

        if os.path.exists(direction):
            overwrite = messagebox.askquestion("Repository Folder Exists",
                                               "Repository folder already exists. Do you want to overwrite it?")
            if overwrite.lower() == 'yes':
                git.rmtree(direction)
            else:
                return

        os.mkdir(direction)
        messagebox.showinfo("Cloning Repository", "Cloning the repository. Please wait...")
        self.start_timer()
        self.progressbar_1_start()

        clone_thread = threading.Thread(target=self.cloning_process, args=(repo_url, direction))
        clone_thread.start()
        logging.info(f"******************* START CLONE THREAD *******************")

    def cloning_process(self, repo_url, direction):
        try:
            clone_progress = CloneProgress(self)
            Repo.clone_from(repo_url, direction, progress=clone_progress)
            self.after(0, self.clone_process_complete, True)
        except Exception as e:
            print("Cloning failed:", str(e))
            logging.error("Cloning failed:", exc_info=e)
            self.after(0, self.clone_process_complete, False)

    def get_remote_branches(self):
        remote_branches_command = f"git ls-remote --heads {self.url_entry.get()}"
        try:
            output = subprocess.check_output(remote_branches_command, shell=True, text=True).splitlines()
            branches = [branch.split("refs/heads/")[-1] for branch in output]
            self.textbox_2.configure(state="normal")
            self.textbox_2.delete(1.0, "end")
            self.textbox_2.insert("end", "List of available branches:\n")
            logging.info("List of available branches:")
            for brunch in branches:
                self.update_textbox(brunch)
                logging.info(f"{brunch}")
            self.select_branch_tab3.configure(values=branches)
        except subprocess.CalledProcessError as e:
            logging.error("Error:", exc_info=e)

    def clone_process_complete(self, result):
        # -----------------------------VARIABLES-------------------------------------------
        destination = self.destination_entry.get()
        destination = destination.replace("\\", "\\\\")
        subdir = self.subdir_entry.get()
        direction_repo = f"{destination}\\\\{subdir}"
        default_repository = self.default_git_repository_entry.get()
        # ---------------------------------------------------------------------------------
        if result:
            self.textbox_2.configure(state="normal")
            self.textbox_2.delete(1.0, "end")
            self.textbox_2.insert("end", "Converting files to the new location, please wait:\n")
            logging.info(f"Converting files to the new location, please wait:")
            self.textbox_2.see("end")
            self.textbox_2.configure(state="disabled")
            self.process_and_print_results(direction_repo, default_repository, direction_repo)
            thread = threading.Thread(target=self.get_remote_branches)
            thread.start()
        else:
            messagebox.showerror("Cloning Failed", "Failed to clone the repository.")
            logging.info(f"************************ Failed to clone the repository ******************************")
            self.progressbar_1_stop()

    def progressbar_1_start(self):
        self.progressbar_1.configure(progress_color='#1F6AA5')
        self.progressbar_1.configure(mode="indeterminate")
        self.progressbar_1.start()

    def progressbar_1_stop(self):
        self.progressbar_1.configure(progress_color='')
        self.progressbar_1.configure(mode="determinate")
        self.progressbar_1.stop()

    def progressbar_2_stop(self):
        self.progressbar_2.configure(progress_color='')
        self.progressbar_2.configure(mode="determinate")
        self.progressbar_2.stop()

    def progressbar_2_start(self):
        self.progressbar_2.configure(progress_color='#1F6AA5')
        self.progressbar_2.configure(mode="indeterminate")
        self.progressbar_2.start()

    # ---------------------------------------------------------------------------------------------------
    # ---------------------------------------------CONVERT FILES TO NEW REPOSITORY-------------------------
    def process_and_print_results(self, dir_path, old_string, new_string):
        def on_conversion_complete():
            self.textbox_2.configure(state="normal")
            self.textbox_2.insert("end", "Processing complete.\n")
            self.textbox_2.see("end")
            self.textbox_2.configure(state="disabled")
            self.stop_timer()
            messagebox.showinfo("Clone Completed", "Repository clone completed.")
            logging.info(f"************************ Repository clone completed ******************************")
            self.progressbar_1_stop()
            self.select_type_tab3.configure(state="normal")
            self.browse_button_3_tab3.configure(state="normal")
            self.browse_button_4_tab3.configure(state="normal")
            self.from_dir_entry_remote.configure(state="normal")
            self.to_dir_entry_remote.configure(state="normal")
            self.copy_button.configure(state="normal")
            self.project_entry_remote.configure(state="normal")
            self.select_branch_tab3.configure(state="normal")

        converter = ConvertLogic(self, dir_path, old_string, new_string, on_conversion_complete)
        converter.start()

    def process_result(self, result):
        self.update_textbox(result)
        logging.info(result)

    def update_textbox(self, result):
        self.textbox_2.configure(state="normal", text_color='white')
        self.textbox_2.insert("end", f"{result}\n")
        self.textbox_2.see("end")
        self.textbox_2.configure(state="disabled")

    def update_textbox_local(self, result):
        self.textbox.configure(state="normal", text_color='white')
        self.textbox.insert("end", f"{result}\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def update_textbox_local_exeption(self, result):
        self.textbox.configure(state="normal", text_color='#F65353')
        self.textbox.insert("end", f"{result}\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def update_textbox_remote_exeption(self, result):
        self.textbox_2.configure(state="normal", text_color='#F65353')
        self.textbox_2.insert("end", f"{result}\n")
        self.textbox_2.see("end")
        self.textbox_2.configure(state="disabled")

    def process_queue(self):
        try:
            while True:
                message = self.queue.get_nowait()
                self.update_textbox(message)
        except queue.Empty:
            self.after(100, self.process_queue)

    # -------------------------------------------------------------------------------------------------

    def checkout_branch(self, selected_branch):
        # -----------------------------VARIABLES-------------------------------------------
        destination = self.destination_entry.get()
        subdir = self.subdir_entry.get()
        checkout_command = f"git checkout {selected_branch}"
        logging.info(f"Checkout: {checkout_command}")
        checkout_directory = os.path.join(destination, subdir)
        # ------------------------------------------------------------------------------------

        messagebox.showinfo("Checkout Branch", "Checking out branch. Please wait...")
        self.start_timer()
        self.progressbar_1_start()

        # Use threading to run the checkout process in a separate thread
        checkout_thread = threading.Thread(target=self.run_checkout_command,
                                           args=(checkout_command, checkout_directory, selected_branch))
        checkout_thread.start()
        logging.debug(f"************************ START CHECKOUT THREAD ******************************")

    def run_checkout_command(self, checkout_command, checkout_directory, selected_branch):
        # -----------------------------VARIABLES-------------------------------------------
        destination = self.destination_entry.get()
        destination = destination.replace("\\", "\\\\")
        subdir = self.subdir_entry.get()
        direction_repo = f"{destination}\\\\{subdir}"
        logging.info(f"Direction repo:{direction_repo}")
        default_repository = self.default_git_repository_entry.get()
        logging.info(f"Default repository: {default_repository}")
        reset_command = f'git reset --hard origin/{self.select_branch_tab3.get()}'
        # ------------------------------------------------------------------------------------
        try:
            reset_output = self.run_git_command(reset_command, checkout_directory)
            checkout_output = self.run_git_command(checkout_command, checkout_directory)
            if reset_output is not None and checkout_output is not None:
                self.textbox_2.configure(state="normal")
                self.textbox_2.delete(1.0, "end")
                self.update_textbox("Reset Output:")
                logging.debug(f"************************ Reset Output: {reset_output}")
                self.update_textbox(reset_output)
                self.update_textbox("")
                self.update_textbox("Checkout Output:")
                logging.debug(f"************************ Checkout Output: {checkout_output}")
                self.update_textbox(checkout_output)
            self.process_and_print_results(direction_repo, default_repository, direction_repo)

        except subprocess.CalledProcessError as e:
            error_message = f"Error while checking out branch '{selected_branch}': {e.stderr}"
            messagebox.showerror("Checkout Failed", error_message)
            logging.error(error_message, exc_info=e)

    @staticmethod
    def run_git_command(command, cwd):
        logging.debug(f"Running command: {command} in directory: {cwd}")
        try:
            result = subprocess.run(command, cwd=cwd, shell=True, check=True, stdout=subprocess.PIPE, text=True)
            logging.debug(f"************************ Command output:\n{result.stdout.strip()}")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logging.error(f"************************ Command failed with error:\n{e} ")
            raise

    @staticmethod
    def change_appearance_mode_event(new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    @staticmethod
    def change_scaling_event(new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)

    def copy_campaign_thread_local(self, from_path, project_name, to_path):
        try:
            self.start_timer()
            result = copy_campaign(from_path, project_name, to_path)
            if result is not None:
                list_of_exceptions, list_of_copy_files = result
                if list_of_copy_files:
                    self.textbox.configure(state="normal", text_color='white')
                    self.textbox.delete(1.0, "end")
                    self.textbox.insert("end", "Copied files list:\n")
                    for file in list_of_copy_files:
                        self.after(0, self.update_textbox_local(file))
                        logging.info(f"Copied file: {file}")
                if list_of_exceptions:
                    self.textbox.configure(state="normal", text_color='#F65353')
                    self.textbox.delete(1.0, "end")
                    self.textbox.insert("end", "Exceptions occurred during the copy process:\n")
                    logging.error(
                        f"************************ Exceptions occurred during the copy process: ************************")
                    for exception in list_of_exceptions:
                        self.after(0, self.update_textbox_local_exeption(exception))
                        logging.error(f"Can not find this file:{exception}")
                    self.stop_timer()
                    messagebox.showerror("Copy process", "Exception during copy process")
                    logging.error("************************ Exception during copy process ************************")
                    self.progressbar_2_stop()
                else:
                    self.stop_timer()
                    messagebox.showinfo("Copy process", "Copy completed successfully!")
                    logging.info(f"************************ Copy completed successfully! ************************")
                    self.progressbar_2_stop()
            else:
                self.stop_timer()
                messagebox.showinfo("Copy process", "Copying campaign cancelled.")
                logging.info(f"************************ Copying campaign cancelled. ************************")
                self.progressbar_2_stop()
        except Exception as e:
            logging.error(
                "************************ Exception within copy_campaign_thread_local: ************************",
                exc_info=e)
            self.stop_timer()
            self.progressbar_2_stop()

    def copy_test_thread_local(self, from_path, project_name, to_path, response):
        try:
            self.start_timer()
            result = copy_test(from_path, project_name, to_path, response)
            if result is not None:
                list_of_exceptions, list_of_copy_files = result
                if list_of_copy_files:
                    self.textbox.configure(state="normal", text_color='white')
                    self.textbox.delete(1.0, "end")
                    self.textbox.insert("end", "Copied files list:\n")
                    for file in list_of_copy_files:
                        self.after(0, self.update_textbox_local(file))
                        logging.info(f"Copied file: {file}")
                if list_of_exceptions:
                    self.textbox.configure(state="normal", text_color='#F65353')
                    self.textbox.delete(1.0, "end")
                    self.textbox.insert("end", "Exceptions occurred during the copy process:\n")
                    logging.error(
                        f"************************ Exceptions occurred during the copy process: ************************")
                    for exception in list_of_exceptions:
                        self.after(0, self.update_textbox_local_exeption(exception))
                        logging.error(f"Can not find this file:{exception}")
                    self.stop_timer()
                    messagebox.showerror("Copy process", "Exception during copy process")
                    logging.error("************************ Exception during copy process ************************")
                    self.progressbar_2_stop()
                else:
                    self.stop_timer()
                    messagebox.showinfo("Copy process", "Copy completed successfully!")
                    logging.info(f"************************ Copy completed successfully! ************************")
                    self.progressbar_2_stop()
            else:
                self.stop_timer()
                messagebox.showinfo("Copy process", "Copying test cancelled.")
                logging.info(f"************************ Copying test cancelled. ************************")
                self.progressbar_2_stop()
        except Exception as e:
            logging.error("************************ Exception within copy_test_thread_local: ************************",
                          exc_info=e)
            self.stop_timer()
            self.progressbar_2_stop()

    def copy_procedure_thread_local(self, from_path, project_name, to_path, response):
        try:
            self.start_timer()
            result = copy_procedure(from_path, project_name, to_path, response)
            if result is not None:
                list_of_exceptions, list_of_copy_files = result
                if list_of_copy_files:
                    self.textbox.configure(state="normal", text_color='white')
                    self.textbox.delete(1.0, "end")
                    self.textbox.insert("end", "Copied files list:\n")
                    for file in list_of_copy_files:
                        self.after(0, self.update_textbox_local(file))
                        logging.info(f"Copied file: {file}")
                if list_of_exceptions:
                    self.textbox.configure(state="normal", text_color='#F65353')
                    self.textbox.delete(1.0, "end")
                    self.textbox.insert("end", "Exceptions occurred during the copy process:\n")
                    logging.error(
                        f"************************ Exceptions occurred during the copy process: ************************")
                    for exception in list_of_exceptions:
                        self.after(0, self.update_textbox_local_exeption(exception))
                        logging.error(f"Can not find this file:{exception}")
                    self.stop_timer()
                    messagebox.showerror("Copy process", "Exception during copy process")
                    logging.error("************************ Exception during copy process ************************")
                    self.progressbar_2_stop()
                else:
                    self.stop_timer()
                    messagebox.showinfo("Copy process", "Copy completed successfully!")
                    logging.info(f"************************ Copy completed successfully! ************************")
                    self.progressbar_2_stop()
            else:
                self.stop_timer()
                messagebox.showinfo("Copy process", "Copying procedure cancelled.")
                logging.info(f"************************ Copying procedure cancelled. ************************")
                self.progressbar_2_stop()
        except Exception as e:
            logging.error(
                "************************ Exception within copy_procedure_thread_local: ************************",
                exc_info=e)
            self.stop_timer()
            self.progressbar_2_stop()

    def copy_campaign_thread_remote(self, from_path, project_name, to_path):
        try:
            self.start_timer()
            result = copy_campaign(from_path, project_name, to_path)
            if result is not None:
                list_of_exceptions, list_of_copy_files = result
                if list_of_copy_files:
                    self.textbox_2.configure(state="normal", text_color='white')
                    self.textbox_2.delete(1.0, "end")
                    self.textbox_2.insert("end", "Copied files list:\n")
                    for file in list_of_copy_files:
                        self.after(0, self.update_textbox(file))
                        logging.info(f"Copied file: {file}")
                if list_of_exceptions:
                    self.textbox_2.configure(state="normal", text_color='#F65353')
                    self.textbox_2.delete(1.0, "end")
                    self.textbox_2.insert("end", "Exceptions occurred during the copy process:\n")
                    for exception in list_of_exceptions:
                        self.after(0, self.update_textbox_remote_exeption(exception))
                        logging.error(f"Can not find this file:{exception}")
                    self.stop_timer()
                    messagebox.showerror("Copy process", "Exception during copy process")
                    logging.error("************************ Exception during copy process ************************")
                    self.progressbar_1_stop()
                else:
                    self.stop_timer()
                    messagebox.showinfo("Copy process", "Copy completed successfully!")
                    logging.info(f"************************ Copy completed successfully! ************************")
                    self.progressbar_1_stop()
            else:
                self.stop_timer()
                messagebox.showinfo("Copy process", "Copying campaign cancelled.")
                logging.info(f"************************ Copying campaign cancelled. ************************")
                self.progressbar_1_stop()
        except Exception as e:
            logging.error(
                "************************Exception within copy_campaign_thread_remote: ************************",
                exc_info=e)
            self.stop_timer()
            self.progressbar_2_stop()

    def copy_test_thread_remote(self, from_path, project_name, to_path, response):
        try:
            self.start_timer()
            result = copy_test(from_path, project_name, to_path, response)
            if result is not None:
                list_of_exceptions, list_of_copy_files = result
                if list_of_copy_files:
                    self.textbox_2.configure(state="normal", text_color='white')
                    self.textbox_2.delete(1.0, "end")
                    self.textbox_2.insert("end", "Copied files list:\n")
                    for file in list_of_copy_files:
                        self.after(0, self.update_textbox(file))
                        logging.info(f"Copied file: {file}")
                if list_of_exceptions:
                    self.textbox_2.configure(state="normal", text_color='#F65353')
                    self.textbox_2.delete(1.0, "end")
                    self.textbox_2.insert("end", "Exceptions occurred during the copy process:\n")
                    logging.error(
                        f"************************ Exceptions occurred during the copy process: ************************")
                    for exception in list_of_exceptions:
                        self.after(0, self.update_textbox_remote_exeption(exception))
                        logging.error(f"Can not find this file:{exception}")
                    self.stop_timer()
                    messagebox.showerror("Copy process", "Exception during copy process")
                    logging.error("************************ Exception during copy process ************************")
                    self.progressbar_1_stop()
                else:
                    self.stop_timer()
                    messagebox.showinfo("Copy process", "Copy completed successfully!")
                    logging.info(f"************************ Copy completed successfully! ************************")
                    self.progressbar_1_stop()
            else:
                self.stop_timer()
                messagebox.showinfo("Copy process", "Copying test cancelled.")
                logging.info(f"************************ Copying test cancelled. ************************")
                self.progressbar_1_stop()
        except Exception as e:
            logging.error("************************Exception within copy_test_thread_remote: ************************",
                          exc_info=e)
            self.stop_timer()
            self.progressbar_2_stop()

    def copy_procedure_thread_remote(self, from_path, project_name, to_path, response):
        try:
            self.start_timer()
            result = copy_procedure(from_path, project_name, to_path, response)
            if result is not None:
                list_of_exceptions, list_of_copy_files = result
                if list_of_copy_files:
                    self.textbox_2.configure(state="normal", text_color='white')
                    self.textbox_2.delete(1.0, "end")
                    self.textbox_2.insert("end", "Copied files list:\n")
                    for file in list_of_copy_files:
                        self.after(0, self.update_textbox(file))
                        logging.info(f"Copied file: {file}")
                if list_of_exceptions:
                    self.textbox_2.configure(state="normal", text_color='#F65353')
                    self.textbox_2.delete(1.0, "end")
                    self.textbox_2.insert("end", "Exceptions occurred during the copy process:\n")
                    logging.error(
                        f"************************ Exceptions occurred during the copy process: ************************")
                    for exception in list_of_exceptions:
                        self.after(0, self.update_textbox_remote_exeption(exception))
                        logging.error(f"Can not find this file:{exception}")
                    self.stop_timer()
                    messagebox.showerror("Copy process", "Exception during copy process")
                    logging.error("************************ Exception during copy process ************************")
                    self.progressbar_1_stop()
                else:
                    self.stop_timer()
                    messagebox.showinfo("Copy process", "Copy completed successfully!")
                    logging.info(f"************************ Copy completed successfully! ************************")
                    self.progressbar_1_stop()
            else:
                self.stop_timer()
                messagebox.showinfo("Copy process", "Copying procedure cancelled.")
                logging.info(f"************************ Copying procedure cancelled. ************************")
                self.progressbar_1_stop()
        except Exception as e:
            logging.error(
                "************************Exception within copy_procedure_thread_remote: ************************",
                exc_info=e)
            self.stop_timer()
            self.progressbar_2_stop()

    def copy_process(self):
        current_tab_name = self.tabview.get()
        # ------------------------------------LOCAL branch------------------------------------------
        if current_tab_name == "Copy from local branch":
            project_name = self.project_entry_local.get()
            logging.info(f"Project name set to: {project_name}")
            from_path = self.from_dir_entry_local.get()
            logging.info(f"From where to copy set to: {from_path}")
            to_path = self.to_dir_entry_local.get()
            logging.info(f"Where to copy set to: {to_path}")

            if not from_path:
                messagebox.showerror("Error", "Please enter from where to copy.")
                return
            if not to_path:
                messagebox.showerror("Error", "Please enter where to copy.")
                return
            if not project_name:
                messagebox.showerror("Error", "Please enter a project name.")
                return
            if not self.check_git_in_path(to_path):
                messagebox.showerror("Error", "You can not copy to non git repository")
                return
            # --------------------------COPY CAMPAIGN IN LOCAL---------------------------------
            if self.select_type_tab2.get() == "Campaign":
                messagebox.showinfo("Copy process", "Copy process started!")
                self.progressbar_2_start()
                copy_thread = threading.Thread(target=self.copy_campaign_thread_local,
                                               args=(from_path, project_name, to_path))
                copy_thread.start()
                logging.info("************************ Strting Copy THREAD Campaign ************************")
            # ----------------------------------------------------------------------------------
            # ---------------------------COPY TEST IN LOCAL----------------------------------
            elif self.select_type_tab2.get() == "Test":
                messagebox.showinfo("Copy process", "Copy process started!")
                self.progressbar_2_start()
                response = self.radio_var.get()
                copy_thread = threading.Thread(target=self.copy_test_thread_local,
                                               args=(from_path, project_name, to_path, response))
                copy_thread.start()
                logging.info("************************ Strting Copy THREAD Test ************************")
            # ----------------------------------------------------------------------------------

            # -------------------------COPY PROCEDURE IN LOCAL------------------------------
            elif self.select_type_tab2.get() == "Procedure":
                messagebox.showinfo("Copy process", "Copy process started!")
                self.progressbar_2_start()
                response = self.radio_var.get()
                copy_thread = threading.Thread(target=self.copy_procedure_thread_local,
                                               args=(from_path, project_name, to_path, response))
                copy_thread.start()
                logging.info("************************ Strting Copy THREAD Procedure ************************")
        # --------------------------------------------------------------------------------------------

        # ------------------------------------REMOTE branch------------------------------------------
        if current_tab_name == "Copy from remote branch":
            project_name = self.project_entry_remote.get()
            logging.info(f"Project name set to: {project_name}")
            from_path = self.from_dir_entry_remote.get()
            logging.info(f"From where to copy set to: {from_path}")
            to_path = self.to_dir_entry_remote.get()
            logging.info(f"Where to copy set to: {to_path}")

            if not from_path:
                messagebox.showerror("Error", "Please enter from where to copy.")
                return
            if not to_path:
                messagebox.showerror("Error", "Please enter where to copy.")
                return
            if not project_name:
                messagebox.showerror("Error", "Please enter a project name.")
                return
            if not self.check_git_in_path(from_path):
                messagebox.showerror("Error", "You can not copy from non git repository")
                return
            if not self.check_git_in_path(to_path):
                messagebox.showerror("Error", "You can not copy to non git repository")
                return
            # -----------------------------------------COPY CAMPAIGN REMOTE--------------------------------------------

            if self.select_type_tab3.get() == "Campaign":
                messagebox.showinfo("Copy process", "Copy process started!")
                self.progressbar_1_start()
                copy_thread = threading.Thread(target=self.copy_campaign_thread_remote,
                                               args=(from_path, project_name, to_path))
                copy_thread.start()
                logging.info("************************ Strting Copy THREAD Campaign ************************")
            # -----------------------------------------COPY TEST REMOTE--------------------------------------------
            elif self.select_type_tab3.get() == "Test":
                messagebox.showinfo("Copy process", "Copy process started!")
                self.progressbar_1_start()
                response = self.radio_var.get()
                copy_thread = threading.Thread(target=self.copy_test_thread_remote,
                                               args=(from_path, project_name, to_path, response))
                copy_thread.start()
                logging.info("************************ Strting Copy THREAD Test ************************")
            # -------------------------------------------COPY PROCEDURE REMOTE---------------------------------------
            elif self.select_type_tab3.get() == "Procedure":
                messagebox.showinfo("Copy process", "Copy process started!")
                self.progressbar_1_start()
                response = self.radio_var.get()
                copy_thread = threading.Thread(target=self.copy_procedure_thread_remote,
                                               args=(from_path, project_name, to_path, response))
                copy_thread.start()
                logging.info("********************  Strting Copy THREAD Procedure  ************************")
        # --------------------------------------------------------------------------------------------


class ExceptionFilter(logging.Filter):
    def filter(self, record):
        return "Exception" in record.msg


def custom_excepthook(exc_type, exc_value, exc_traceback):
    logging.error("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))


# Set the custom excepthook
sys.excepthook = custom_excepthook


def main():
    log_folder = "logs"
    os.makedirs(log_folder, exist_ok=True)

    # Create a log filename with a timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    log_filename = os.path.join(log_folder, f"log_{timestamp}.log")

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_filename, mode="a")
        ]
    )

    app = App()

    app.show_error_message = app.show_error_message
    exception_filter = ExceptionFilter()
    handler = ErrorPopupHandler(app)
    handler.addFilter(exception_filter)
    handler.app = app
    logging.getLogger().addHandler(handler)

    app.mainloop()


if __name__ == "__main__":
    main()
