from __future__ import unicode_literals, division, absolute_import, print_function

__license__   = 'GPL v3'

try:
    from qt.core import (QVBoxLayout, Qt, QGroupBox, QCheckBox)
except:
    from PyQt5.Qt import (QVBoxLayout, Qt, QGroupBox, QCheckBox)

try:
    load_translations()
except NameError:
    pass # load_translations() added in calibre 1.9

from calibre.gui2.metadata.config import ConfigWidget as DefaultConfigWidget
from calibre.utils.config import JSONConfig

STORE_NAME = 'Options'
KEY_GET_CATEGORY_AS_TAGS          = 'getCategoryAsTags'
KEY_GET_FILTER_AS_TAGS            = 'getFilterAsTags'
KEY_GET_ARTISTS_AS_AUTHORS        = 'getArtistsAsAuthors'
KEY_GET_EDITORS_AS_AUTHORS        = 'getEditorsAsAuthors'
KEY_GET_CONTRIBUTORS_AS_AUTHORS   = 'getContributorsAsAuthors'

DEFAULT_STORE_VALUES = {
    KEY_GET_CATEGORY_AS_TAGS: True,
    KEY_GET_FILTER_AS_TAGS: True,
    KEY_GET_ARTISTS_AS_AUTHORS: False,
    KEY_GET_EDITORS_AS_AUTHORS: False,
    KEY_GET_CONTRIBUTORS_AS_AUTHORS: False,
}

# This is where all preferences for this plugin will be stored
plugin_prefs = JSONConfig('plugins/WarGameVault')

# Set defaults
plugin_prefs.defaults[STORE_NAME] = DEFAULT_STORE_VALUES

def get_option(option_name):
    return plugin_prefs[STORE_NAME].get(option_name, DEFAULT_STORE_VALUES[option_name])

class ConfigWidget(DefaultConfigWidget):

    def __init__(self, plugin):
        DefaultConfigWidget.__init__(self, plugin)
        c = plugin_prefs[STORE_NAME]

        other_group_box = QGroupBox(_('Other options'), self)
        self.l.addWidget(other_group_box, self.l.rowCount(), 0, 1, 2)
        other_group_box_layout = QVBoxLayout()
        other_group_box.setLayout(other_group_box_layout)

        self.get_category_as_tags_checkbox = QCheckBox(_('Include \'Categories\' in the Tags column'), self)
        self.get_category_as_tags_checkbox.setToolTip(_('When checked, if a book has any categories defined they will be\n'
                                                   'returned in the Tags column from this plugin.'))
        self.get_category_as_tags_checkbox.setChecked(get_option(KEY_GET_CATEGORY_AS_TAGS))
        other_group_box_layout.addWidget(self.get_category_as_tags_checkbox)

        self.get_filter_as_tags_checkbox = QCheckBox(_('Include \'Filters\' in the Tags column'), self)
        self.get_filter_as_tags_checkbox.setToolTip(_('When checked, if a book has any Filters defined it will be\n'
                                                         'returned in the Tags column from this plugin.'))
        self.get_filter_as_tags_checkbox.setChecked(get_option(KEY_GET_FILTER_AS_TAGS))
        other_group_box_layout.addWidget(self.get_filter_as_tags_checkbox)

        self.get_artists_as_authors_checkbox = QCheckBox(_('Include \'Artists\' in the Author(s) field'), self)
        self.get_artists_as_authors_checkbox.setToolTip(_('When checked, if a book has any Artists defined\n'
                                                         'they will be added to the Author(s) field.'))
        self.get_artists_as_authors_checkbox.setChecked(get_option(KEY_GET_ARTISTS_AS_AUTHORS))
        other_group_box_layout.addWidget(self.get_artists_as_authors_checkbox)

        self.get_editors_as_authors_checkbox = QCheckBox(_('Include \'Editors\' in the Author(s) field'), self)
        self.get_editors_as_authors_checkbox.setToolTip(_('When checked, if a book has any Editors defined\n'
                                                         'they will be added to the Author(s) field.'))
        self.get_editors_as_authors_checkbox.setChecked(get_option(KEY_GET_EDITORS_AS_AUTHORS))
        other_group_box_layout.addWidget(self.get_editors_as_authors_checkbox)

        self.get_contributors_as_authors_checkbox = QCheckBox(_('Include \'Contributors\' in the Author(s) field'), self)
        self.get_contributors_as_authors_checkbox.setToolTip(_('When checked, if a book has any Contributors defined\n'
                                                         'they will be added to the Author(s) field.'))
        self.get_contributors_as_authors_checkbox.setChecked(get_option(KEY_GET_CONTRIBUTORS_AS_AUTHORS))
        other_group_box_layout.addWidget(self.get_contributors_as_authors_checkbox)

        other_group_box_layout.addStretch(1)

    def commit(self):
        DefaultConfigWidget.commit(self)

        new_prefs = {}
        new_prefs[KEY_GET_CATEGORY_AS_TAGS] = self.get_category_as_tags_checkbox.checkState() == Qt.Checked
        new_prefs[KEY_GET_FILTER_AS_TAGS] = self.get_filter_as_tags_checkbox.checkState() == Qt.Checked
        new_prefs[KEY_GET_ARTISTS_AS_AUTHORS] = self.get_artists_as_authors_checkbox.checkState() == Qt.Checked
        new_prefs[KEY_GET_EDITORS_AS_AUTHORS] = self.get_editors_as_authors_checkbox.checkState() == Qt.Checked
        new_prefs[KEY_GET_CONTRIBUTORS_AS_AUTHORS] = self.get_contributors_as_authors_checkbox.checkState() == Qt.Checked

        plugin_prefs[STORE_NAME] = new_prefs
