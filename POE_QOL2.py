#!/usr/bin/env python3

import tkinter as tk
import tkinter.messagebox as Msg
from tkinter import filedialog
import pygubu
import pyautogui
from math import floor
import requests
import json
import configparser
from pygubu.builder import ttkstdwidgets
import os
import time
from math import ceil
from tkinter import font
import datetime
import pyperclip
import copy
import sys
import pprint
import time
import threading


# 0xdavidel - I hate hardcoded strings, using constants is the better way to make your code maintanable
CHAOS_RECIPE_SECTION_NAME = "Chaos recipe"
DEBUG_LOG_PATH = "poeqol2_logfile.txt"
CONFIG_PATH = "Config.ini"
GUI_FILE_PATH = r"ui/Gui_Button_V2.ui"
MAIN_GUI_FRAME_NAME = "Frame_1"
RESOURCES_FOLDER = "resources"
SYNC_TRY_RATE = 10
MSG_BOX_TITLE = "POE QoL"
RUNNING = True


def debug_app(debug_bool):
    sys.stdout = open(DEBUG_LOG_PATH, "w")
    pp = pprint.PrettyPrinter(indent=4)
    return pp


def highlight_click_handler(a, b, c):
    """
    Used for when the user clicks on the highlight. Destroys the highlight and passes through the click action.
    Wish I knew how to make it 'click-through able'
    """
    a.destroy()
    # exec(f"app.{a}.destroy()")  #legacy -notaspy 14-9-2020
    x, y = pyautogui.position()
    pyautogui.click(x=x, y=y)


class MyApplication(pygubu.TkApplication):
    def load_config(self, config_path=CONFIG_PATH):
        """
        Wrapper to read the config and store it in self.config
        """
        self.config = configparser.ConfigParser()
        self.config.read(config_path)

        # TODO: add config format verification

    def debug_print(self, msg):
        """
        Wrapper for the Debug pretty printing
        """
        if self.DEBUG:
            self.pp.pprint(msg)
            sys.stdout.flush()

    def __init__(self, master=None):
        """
        This seems fine. -notaspy 14-9-2020
        Agree, Made it a little more readable -0xdavidel 26.09.2020
        """
        self.load_config()

        # Check if the value (case insensitive) is one of the following - True, Y, yes, Positive, Chaos
        self.DEBUG = self.config["Config"]["debug"].lower() in [
            "true",
            "y",
            "yes",
            "positive",
            "chaos",
        ]

        # Setup the debug pretty printer
        if self.DEBUG:
            self.pp = debug_app(debug_bool=self.DEBUG)

        self.debug_print("Setting up App")
        self.debug_print("Initializing App")

        super().__init__(master=master)

    def _create_ui(self):
        """
        Overriding the default function to build our own UI
        """
        self.debug_print("Creating UI")

        self.main_window_builder = pygubu.Builder()
        # Add the resource folder as a resource
        self.main_window_builder.add_resource_path(RESOURCES_FOLDER)
        # Load the UI file
        self.main_window_builder.add_from_file(GUI_FILE_PATH)
        # Get the correct GUI frame from the main file
        self.mainwindow = self.main_window_builder.get_object(
            MAIN_GUI_FRAME_NAME, self.master
        )
        # Setup the font
        self.font = font.Font(self.master, family="Times", size=20, weight="bold")
        # And connect the window to the current class
        # IMPORTANT - without this line most buttons wont work
        self.main_window_builder.connect_callbacks(self)

        # TODO: Use self.load_config before executing certain methods so it can be updated on the fly
        # TODO: Implement load_config config verification
        # TODO: Validate the chaos_items_filter.filter file contents and formatting and instruct user how to fix it if necessary
        # TODO: Restore the original main filter file on exit.
        self.setup_app()

    def sync_stashtab_records_thread(self):
        """
        This thread sleeps half a second, check if enough time elapsed and then syncs the inventory if deemed needed
        """
        elapsed = 0
        while True:
            if not self.sync_running:
                break
            time.sleep(0.5)
            elapsed += 0.5
            if elapsed >= SYNC_TRY_RATE:
                elapsed = 0
                if not self.check_inventory_sync():
                    self.sync_stash_tabs()

    def setup_app(self):
        """
        Chaos recipe app nitialization.
        This is a separate method from the GUI init so that we can reuse it while running.
        It *might* cause some undesired effects. TBD
        """
        self.debug_print("Setting Up App")

        # Note to developers, from trying a bunch of different resolutions and 3 monitors i found that,
        # stash/inv tabs had a fixed width to height ratio of 886/1440 (~0.6153)that must be obeyed.
        # -notaspy ~ 14-9-2020

        # TODO: Extract the screen resolution code into a function
        # Handeling the upper case "X" situation using .lower
        raw_screen_res = self.config["Overlay"]["screen_res"].lower()
        if "x" not in raw_screen_res:
            raise ValueError(
                'Screen Resolution was not given correctly. Please use the "WIDTH x HIGHT" format'
            )

        # Split it
        split_screen_res = raw_screen_res.split("x")
        if len(split_screen_res) != 2:
            raise ValueError(
                'Screen Resolution was not given correctly. Please use the "WIDTH x HIGHT" format'
            )

        # Convert to numbers
        try:
            self.screen_res = [int(number.strip()) for number in split_screen_res]
        except:
            raise ValueError(
                "Screen Resolution was not given correctly. WIDTH and HIGHT must be only numbers"
            )

        # notaspy findings - 14-9-2020:
        # Stash tab UI relation to the screen size -
        #   The leftmost edge of the UI is at 22/1440 of screen width
        #   The rightmost edge of the UI is 864/1440 of the screen width
        #   The top of the UI is at 215/1440 of screen width
        #   The botom of the UI is at 1057/1440
        # from those conculsions its possible to calculate the top-left corner of the UI and the botop-right corner of the UI
        # Those two points represent the area of the Stash tab UI
        horizontal_offset = int(self.config["Overlay"]["horizontal_offset"])
        vertical_offset = int(self.config["Overlay"]["vertical_offset"])

        self.tab_origin = (
            22 / 1440 * self.screen_res[1] + horizontal_offset,
            215 / 1440 * self.screen_res[1] - vertical_offset,
        )

        self.tab_end = (
            864 / 1440 * self.screen_res[1] + horizontal_offset,
            1057 / 1440 * self.screen_res[1] - vertical_offset,
        )

        # scale the size of a stash tab box depending on if it is quad or not.
        # TODO: currently set by user, but can actually get this from the site request
        if self.config["Stash"]["quad_tab"].lower() == "true":
            box_density_scalar = 24
        else:
            box_density_scalar = 12

        # Calculate the width and hight of each cell in the stash tab
        self.box_width = (self.tab_end[0] - self.tab_origin[0]) / (box_density_scalar)
        self.box_height = (self.tab_end[1] - self.tab_origin[1]) / (box_density_scalar)

        try:
            threshold = int(self.config["Overlay"]["threshold"])
        except:
            raise ValueError("Error parsing Threshold, it should be an intiger")

        # notaspy-
        # Store some meta-data about each item slot
        # Probably better to use another data-structure other than a list of dicts
        # scheme is [normalized width,
        # normalized height,
        # highlight color (can use any tk names color for now),
        # order user should add item to inventory to avoid inventory tetris fail situations,
        # threshold of how many items before dynamic filter editor starts to hide this item slot
        # ]

        # 0xdavidel-
        # This is legacy / code from notaspy, didn't want to change it
        # BUT the only details needed right now are the thresholds and the colors for each slot,
        # The box sizes are handled by the new BetterStashTabAPI I've created
        self.item_details = dict(
            Rings=[1, 1, "#33bbee", "4", threshold * 2],
            OneHandWeapons=[1, 3, "#bbbbbb", "1", threshold * 2],
            TwoHandWeapons=[2, 4, "#bbbbbb", "1", threshold],
            Shields=[2, 2, "#bbbbbb", "2", threshold * 2],
            BodyArmours=[2, 3, "#ee3377", "1", threshold],
            Helmets=[2, 2, "#cc3311", "2", threshold],
            Gloves=[2, 2, "#ee7733", "2", threshold],
            Boots=[2, 2, "#009988", "2", threshold],
            Belts=[2, 1, "#0077bb", "3", threshold],
            Amulets=[1, 1, "#33bbee", "4", threshold],
        )

        # Load the stash tab
        self.stash_tab = self.stash_finder()

        # The app has asynchronous knowledge of the items in tab, we have a local record in self.latest_stash
        # Use it when you want to access the stash data
        # ~~~IMPORTANT~~~~: The remote snapshot and the local record are two separate objects

        # Fast and easy way to create a new stash_tab object
        self.latest_stash = self.stash_finder()
        # Sync it with the previous stash object
        self.latest_stash.tab_items = self.stash_tab.tab_items[:]

        # Read the chaos_items_filter template
        self.read_default_chaos_filter_sections()
        # Check if target filter exists or make the user select it
        self.pre_process_item_filter()

        # Update the filter
        self.update_filter()

        # check if the local and remote inventories are synchronized. Uses the refresh rate (in seconds) set in the Config.ini file.
        # I don't know the actual refresh rate of the website; seems random.
        # Probably fine to assume that the local record is most accurate for 60s since it should take about that long to vendor everything.
        # Can't remember why I do this here, but it doesn't hurt anything (lol only one day later and I can't remember yikes)

        # 0xdavidel: No actual need but it really doesn't hurt anything, so instead of calling it once i created a thread to call it once every SYNC_TRY_RATE seconds
        # This should eliminate the out of sync problems, MIGHT cause race conditions when reading the stash tab data

        self.sync_running = True
        self.stash_sync_thread = threading.Thread(
            target=self.sync_stashtab_records_thread
        )
        # self.stash_sync_thread.daemon=True
        self.stash_sync_thread.start()

        # This is a record of all highlights
        self.highlighted_items = []
        self.debug_print("Done setting up App")

    def run(self):
        """Run the main loop. Self explanatory."""

        self.mainwindow.mainloop()

    def remove_highlights(self, update_local_record=True):
        """
        In case the user wants to manually remove the highlights on screen. By default it resets to local record to be synced with the remote snapshot.
        We assume the user did not click on items if they removed all the highlights.
        This is prone to errors if a user clicks on some, but not all of the highlights and then clicks this button.
        TODO: handle half-removed highlights in combination with this method.
        """
        if (
            self.highlighted_items
        ):  # test that highlight actually exist that need deletion
            for highlight in self.highlighted_items:  # delete them
                highlight.destroy()
            return True
        else:
            return False

    def chaos_recipe_idd(self):
        self.chaos_recipe(identified=True)

    def chaos_recipe_unidd(self):
        self.chaos_recipe(identified=False)

    def chaos_recipe(self, identified=False):
        """
        The meat of the program. Based on the number of complete sets, create top-level geometries that highlight areas of the screens for each item in the set.
        """
        # TODO: Make it so that the item is removed from local inventor ONLY if the user clicks on the highlight box. I am sure someone will click it without actually removing the item and it will not be recognize and user will complain.
        # This one is possibly fixed already by the sync thread - 0xdavidel 26.09.2020
        # TODO: HIGH Priority:  figure out why sometimes the same initial areas are highlighted. I may have fixed this by checking the inventory sync (and for left over highlights) first thing

        # if any previous highlights still exist, destroy them.
        # If we don't do this, the way it is written below, if user doesn't manually click each highlight, they become non-interactive.
        # So, just killing everything is the fast and dirty way I decided wipe the screen clear if needed.
        if self.check_inventory_sync():
            self.remove_highlights(update_local_record=False)
        else:
            self.remove_highlights(update_local_record=True)

        # get a dictionary of the LOCAL complete sets items.
        # this will be sync'd with the online stash if this is the first time this method has been called since last remote refresh
        # If user has clicked on a highlighted item, it gets removed locally, but the remote won't know that for a little.
        # Dict keys are the slot name and values are the normalized positions.
        # the positions are lists of length-2 lists:eg [[x0, y0], [x1, y1]]

        sets = self.get_complete_sets(identified=identified)

        # unident will be an empty dict if there's no complete sets left, and will inform user
        # TODO: This should work better
        if not sets:
            self.debug_print("Not enough Chaos Recipe Items")
            Msg.showinfo(title=MSG_BOX_TITLE, message="Not enough Chaos Recipe Items")
            return
        self.debug_print("Found {} sets for the chaos recipe".format(len(sets)))
        # if we have sets, go into the highlighting logic

        label_item_order = self.config["Overlay"]["label_item_order"].lower() in [
            "true",
            "y",
            "yes",
            "positive",
            "chaos",
        ]

        # loop through each item slot (key)
        for item_set in sets:
            self.debug_print("Current set to show : {}".format(item_set))
            # we will count from the top-left origin
            x_off = self.tab_origin[0]
            y_off = self.tab_origin[1]
            # cord_x, cord_y = self.unident[x].pop(0)  # Leaving this here so you can see the previous method was to pop items from the list. It was problematic. -notaspy 14-9-2020
            for item in item_set:
                # reimplemented this as a loop over the items that make up the number of complete sets
                # The execs are legacy. I don't like them, and could probably re-do it, but won't atm
                # TODO: refactor exec usage
                # get coordinates of entry
                cord_x, cord_y = item["x"], item["y"]
                cord_x = (
                    cord_x * self.box_width + x_off
                )  # convert coordinates to pixels
                cord_y = cord_y * self.box_height + y_off
                self.debug_print(("Screen Coordinates:", (cord_x, cord_y)))
                # create make appropriate size box
                box_width = self.box_width * item["w"]
                box_height = self.box_height * item["h"]

                self.debug_print(("Box dimensions (pixels):", (box_width, box_height)))

                # Create the highlights
                # TODO: Extract into a new function
                highlight = tk.Toplevel(self.mainwindow)
                highlight.attributes("-alpha", 0.65)
                if "color" in dir(item):
                    highlight.config(background=item.color)
                    if label_item_order:
                        label = tk.Label(highlight, text=item.priority)
                        label.config(background=item.color)
                        label.config(font=("", 15))
                        label.pack()
                else:
                    highlight.config(background="#FFFFFF")
                highlight.overrideredirect(1)
                highlight.attributes("-topmost", 1)
                highlight.geometry(
                    f"{ceil(box_width)}x{ceil(box_height)}+{ceil(cord_x)}+{ceil(cord_y)}"
                )
                highlight.bind(
                    "<Button-1>",
                    lambda command, a=highlight, b=cord_x, c=cord_y: highlight_click_handler(
                        a, b, c
                    ),
                )
                self.highlighted_items.append(highlight)

    def check_inventory_sync(self):
        """
        This is kinda useful. Checks if the local and remote stashes are the same OR if the user-give refresh interval has elapsed.
        Sets and returns a bool. I made this. -notaspy 14-9-2020
        And I changed it to work with the new BetterStashTabAPI -0xdavidel 25.09.2020
        """
        t_check = datetime.datetime.now()  # get current time

        # we need to have this here since it is reset by the next call to self.stash_finder()
        t_previous_check = self.last_update

        refresh_time = self.config["Stash"]["refresh_time"]
        refresh_time_datetime_format = datetime.timedelta(seconds=float(refresh_time))
        # compare local and remote stash inventories. short circuits if the refresh time has not elapsed
        new_stashtab = self.stash_finder()
        are_stashes_synced = new_stashtab.tab_items == self.stash_tab.tab_items
        if (
            t_check - t_previous_check
        ) < refresh_time_datetime_format and are_stashes_synced:
            self.synced = True
        else:
            self.synced = False

        self.debug_print(f"Synced?: {self.synced}")
        return self.synced

    def sync_stash_tabs(self):
        self.stash_tab = self.stash_finder()
        self.latest_stash.tab_items = self.stash_tab.tab_items[:]
        self.debug_print("Synced stashtab")

    def get_stash_tab_chaos_recipe_items(self):
        chaos_recipe_items = {}

        for item_type in self.item_details:
            unidentified = self.latest_stash.retrieve_all_by_tag(
                item_type.lower(),
                only_rares=True,
                exclude_identified=True,
                min_ilvl=60,
            )

            identified = self.latest_stash.retrieve_all_by_tag(
                item_type.lower(),
                only_rares=True,
                exclude_unidentified=True,
                min_ilvl=60,
            )

            chaos_recipe_items[item_type] = {
                "identified": identified,
                "unidentified": unidentified,
            }

        return chaos_recipe_items

    def get_complete_sets(self, identified=False):
        """
        Re implemented using BetterStashTabAPI - 0xdavidel 25.09.2020
        TODO: make shure there is always a ilvl 60 - 74 item included due to regal recipe
        """
        # If the local inventory and the last snapshot are not sync'd, update the remote snap shot and also make it the latest local stash inventory
        if not self.check_inventory_sync():
            self.sync_stash_tabs()

        chaos_recipe_items = self.get_stash_tab_chaos_recipe_items()

        identified_str = "identified" if identified else "unidentified"

        num_helmets = len(chaos_recipe_items["Helmets"][identified_str])
        num_body_armors = len(chaos_recipe_items["BodyArmours"][identified_str])
        num_boots = len(chaos_recipe_items["Boots"][identified_str])
        num_gloves = len(chaos_recipe_items["Gloves"][identified_str])
        num_amulets = len(chaos_recipe_items["Amulets"][identified_str])
        # Faster math floor, ints round down automaticly
        num_rings = int(len(chaos_recipe_items["Rings"][identified_str]) / 2)
        num_belts = len(chaos_recipe_items["Belts"][identified_str])
        num_weapons = int(len(chaos_recipe_items["OneHandWeapons"][identified_str]) / 2)
        num_weapons += int(len(chaos_recipe_items["Shields"][identified_str]) / 2)
        num_weapons += len(chaos_recipe_items["TwoHandWeapons"][identified_str])

        total_ready_sets = min(
            [
                num_helmets,
                num_body_armors,
                num_boots,
                num_gloves,
                num_amulets,
                num_rings,
                num_belts,
                num_weapons,
            ]
        )

        if total_ready_sets == 0:
            return False

        try:
            maximum_sets_to_show = int(self.config["Overlay"]["highlight_max_num_sets"])
        except:
            self.debug_print("Config error, highlight_max_num_sets is not a number")
            Msg.showinfo(
                title=MSG_BOX_TITLE,
                message="Config error, highlight_max_num_sets is not a number",
            )

        sets = []

        # Create the item sets
        for set_index in range(min(maximum_sets_to_show, total_ready_sets)):
            current_set = []
            current_set.append(chaos_recipe_items["Helmets"][identified_str].pop())
            current_set.append(chaos_recipe_items["BodyArmours"][identified_str].pop())
            current_set.append(chaos_recipe_items["Boots"][identified_str].pop())
            current_set.append(chaos_recipe_items["Gloves"][identified_str].pop())
            current_set.append(chaos_recipe_items["Amulets"][identified_str].pop())
            current_set.append(chaos_recipe_items["Belts"][identified_str].pop())
            current_set.append(chaos_recipe_items["Rings"][identified_str].pop())
            current_set.append(chaos_recipe_items["Rings"][identified_str].pop())

            # 2x 1h weapons
            if len(chaos_recipe_items["OneHandWeapons"][identified_str]) >= 2:
                current_set.append(
                    chaos_recipe_items["OneHandWeapons"][identified_str].pop()
                )
                current_set.append(
                    chaos_recipe_items["OneHandWeapons"][identified_str].pop()
                )

            # 1x 1h weapon + 1 shield
            elif (
                len(chaos_recipe_items["OneHandWeapons"][identified_str]) >= 1
                and len(chaos_recipe_items["Shields"][identified_str]) >= 1
            ):
                current_set.append(
                    chaos_recipe_items["OneHandWeapons"][identified_str].pop()
                )
                current_set.append(chaos_recipe_items["Shields"][identified_str].pop())

            # 2x shield
            elif len(chaos_recipe_items["Shields"]["unidentified"]) >= 2:
                current_set.append(chaos_recipe_items["Shields"][identified_str].pop())
                current_set.append(chaos_recipe_items["Shields"][identified_str].pop())

            # 1x 2h weapon
            elif len(chaos_recipe_items["TwoHandWeapons"][identified_str]) >= 1:
                current_set.append(
                    chaos_recipe_items["TwoHandWeapons"][identified_str].pop()
                )

            # if we reach this, it means we fucked up in the addition stage earlier
            else:
                raise RuntimeError("unintended elif branch reached")

            # delete the selected items from the local stash variable
            for item in current_set:
                self.latest_stash.remove_item(item)
                # Makeshift way to add colors to items, gonna remake this later
                for tag in item.tags:
                    for detail_key in self.item_details:
                        if tag.lower() == detail_key.lower():
                            item.color = self.item_details[detail_key][2]
                            item.priority = self.item_details[detail_key][3]

            sets.append(current_set)
        return sets

    def show_chaos(self):
        """
        This is all legacy. It creates and shows the overlay that has a running counter of items in each stash
        I did not make changes other than to comment out the error being raised if the monitor was not 1920x1080
        I honestly don't know what the buttons are even for, they never show up?
        It uses this bizzare and obscure pygubu library.
        It also relies on some html file that comes with this code (or ccs? idk some web language)
        """
        self.overlay_builder = pygubu.Builder()
        self.overlay_builder.add_from_file(GUI_FILE_PATH)
        self.overlay_GUI = tk.Toplevel(self.mainwindow)

        self.frame3 = self.overlay_builder.get_object("Frame_2", self.overlay_GUI)
        self.overlay_builder.connect_callbacks(self)
        self.overlay_GUI.overrideredirect(1)

        # I went ahead and put this at bottom center
        vertical_offset = int(
            self.config["Overlay"]["item_counter_overlay_vertical_offset"]
        )
        overlay_location = f"+{self.screen_res[0] // 2 - 130}+{floor(self.screen_res[1] * (1 - 80/1080)) - vertical_offset}"
        self.overlay_GUI.geometry(overlay_location)
        self.overlay_GUI._offsetx = 260
        self.overlay_GUI._offsety = 80

        # 0xdavidel - fixed overlay movement - 26.09.2020 (more like 25.09.2020 late night)
        # This handles the start of the movement
        def StartMove(event):
            self.overlay_GUI.x = event.x
            self.overlay_GUI.y = event.y

        # This handles the stp[] of the movement
        def StopMove(event):
            self.overlay_GUI.x = None
            self.overlay_GUI.y = None

        # This handles the actual movement
        def OnMotion(event):
            deltax = event.x - self.overlay_GUI.x
            deltay = event.y - self.overlay_GUI.y
            x = self.overlay_GUI.winfo_x() + deltax
            y = self.overlay_GUI.winfo_y() + deltay
            self.overlay_GUI.geometry("+%s+%s" % (x, y))

        # Append the functions into the overlay object
        self.overlay_GUI.StartMove = StartMove
        self.overlay_GUI.StopMove = StopMove
        self.overlay_GUI.OnMotion = OnMotion

        # Bind all to button 1 (TK thinks that Button-1 is the leftmost button no matter the button name)
        self.overlay_GUI.bind("<ButtonPress-1>", self.overlay_GUI.StartMove)
        self.overlay_GUI.bind("<ButtonRelease-1>", self.overlay_GUI.StopMove)
        self.overlay_GUI.bind("<B1-Motion>", self.overlay_GUI.OnMotion)
        self.debug_print(f"Overlay Location:{overlay_location}")

        # Make overlay stay on top
        self.overlay_GUI.attributes("-topmost", 1)

        # Populate the overlay values
        self.refresh_me()

    def close_overlay(self):
        # more legacy for overlay
        self.overlay_GUI.destroy()

    def refresh_me(self):
        # Refreshes the running count of unidentified and identified items in the stash tab.
        # 0xdavidel - 25.09.2020 - reworked with the BetterStashTabAPI
        if not self.check_inventory_sync():
            self.sync_stash_tabs()

        self.debug_print("Refreshing filter within refresh me.")

        chaos_recipe_items = self.get_stash_tab_chaos_recipe_items()

        # summarizing 2h- and 1h-weapons + shields as 1h-weapons
        for key in ["TwoHandWeapons", "Shields"]:
            chaos_recipe_items["OneHandWeapons"]["identified"] += chaos_recipe_items[
                key
            ]["identified"]
            chaos_recipe_items["OneHandWeapons"]["unidentified"] += chaos_recipe_items[
                key
            ]["identified"]
            del chaos_recipe_items[key]

        for key in chaos_recipe_items:
            identified_items = len(chaos_recipe_items[key]["identified"])
            unidentified_items = len(chaos_recipe_items[key]["unidentified"])
            if key == "OneHandWeapons":
                self.overlay_builder.get_object(key).configure(
                    text="{}:\n{} UID | {} ID".format(
                        "Weapons", unidentified_items, identified_items
                    )
                )
            else:
                self.overlay_builder.get_object(key).configure(
                    text="{}:\n{} UID | {} ID".format(
                        key, unidentified_items, identified_items
                    )
                )

        self.update_filter()

    def stash_finder(self):
        from utils.BetterStashTabAPI import get_stash_tab_content

        account_name = self.config["Account"]["account"]
        league = self.config["Account"]["league"]
        POESESSSID = self.config["Account"]["POESESSID"]
        tab_index = self.config["Stash"]["tab"]

        self.debug_print("Pulling stash tab from pathofexile.com")
        self.debug_print(
            "Account Name: {} | League: {} | Tab Index: {} | POESESSID (DO NOT SHARE THIS VALUE!): {}".format(
                account_name, league, tab_index, POESESSSID
            )
        )

        try:
            stash_tab = get_stash_tab_content(
                account_name, league, tab_index, POESESSSID
            )
        except Exception as e:
            self.pp.pprint("ERROR : {}".format(str(e)))
            Msg.showinfo(title=MSG_BOX_TITLE, message=str(e))
            # Lets not continue running
            sys.exit(1)

        self.debug_print("Stash tab retrieved")

        self.last_update = datetime.datetime.now()  # added by notaspy 14-9-2020
        return stash_tab

    # Re-Implemented using BetterFilterAPI - 0xdavid - 25.09.2020
    def read_default_chaos_filter_sections(self):
        from utils.BetterFilterAPI import load_rules_from_base_filter

        chaos_filter_path = self.config["Filter"]["chaos_items_filter"]

        try:
            self.chaos_filter_parsed = load_rules_from_base_filter(chaos_filter_path)
        except Exception as e:
            self.debug_print("Exception reading chaos filter: {}".format(str(e)))
            Msg.showinfo(
                "POE QoL error", "Exception reading chaos filter: {}".format(str(e))
            )
            sys.exit(1)

    def pre_process_item_filter(self):
        from utils.BetterFilterAPI import get_filter_path, get_filter_directory

        # Get the absolute filter path,
        main_filter_path = get_filter_path(self.config["Filter"]["filter"])

        filter_exists = os.path.isfile(main_filter_path)

        self.debug_print(
            "Filter path: {}, Filter exists: {}".format(main_filter_path, filter_exists)
        )

        if not filter_exists:
            self.debug_print("Asking the user to select the correct filter file")
            Msg.showinfo(
                "POE QoL error",
                "Could not find your selected filter, please select it from the dialog",
            )
            # Asking dialog
            main_filter_path = filedialog.askopenfilename(
                initialdir=get_filter_directory(),
                filetypes=(("loot filters", "*.filter"), ("all files", "*.*")),
                title="Select a filter file",
            )
            # Recheck
            filter_exists = os.path.isfile(main_filter_path)
            self.debug_print(
                "SELECTED Filter path: {}, Filter exists: {}".format(
                    main_filter_path, filter_exists
                )
            )

            # TODO: reimplement
            # we are now just going to update the setup file with what the user says to avoid errors in the future
            # config_file_updates = {'filter': {
            #     'path': self.main_filter_path, 'lino': None, 'field': 'filter='}}
            # with open('Config.ini', 'r', encoding='utf-8') as configfile_in:
            #     contents0 = configfile_in.readlines()
            #     for lino, l in enumerate(contents0):
            #         if l[0:7] == 'filter=':
            #             config_file_updates['filter']['lino'] = lino
            #         else:
            #             continue
            # with open('Config.ini', 'w', encoding='utf-8') as configfile_out:
            #     contents0[config_file_updates['filter']['lino']] = config_file_updates['filter']['field'] + \
            #         config_file_updates['filter']['path'] + \
            #         "\n"  # encode it at utf-8 for international players
            #     for l in contents0:
            #         configfile_out.write(l)

        # Testing if user selected a real file
        if not filter_exists:
            # TODO: Handle new filter file creation
            self.debug_print("User selected a non existant filter file")
            Msg.showinfo(
                "POE QoL error",
                "Could not find your selected filter, try again next time!",
            )
            sys.exit(1)

        self.main_filter_path = main_filter_path

    def update_filter(self):
        """
        Attempt to update the main filter with showing/hiding recipe item slots that have reached the threshold.
        It is inefficient, since it loops through a very large filter blade file, and re-writes text that should not change.
        I re-insert all the text from the chaos_items_filter just to be safe, but wouldn't need to if this is implemented in a better way.
        This will not hide any items set to be ignored in the Config.ini file.
        """
        self.debug_print("Updating Filter")

        if self.chaos_filter_parsed and self.main_filter_path:
            self.debug_print("Found necessary filter files.")
        else:
            self.debug_print("Something went very wrong while updating the filter")
            Msg.showinfo(
                "POE QoL error", "Something went very wrong while updating the filter"
            )
            sys.exit(1)
        ignore_threshold_list = self.config["Overlay"]["ignore_threshold"]
        # Copy of the full chaos filter, remove entries from here as we go through the different slots
        temp_chaos_filter = copy.copy(self.chaos_filter_parsed)
        # go through the item slots and their meta-data (which has the threshold for items set by user)
        for slot, details in self.item_details.items():
            try:
                slot_threshold = details[4]
                if slot in ignore_threshold_list:
                    self.debug_print(
                        "Slot {} is in the ignore threshold list, keeping it in the chaos filter".format(
                            slot
                        )
                    )
                    continue

                all_unidentified_in_slot = self.stash_tab.retrieve_all_by_tag(
                    slot, only_rares=True
                )

                # The amount of items of the current slot is larger or equal to the threshold, remove it from the filter
                if len(all_unidentified_in_slot) >= slot_threshold:
                    self.debug_print(
                        "Slot {} has more items ({}) than the threshold - {}".format(
                            slot, len(all_unidentified_in_slot), slot_threshold
                        )
                    )
                    temp_chaos_filter.pop(slot)

            except Exception as e:
                self.debug_print(
                    "Exception when changing chaos filter - {}".format(str(e))
                )
                Msg.showinfo(
                    title=MSG_BOX_TITLE,
                    message="Exception when changing chaos filter - {}".format(str(e)),
                )

        from utils.BetterFilterAPI import write_section_to_filter

        write_section_to_filter(
            self.main_filter_path, CHAOS_RECIPE_SECTION_NAME, temp_chaos_filter
        )

    def handle_on_close(self):
        # Kill the sync thread
        self.sync_running = False
        # self.stash_sync_thread.join()
        # Incert any other on_close operations you might want

    # Below are just methods that will search the stash tab for common things. didn't mess with these -notaspy 14-9-2020

    def search(self, text):
        """
        LEGACY CODE
        this handles the automated searching
        This might break the "one-action per button click" rule by GGG, but other tools do something similar so oh well - 0xdavidel 26.09.2020
        """
        pyperclip.copy(text)
        x, y = pyautogui.position()
        pyautogui.click(
            x=floor(self.tab_end[0] * 19 / 24), y=floor(self.tab_end[1] * 1183 / 1057)
        )
        pyautogui.moveTo(x=x, y=y)
        pyautogui.hotkey("ctrl", "f")
        pyautogui.hotkey("ctrl", "v")

    def currency(self):
        self.search('"Rarity: Currency"')

    def essence(self):
        self.search('"Essence of" "Rarity: Currency"')

    def divcard(self):
        self.search('"Rarity: Divination Card"')

    def fragment(self):
        self.search('"can be used in a personal Map device"')

    def splinter(self):
        self.search('"Splinter" "Splinters to create"')

    def delve(self):
        self.search('"Rarity: Currency" "Fossil"')

    def incubator(self):
        self.search('"The Incubated item drops"')

    def map(self):
        self.search('"Map" "personal Map Device"')

    def blight_map(self):
        self.search('"Blighted" "personal Map Device"')

    def veiled(self):
        self.search('"Veiled"')

    def rare(self):
        self.search('"Rarity: Rare"')

    def unique(self):
        self.search('"Rarity: Unique"')

    def prophecy(self):
        self.search('"add this prophecy"')

    def gem(self):
        self.search('"Rarity: Gem"')

    def unid(self):
        self.search('"Unidentified"')


if __name__ == "__main__":

    def on_close():
        # Signal the program that its time to close itself
        app.handle_on_close()
        # Ugly way to exit since the thread didnt want to cooperate properly
        sys.exit(1)

    # legacy. Run the applet.
    root = tk.Tk()
    # Bind an on_close function
    root.wm_protocol("WM_DELETE_WINDOW", on_close)
    root.title("Path of Exile - Quality of Life (POE-QOL)")
    app = MyApplication(root)
    app.run()
