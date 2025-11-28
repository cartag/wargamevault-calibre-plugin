# WarGameVault Plugin

## Overview

This plugin allows retrieving book metadata from [www.wargamevault.com](https://www.wargamevault.com/). If you've purchased PDFs from WarGameVault, there's really no better source for metadata.

For increased speed while populating your TTRPG book metadata into Calibre, I recommend temporarily disabling all other Metadata sources; since you know you want WarGameVault data, there's no point in also searching Amazon, Goodreads, Google, OpenLibrary, etc.

WarGameVault search isn't great. I find it's often easier to just tell the plugin which exact item it is. You do this by adding adding "wargamevault:[id#]" into the "Ids" field in the Calibre item metadata. For example, for https://www.drivethrurpg.com/en/product/345698/stargrave-science-fiction-wargames-in-the-ravaged-galaxy you would put "wargamevault:345698" into the Ids field (without the quotes, of course). You get the Id from the product URL.

If you don't want to manually enter Ids and prefer to try your luck with search, I *highly* recommend enabling the Calibre option "Keep more than one entry per source" in the "Configure Metadata download" window. Otherwise it will only show you the first search result from WarGameVault, which will *often* be wrong.

## Main Features

- Can retrieve Title, Author(s), ISBN, Comments, Publisher, Publication Date, and Cover
- Configure whether to add WarGameVault item categories and filters into the book Tags
- Configure whether to add Artists, Editors and/or Contributors into the book Author(s)
- Retrieves a WarGameVault id, which can be used to directly jump to the web page for a specific book (from the book details pane)

## Development / Contributions

This plugin started out life as a copy of the FictionDB plugin (https://github.com/kiwidude68/calibre_plugins), was mangled into pulling data from the DriveThruRPG API by a Python n00b (https://github.com/quickwick/drivethrurpg-calibre-plugin), and then shamelessly ripped off to pull from WarGameVault by a nerd.
