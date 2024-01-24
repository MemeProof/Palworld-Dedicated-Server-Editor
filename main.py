from tkinter import *
from tkinter import ttk
from tkinter import filedialog
import webbrowser
from tkinter import messagebox
import configparser
import os
import re
import shutil
from datetime import datetime

config_file = 'settings.ini'
config = configparser.ConfigParser()
config.read(config_file)

# Dict to store input fields
input_fields = {}

### ask to save before closing ###
def on_close(main_window, config_palsettings, config_playersettings, config_othersettings, config_serversettings):
    if messagebox.askyesno("Save before quitting", "Do you want to save before closing?"):
        on_save(config_palsettings, config_playersettings, config_othersettings, config_serversettings)
    main_window.destroy()

### used to backup files ###
def backup_file(original_file, backup_folder, max_backups=10):
    # make sure the backup folder exists
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    # create timestamped backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}_{os.path.basename(original_file)}"
    backup_path = os.path.join(backup_folder, backup_filename)

    # Copy the file -> backup
    shutil.copy2(original_file, backup_path)

    # Remove old backups, keeping only the last `max_backups` number of files
    all_backups = sorted(
        [os.path.join(backup_folder, f) for f in os.listdir(backup_folder)],
        key=os.path.getmtime
    )
    for old_backup in all_backups[:-max_backups]:
        os.remove(old_backup)

### handles all the config saving for the palworld settings and saving the program user settings to settings.ini ###
def on_save(config_palsettings, config_playersettings, config_othersettings, config_serversettings):    
     # Check if LastDirectory is set in the config
    last_directory = load_directory_path(config, config_file)
    if not last_directory:
        messagebox.showerror("Error", "The palserver directory is not set. Please choose your palserver directory first. On the Info tab.")
        return  # Stop the save function

    # Defines the order of settings based on the defaults given in DefaultPalWorldSettings.ini
    settings_order = [
        "Difficulty", "DayTimeSpeedRate", "NightTimeSpeedRate", "ExpRate", "PalCaptureRate",
        "PalSpawnNumRate", "PalDamageRateAttack", "PalDamageRateDefense", "PlayerDamageRateAttack",
        "PlayerDamageRateDefense", "PlayerStomachDecreaceRate", "PlayerStaminaDecreaceRate",
        "PlayerAutoHPRegeneRate", "PlayerAutoHpRegeneRateInSleep", "PalStomachDecreaceRate",
        "PalStaminaDecreaceRate", "PalAutoHPRegeneRate", "PalAutoHpRegeneRateInSleep",
        "BuildObjectDamageRate","BuildObjectDeteriorationDamageRate","CollectionDropRate",
        "CollectionObjectHpRate","CollectionObjectRespawnSpeedRate","EnemyDropItemRate",
        "DeathPenalty","bEnablePlayerToPlayerDamage","bEnableFriendlyFire","bEnableInvaderEnemy",
        "bActiveUNKO","bEnableAimAssistPad","bEnableAimAssistKeyboard","DropItemMaxNum",
        "DropItemMaxNum_UNKO","BaseCampMaxNum","BaseCampWorkerMaxNum","DropItemAliveMaxHours",
        "bAutoResetGuildNoOnlinePlayers","AutoResetGuildTimeNoOnlinePlayers","GuildPlayerMaxNum",
        "PalEggDefaultHatchingTime","WorkSpeedRate","bIsMultiplay","bIsPvP","bCanPickupOtherGuildDeathPenaltyDrop",
        "bEnableNonLoginPenalty","bEnableFastTravel","bIsStartLocationSelectByMap","bExistPlayerAfterLogout",
        "bEnableDefenseOtherGuildPlayer","CoopPlayerMaxNum","ServerPlayerMaxNum","ServerName",
        "ServerDescription","AdminPassword","ServerPassword","PublicPort","PublicIP",
        "RCONEnabled","RCONPort","Region","bUseAuth","BanListURL"
    ]

    # get data from configurators
    pal_settings = config_palsettings.get_input_values()
    player_settings = config_playersettings.get_input_values()
    other_settings = config_othersettings.get_input_values()
    server_settings = config_serversettings.get_input_values()

    # Combine all settings into one dictionary, makes collection of data a little easier
    all_settings = {**pal_settings, **player_settings, **other_settings, **server_settings}

    formatted_settings = {}

    # Set default values if not set
    for setting in settings_order:
    # Handle special cases for non-numeric defaults
        value = all_settings.get(setting, "1.000000")  # Default value for numeric settings, this shouldn't happen but just in case
        if setting == "Difficulty" and not all_settings[setting]:
            all_settings[setting] = "None"
        if setting in ["ServerName", "ServerDescription", "AdminPassword", "ServerPassword", "PublicIP", "Region", "BanListURL"]:  # Add other text fields as needed
            value = f'"{value}"'  # Wrap text fields in quotes
        formatted_settings[setting] = value

    # Format the data in ordered specified in the settings_order var. I don't know if the everything needs to be in a specific order for palworld settings, but just incase it does, this handles that.
    settings_str = ",".join(f"{key}={formatted_settings[key]}" for key in settings_order)

    # Prepare the full string to write
    full_settings_str = f"OptionSettings=({settings_str})"

    # Backup the existing file before overwriting
    pal_server_root_dir = load_directory_path(config, config_file)
    server_settings_path = os.path.join(pal_server_root_dir, 'Pal', 'Saved', 'Config', 'WindowsServer', 'PalWorldSettings.ini')
    backup_folder ='Backup'
    # Only backup if the file exists...of course
    if os.path.exists(server_settings_path):
        backup_file(server_settings_path, backup_folder)

    # Write to the PalWorldSettings.ini file
    if pal_server_root_dir:
        server_settings_path = os.path.join(pal_server_root_dir, 'Pal', 'Saved', 'Config', 'WindowsServer', 'PalWorldSettings.ini')
        try:
            with open(server_settings_path, 'w') as writeFile:
                writeFile.write('[/Script/Pal.PalGameWorldSettings]\n')
                writeFile.write(full_settings_str)
        except IOError as e:
            print(f"Error writing to the server settings file: {e}")
    # Save settings from each configurator
    config_palsettings.save_config()
    config_playersettings.save_config()
    config_othersettings.save_config()
    config_serversettings.save_config()
    messagebox.showinfo("Success", "Settings saved successfully!")


class Configurator_Manager:
    def __init__(self, parent):
        self.parent = parent
        self.row = 0 # handles moving each new input field down
        self.input_fields = {}
        self.config = config
        self.config_file = config_file

    '''main configurator setup:
    Description: The value to the left of the input widget and tells user what the setting is for
    input_type: helps specify what the input widget should be. whether its decimal only, combo box, text, or id
    identifier: the name of the setting as it is listed in the palworldsettings.ini. This is used for both the ordering and saving of the values in the settings file
    options: used for combo boxes. list of options
    default_value: default value for the input widget
    align: left, right, or center for aligning the whole widget
    combo_state: readonly, normal, or disabled for combo boxes. This is mainly so the state can be set as readonly but can be changed if needed
    '''
    def add_config_line(self, description, input_type, identifier, options=None, default_value="1.000000", align="left", combo_state="readonly"):
        description_label = Label(self.parent, text=description, font=("Arial", 10), justify=align) 
        description_label.grid(row=self.row, column=0, sticky="w", padx=5, pady=5)
        
        if self.config.has_option('Settings', identifier):
            value = self.config.get('Settings', identifier)
        else:
            value = default_value

        if input_type == 'entry':
            vcmd = (self.parent.register(self.on_validate), '%P')# handle input validation
            input_widget = Entry(self.parent, validate="key", validatecommand=vcmd) # handle input validation
            input_widget.insert(0, value)  # Insert the value into the Entry widget
        elif input_type == 'ip':
            ip_vcmd = (self.parent.register(self.validate_ip), '%P')# handle input validation
            input_widget = Entry(self.parent, validate="key", validatecommand=ip_vcmd)# handle input validation
            input_widget.insert(0, value)  # Insert the value into the Entry widget
        elif input_type == 'combo' and options is not None:
            input_widget = ttk.Combobox(self.parent, values=options,state=combo_state)
            if value in options:
                input_widget.set(value)
            else:
                input_widget.set(options[0])
        elif input_type == 'text':  # For regular text entry without validation
            input_widget = Entry(self.parent)
            input_widget.insert(0, value)
        else:
            raise ValueError("Invalid input type or missing options for combo box")

        input_widget.grid(row=self.row, column=1, sticky="ew", padx=2, pady=5)
        self.parent.columnconfigure(1, weight=1)

        self.input_fields[identifier] = input_widget
        self.row += 1  # Increment the row for the next config widget line

### validate functions just handle input validation so decimals and ip addresses work ###
    def on_validate(self, P):
        if P == "":
            return True  # Allow the change if the field is being cleared
        try:
            float(P)
            return True
        except ValueError:
            return False
    def validate_ip(self, P):
        if P == "":
            return True  # Allow the change if the field is being cleared

        # IP address regex pattern
        ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){0,3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)?$'

        # Validate against the regex pattern
        return re.match(ip_pattern, P) is not None

### hanldles getting the input values to be written to the config file ###
    def get_input_values(self):
        values = {}
        for identifier, widget in self.input_fields.items():
            values[identifier] = widget.get()
        return values
    
    ### handles saving the input values to the programs ini file ###
    def save_config(self):
        if not self.config.has_section('Settings'):
            self.config.add_section('Settings')
            
        for identifier, widget in self.input_fields.items():
            value = widget.get()
            self.config.set('Settings', identifier, value)

        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

###Create a tab with a scrollable frame and return the frame.###
def create_scrollable_tab(notebook, tab_name):
    tab = Frame(notebook)
    notebook.add(tab, text=tab_name)

    canvas = Canvas(tab)
    scrollbar = Scrollbar(tab, orient="vertical", command=canvas.yview)
    scrollable_frame = Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e, canvas=canvas: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    return scrollable_frame

### used for opening links to users browser ### used only once but eh, might need it again
def open_link(url):
    webbrowser.open_new(url)

### handles the browse button and saves the directory path to the config file ###
def browse_directory(label, config, config_file):
    directory = filedialog.askdirectory()
    if directory:
        label.config(text=directory)
        save_directory_path(directory, config, config_file)

### handles saving the directory path to the config file ###
def save_directory_path(directory, config, config_file):
    if 'Settings' not in config:
        config['Settings'] = {}
    config['Settings']['LastDirectory'] = directory
    with open(config_file, 'w') as configfile:
        config.write(configfile)

### handles loading the directory path from the config file ###
def load_directory_path(config, config_file):
    # Check if the INI file exists
    if not os.path.isfile(config_file):
        with open(config_file, 'w') as new_file:
            new_file.write('[Settings]\n')  # Create a new file with 'Settings' section
        return ''  # Return an empty string as no directory path is set yet

    config.read(config_file)

    # Check if 'Settings' section exists
    if 'Settings' not in config:
        config['Settings'] = {}  # Create 'Settings' section if not present
        with open(config_file, 'w') as configfile:
            config.write(configfile)
        return ''

    return config['Settings'].get('LastDirectory', '')  # Return the directory path or an empty string



def populate_info_tab(frame):
    Label(frame, text="This program was created to help fill a small gap in Palword Dedicated Server configuration options.",anchor="center",justify="center",wraplength=890).pack()
    Label(frame, text="I understand that you can just go in and edit the settings yourself, but this might make it easier for people who are less tech savvy or don't want to deal with just plain text.",anchor="center",justify="center",wraplength=890).pack()
    Label(frame, text="The definitions for a lot of these settings are pulled one to one from tech.palworldgame.com. Link here:",anchor="center",justify="center",wraplength=890).pack()
    
    link2 = Label(frame, text="https://tech.palworldgame.com/dedicated-server-guide",anchor="center",justify="center",wraplength=890,font=("Helvetica", 12),fg="blue",cursor="hand2")
    link2.pack()
    link2.bind("<Button-1>", lambda e: open_link('https://tech.palworldgame.com/dedicated-server-guide'))
    Label(frame, text="Pocketpair. (n.d.). Introduction. Palworld Tech Guide. https://tech.palworldgame.com/dedicated-server-guide",anchor="center",justify="left",wraplength=890,font=("Helvetica", 7)).pack()

    ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=5)
    Label(frame, text="Before you can get into editing the server settings, please make sure you have launched your world at least once.\nThis will ensure that all necessary files are in place.",anchor="center",justify="center",wraplength=890).pack()
    Label(frame, text="To download and run the dedicated server, follow the instructions from the tech.palworldgame.com link under the Windows Steam section:",anchor="center",justify="center",wraplength=890).pack()

    
    ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=5)
    Label(frame, text="From here, please browse and choose your palserver directory under the steamlibrary folder/steamapps/common/palserver. You will only need to choose this once.\n\n",anchor="center",justify="center",wraplength=890).pack()
        # Directory path label
    directory_label = Label(frame, text="Please choose your palserver directory", anchor="w")
    directory_label.pack()

    # Browse button
    browse_button = Button(frame, text="Browse", command=lambda: browse_directory(directory_label, config, config_file))
    browse_button.pack()

    # Load and display the saved directory path
    last_directory = load_directory_path(config, config_file)
    if last_directory:
        directory_label.config(text=last_directory)
    Label(frame, text="\n\n\nEverytime you click save, a backup of the server settings will be created and saved to a backup folder located in the same directory as this program",anchor="center",justify="center",wraplength=890).pack()


### I know that some fields start with a 'b' in the config file, but, to make it easier on the user, 
### I just removed the 'b' from the field names on the description and keep the b for the config file when the write happens.
### This makes life easier for the user to find things alphabetically...i think/hope
def populate_pal_settings(configurator):
    configurator.add_config_line("PalAutoHPRegeneRate: Pal auto HP regeneration rate.", "entry", "PalAutoHPRegeneRate", None, "1.000000")
    configurator.add_config_line("PalAutoHpRegeneRateInSleep: Pal sleep health regeneration rate (in Palbox).", "entry", "PalAutoHpRegeneRateInSleep", None, "1.000000")
    configurator.add_config_line("PalCaptureRate: Pal capture rate.", "entry", "PalCaptureRate", None, "1.000000")
    configurator.add_config_line("PalDamageRateAttack: Damage from pals multipiler.", "entry", "PalDamageRateAttack", None, "1.000000")
    configurator.add_config_line("PalDamageRateDefense: Damage to pals multipiler.", "entry", "PalDamageRateDefense", None, "1.000000")
    configurator.add_config_line("PalEggDefaultHatchingTime: Time(h) to incubate massive egg. Default 72", "entry", "PalEggDefaultHatchingTime", None, "72.000000")
    configurator.add_config_line("PalSpawnNumRate: Pal appearance rate.", "entry", "PalSpawnNumRate", None, "1.500000")
    configurator.add_config_line("PalStaminaDecreaceRate: Pal stamina reduction rate.", "entry", "PalStaminaDecreaceRate", None, "1.000000")
    configurator.add_config_line("PalStomachDecreaceRate: Pal hunger depletion rate.", "entry", "PalStomachDecreaceRate", None, "1.000000")


def populate_player_settings(configurator):
    configurator.add_config_line("ExpRate: Modifies how much experience you get.", "entry", "ExpRate", None, "1.000000")
    configurator.add_config_line("PlayerAutoHPRegeneRate: Player auto HP regeneration rate.", "entry", "PlayerAutoHPRegeneRate", None, "1.000000")
    configurator.add_config_line("PlayerAutoHpRegeneRateInSleep: Player sleep HP regeneration rate.", "entry", "PlayerAutoHpRegeneRateInSleep", None, "1.000000")
    configurator.add_config_line("PlayerDamageRateAttack: Damage from player multipiler.", "entry", "PlayerDamageRateAttack", None, "1.000000")
    configurator.add_config_line("PlayerDamageRateDefense: Damage to player multipiler.", "entry", "PlayerDamageRateDefense", None, "1.000000")
    configurator.add_config_line("PlayerStaminaDecreaceRate: Player stamina reduction rate.", "entry", "PlayerStaminaDecreaceRate", None, "1.000000")
    configurator.add_config_line("PlayerStomachDecreaceRate: Player hunger depletion rate.", "entry", "PlayerStomachDecreaceRate", None, "1.000000")
    configurator.add_config_line("WorkSpeedRate: I think this is player work speed. If not it's global work speed", "entry", "WorkSpeedRate", None, "1.000000")
    configurator.add_config_line("EnableFriendlyFire: Friendly fire between guild members i think. default is False", "combo", "bEnableFriendlyFire", ["True", "False"], "False")
    configurator.add_config_line("EnablePlayerToPlayerDamage: enables pvp, default is False", "combo", "bEnablePlayerToPlayerDamage", ["True", "False"], "False")
    configurator.add_config_line("DeathPenalty: This decides what items are dropped when you die.\n\t-None: Nothing dropped\n\t-item: drop items in inventory only\n\t-ItemAndEquipment: drop items and equipment but notpals in inventory\n\t-All (default): drop everything including pals", "combo", "DeathPenalty", ["None","Item", "ItemAndEquipment", "All"], "All")

def populate_other_settings(configurator):
    configurator.add_config_line("ActiveUNKO: No idea. Default is False", "combo", "bActiveUNKO", ["True", "False"], "False")
    configurator.add_config_line("Aim Assist for Keyboard: Enable Aim assist for keyboard. Default is False", "combo", "bEnableAimAssistKeyboard", ["True", "False"], "False")
    configurator.add_config_line("Aim Assist for Controllers: Enables aim assist for controllers. Default is True", "combo", "bEnableAimAssistPad", ["True", "False"], "True")
    configurator.add_config_line("AutoResetGuildNoOnlinePlayers: I THINK this is if no players are on for x amount of hours it removes the guild", "combo", "bAutoResetGuildNoOnlinePlayers", ["True", "False"], "False")
    configurator.add_config_line("AutoResetGuildTimeNoOnlinePlayers: I think, if previous setting is True, this is how long the server will wait to wipe a guild", "entry", "AutoResetGuildTimeNoOnlinePlayers", None, "72.000000")
    configurator.add_config_line("BaseCampMaxNum: No idea but the default is 128", "entry", "BaseCampMaxNum", None, "128")
    configurator.add_config_line("BaseCampWorkerMaxNum: Max Number of pals you can have at one base camp. default is 15", "entry", "BaseCampWorkerMaxNum", None, "15")
    configurator.add_config_line("BuildObjectDamageRate: Structure determination rate", "entry", "BuildObjectDamageRate", None, "1.000000")
    configurator.add_config_line("BuildObjectDeteriorationDamageRate: Structure determination rate", "entry", "BuildObjectDeteriorationDamageRate", None, "1.000000")
    configurator.add_config_line("CanPickupOtherGuildDeathPenaltyDrop: Whether guild members can pickup death penalty of non guild members", "combo", "bCanPickupOtherGuildDeathPenaltyDrop", ["True", "False"], "False")
    configurator.add_config_line("CollectionDropRate: Gatherable items multiplier", "entry", "CollectionDropRate", None, "1.000000")
    configurator.add_config_line("CollectionObjectHpRate: Gatherable objects HP multiplier", "entry", "CollectionObjectHpRate", None, "1.000000")
    configurator.add_config_line("CollectionObjectRespawnSpeedRate: Gatherable objects respawn interval", "entry", "CollectionObjectRespawnSpeedRate", None, "1.000000")
    configurator.add_config_line("CoopPlayerMaxNum: No idea, default is 31","entry","CoopPlayerMaxNum",None,"31")
    configurator.add_config_line("DayTimeSpeedRate: Day time speed", "entry", "DayTimeSpeedRate", None, "1.000000")
    configurator.add_config_line("Difficulty: This currently (as of 2021-11-06) does not do anything", "combo", "Difficulty", ["None"], "None")
    configurator.add_config_line("DropItemAliveMaxHours: I think it's how long items will stay on the ground in hours. default is 1.000000", "entry", "DropItemAliveMaxHours", None, "1.000000")
    configurator.add_config_line("DropItemMaxNum: I think this is max amount of items droppable. Default is 3000", "entry", "DropItemMaxNum", None, "3000")
    configurator.add_config_line("DropItemMaxNum_UNKO: No idea but the default is 100", "entry", "DropItemMaxNum_UNKO", None, "100")
    configurator.add_config_line("EnableDefense Other Guild Player: No idea, default is False", "combo", "bEnableDefenseOtherGuildPlayer", ["True", "False"], "False")
    configurator.add_config_line("EnableFastTravel: Whether fast travel can be used", "combo", "bEnableFastTravel", ["True", "False"], "True")
    configurator.add_config_line("EnableFriendlyFire: Friendly fire between guild members I think. default is False", "combo", "bEnableFriendlyFire", ["True", "False"], "False")
    configurator.add_config_line("EnableInvaderEnemy: Toggle of if invader events happen. Default is True", "combo", "bEnableInvaderEnemy", ["True", "False"], "True")
    configurator.add_config_line("EnableNonLoginPenalty: No idea, default is True", "combo", "bEnableNonLoginPenalty", ["True", "False"], "True")
    configurator.add_config_line("EnemyDropItemRate: Dropped Items Multiplier", "entry", "EnemyDropItemRate", None, "1.000000")
    configurator.add_config_line("ExistPlayer After Logout: No idea, default is False", "combo", "bExistPlayerAfterLogout", ["True", "False"], "False")
    configurator.add_config_line("GuildPlayerMaxNum: Max player of Guild (currently 20 max)", "combo", "GuildPlayerMaxNum", ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20"], "20")
    configurator.add_config_line("IsMultiplay: I think this is if the server is multiplayer or singleplayer, default is False", "combo", "bIsMultiplay", ["True", "False"], "False")
    configurator.add_config_line("IsPvP: No idea, default is False", "combo", "bIsPvP", ["True", "False"], "False")
    configurator.add_config_line("IsStartLocationSelect By Map: No idea, default is True", "combo", "bIsStartLocationSelectByMap", ["True", "False"], "True")
    configurator.add_config_line("NightTimeSpeedRate: Night time speed", "entry", "NightTimeSpeedRate", None, "1.000000")

def populate_server_settings(configurator):
    configurator.add_config_line("AdminPassword: Admin password to run basic commands. Can be left empty", "text", "AdminPassword", None, "")
    configurator.add_config_line("BanListURL: list of steam_id's of banned players. Default is\nhttps://api.palworldgame.com/api/banlist.txt.", "text", "BanListURL", None, "https://api.palworldgame.com/api/banlist.txt")
    configurator.add_config_line("PublicIP: Public IP. Can be left empty. I leave mine empty and just give my friends my IP.\nYou can make this your public IP.", "ip", "PublicIP", None, "127.0.0.1")
    configurator.add_config_line("PublicPort: Port for Server, default is 8211", "entry", "PublicPort", None, "8211")
    configurator.add_config_line("RCONEnabled: Enable RCON Default is False.\nRCON is the ability to remotely execute commands to the server.", "combo", "RCONEnabled", ["True", "False"], "False")
    configurator.add_config_line("RCONPort: Port number for RCON. Default is 25575", "entry", "RCONPort", None, "25575")
    configurator.add_config_line("Region: i'm not sure what this is default is blank", "text", "Region", None, "")
    configurator.add_config_line("ServerDescription: Server Description. Can be left empty", "text", "ServerDescription", None, "")
    configurator.add_config_line("ServerName: Server name. Can be left empty", "text", "ServerName", None, "Default Palword Server")
    configurator.add_config_line("ServerPassword: Server Password. Can be left empty", "text", "ServerPassword", None, "")
    configurator.add_config_line("ServerPlayerMaxNum: Maximum number of people who can join the server default is 32", "combo", "ServerPlayerMaxNum", ["0","1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21","22","23","24","25","26","27","28","29","30","31","32"], "32")
    configurator.add_config_line("UseAuth: Also don't know what this is. Default is True.", "combo", "bUseAuth", ["True", "False"], "True")




def main():
    main_window = Tk()
    main_window.title("Palword Server Settings Editor")
    main_window.geometry("900x800")

    tabBook = ttk.Notebook(main_window)
    tabBook.pack(pady=15)

    frame1 = create_scrollable_tab(tabBook, "Intro Info")
    frame2 = create_scrollable_tab(tabBook, "Pal Settings")
    frame3 = create_scrollable_tab(tabBook, "Player Settings")
    frame4 = create_scrollable_tab(tabBook, "Other Settings")
    frame5 = create_scrollable_tab(tabBook, "Server Settings")

    # try to load config from file
    config_palsettings = Configurator_Manager(frame2)
    config_playersettings = Configurator_Manager(frame3)
    config_othersettings = Configurator_Manager(frame4)
    config_serversettings = Configurator_Manager(frame5)

    populate_info_tab(frame1)
    populate_pal_settings(config_palsettings)
    populate_player_settings(config_playersettings)
    populate_server_settings(config_serversettings)
    populate_other_settings(config_othersettings)

    tabBook.pack(expand=True, fill='both')

    # Create a frame for the buttons
    button_frame = Frame(main_window)
    button_frame.pack(side="bottom", fill="x", padx=5, pady=5)

    close_button = Button(button_frame, text="Close", command=lambda: on_close(main_window, config_palsettings, config_playersettings, config_othersettings, config_serversettings))
    save_button = Button(button_frame, text="Save", command=lambda: on_save(config_palsettings, config_playersettings, config_othersettings, config_serversettings))

    close_button.pack(side="right", padx=2, pady=2)
    save_button.pack(side="right", padx=2, pady=2)

    main_window.mainloop()

# Execute the main function only if the script is run directly
if __name__ == "__main__":
    config_file = 'settings.ini'
    config = configparser.ConfigParser()
    config.read(config_file)
    input_fields = {}  # Dictionary to store input fields
    main()