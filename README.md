## Update:
The code owner (Path of Matth) has decided to release the source code at this point. We are happy to do this so that everyone can feel better about using the tool, and welcome kind contributions. This is a scruffy code. We want to thank @macr0s for starting the project, even though more than half of it has changed. A history of the code up to this point is in the branch `archive` for those interested.

#Roadmap and Plans:

This has come a long way if just under a week. I really have a new understanding of the experience GGG goes through with PoE players. A big thank you to all those who have helped users having troubles! 

The code is scuffed, and not professionally written in anyway. I am learning a ton, and help is welcome!

To everyone still having issues, please bear with us as we step through the following fixes and changes, in no particular order:

- [ ] Instructions for contributors

- [ ] Easier method of pointing the app to the players filter folder. Right now this is confusing, and making it interactive with a file dialog should make this better.

- [ ] Simplify the user settings inpute and defaults, including league, acct name, poesessid, etc.

- [ ] Proper logging and debugging

- [x] Support non-ASCII characters in account names

- [ ] Alert player that they should manually refresh the filter in the game's UI options tab

- [ ] Add a Highlight button to the overlay in addition to the app

- [ ] Fix some instances of `fatal error`

- [ ] False positive security alerts from anti-virus apps

- [ ] Identify why filter will not start hiding items after they have reached threshold in some instances

- [ ] Overlay will highlight magic items in addition to rare items

- [ ] Overlay will highlight one handed weapons which do not meet the 1x3 size criteria

- [ ] Distribute with the latest Neversink filters, including a fix the the 'Pernarch' missing base type issue.

- [ ] Help users to provide their own filters, in addition to ones from Path of Matth and Neversink/filterblade

- [ ] Better way of the app finding and updating its filter entries based on its counts

- [ ] Fix bug where alternate artwork items in stash tabs will short circuit the tool in certain cases

- [ ] Overlay will randomly jump in response to clicking on it

- [ ] Stash search improvement

- [ ] Option to fix the position of the overlay after placing it

- [ ] Detecting the screen and resolution of the PoE window so that users can run the overlay on a non-primary monitor

- [ ] Allow for higher iLvl items to be shown and highlighted as long as it is possible to include at least one iLvl<75 item

- [ ] Toggle Regal orb recipe

- [ ] Support for multiple tabs

- [ ] Support different thresholds for different item classes



# Read Me

Important: If you are not been using v2.0.3, please download that release [here](https://github.com/notablackbear/poe_qolV2/releases/tag/V2.0.3) and consider *deleting the POEQOL_Base.filter* from your filter folder to reset everything. If you've made some customizations to that filter prior to 2.0.3, perhaps temporarily move any existing filter named `POEQOL_Base.filter` to another location, or make sure you have a back-up copy of your customizations.

Steps/Notes/Advice/Info
1) You can clone the repo as is, or download the zip file from the releases, [here](https://github.com/notablackbear/poe_qolV2/releases/tag/V2.0.3) and unzip that folder.
2) All files should be located in the same folder as the exe file. The location of the POE_QOL folder shouldn't matter, but, for example, I keep it in `Documents`.
3) Open up the Config.ini file in text editor and *please read the instructions in that file*. There is info you need to fill out or else it won't work. Most importantly your poe account name and your POESESSID.
4) It assumes the OS is Windows 10. ~~Leave the Setup entry `filter` as is to let the app create a new filter, and it will by default try to save it in the folder `USER\Documents\My Games\Path of Exile\`. _If the app cannot find it,~~ Temporarily until it can be fixed, use the absolut path or leave the filter parameter blank and follow the pop-ups for help and manually select the folder. You should only need to do this once, since it will store the location you choose in the setup file._
5) The app recreates the included default on start up, if it is not detected in your filters folder, and saves it to your filters folder. Each time you refresh or highlight chaos recipe items, it will update this filter file. So you will then need to refresh the filters in game to see changes.
6) It's not instant. Unfortunately there's going to be some lag between the online stash and the app synchronization/refresh. It won't keep up with how quickly you are making exalts. It seems that you can force the stash to update by changing locations in game (going somewhere that requires a loading screen, like a waypoint)
7) It should work with any screen resolution, but have seen some issues crop up. If you are running two monitors, it is going to show up on Screen 0, so _run PoE in Windowed Fullscreen on your primary monitor._
8) There's been issues when using Vulkan for some players. Please try without Vulkan as well.


----

Updates
-----

* v2.0.3 You can now move the overlay by click and dragging the vertical side-bar on the left.

* The picture are actually loading into the app, so that is nice. Also the search is quicker, but you need to have your stash open.

* If the path to your filter folder is not "USER\Documents\My Games\Path of Exile" you can enter the full folder path, starting from the "C:\" drive root. If the app cannot find the folder, it will give you a message, click 'Ok' and then find the _folder_ where your filters are. *You may want to remove any that were already put there by any version before 2.0.3.*

* If your account has special characters, go ahead and use them! Report if there are still troubles. This should be fixed in 2.0.3 ~~If your account name contains non-ASCII characters, you must URL encode it first here: https://www.urlencoder.org/ Example: username Đãřķ becomes %C4%90%C3%A3%C5%99%C4%B7 after URL encoding and that can be used in the Config.ini~~ 

* You can turn on a rudimentary debuggin log in the `Settings.ini` file by setting the `debug` value to `True`

* By default, only *unidentified* rare items item level ~~64~~60 and 75 will be highlighted. This can be changed in the `chaos_items_filter.filter` file.

* There are two numbers in the overlay for each item class: #1/#2 where #1 is the number of unidentified items of that class were found in the stash tab, and #2 is how many identified items were found in the stash tab (within the item level range mentioned above).

* You will need to click the 'Chaos Recipe' button to cycle through highlights for each complete set. The number of sets highlighted can be customized by the `highlight_max_num_sets` parameter in the `Config.ini` file.

* Please try the latest files if you are having issues after successfully being able to launch the app the first time.

* There is no need to copy anything into your "Documents\My Games\Path of Exile\", since this is done for you the first time. If you need to reset the filter for any reason, you can remove the filter that was added to your "Documents\My Games\Path of Exile\" folder. Don't delete the filters that come with the executable.

* Color scheme should be colorblind friendly!

* If you'd like to use this too in ssf, you can try to change the league to "ssf standard" (no quotation marks for now)
