from vanilla import HUDFloatingWindow, List, ImageListCell, CheckBoxListCell, GradientButton, Group, PopUpButtonListCell, CheckBox, SquareButton
from mojo.events import installTool, uninstallTool, getToolOrder, setToolOrder, setActiveEventTool, getActiveEventTool, addObserver, removeObserver, extractNSEvent
from mojo.UI import AllGlyphWindows, GetFile, PutFile, Message, AllGlyphWindows
from mojo.extensions import getExtensionDefault, setExtensionDefault
from copy import deepcopy
from plistlib import readPlist, writePlist
from AppKit import NSBeep, NSWindowMiniaturizeButton, NSWindowZoomButton, NSWindowCloseButton, NSImageNameActionTemplate, NSDragOperationMove
from CustomAppKit import VerticallyCenteredTextFieldCell
from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.roboFont import OpenWindow
from lib.eventTools.eventManager import EventManager
from pprint import pprint
# from lib.UI.toolbarGlyphTools import ToolbarGlyphTools

'''
    TODO:
    – [X] add custom shortcuts
    – [X] add tool palette functionality
    – [ ] add sorting functionality
'''
toolOrderDragType = "toolOrderDragType"
key = 'com.rafalbuchner.ToolManagerWindow'
settingskey = 'com.rafalbuchner.ToolManagerWindow.settings'
hotkeykey = 'com.rafalbuchner.ToolManagerWindow.hotkeys'
showOnLaunchKey = 'com.rafalbuchner.ToolManagerWindow.showOnLaunch'
modifierDict = {
'no-modifiers':None,
'control':'controlDown',
'option':'optionDown',
'command':'commandDown',
}
class ToolManagerWindow(BaseWindowController):
    modifiers = [
        "no-modifiers",
        "command",
        "option",
        "control"
    ]
    suffix = 'roboFontToolPalette'
    settingsWidth = 200
    rowHeight = 30
    minSize = (rowHeight+9,400)
    windowTitle = 'Tools'
    def __init__(self):
        self.isDropping=False
        self.isEditingHotkeys=False
        self.showOnLaunch = getExtensionDefault(showOnLaunchKey)
        if self.showOnLaunch is None: self.showOnLaunch = False
        self.tools = EventManager.getOrderedEvents()

        toolsDict = {tool.__class__.__name__:tool for tool in self.tools}
        self.toolNames = [tool.__class__.__name__ for tool in self.tools]

        self.toolDescription = {}
        self.toolIcons = {}
        for toolName in toolsDict:
            self.toolIcons[toolName] = toolsDict[toolName].getToolbarIcon()
            self.toolDescription[toolName] = True
        toolDescription = getExtensionDefault(key)
        settings = getExtensionDefault(settingskey)
        if settings is None: self.hideToolbar = False
        else: self.hideToolbar = settings.get('hideToolbar', False)
        if settings is None: self.openWithGlyphWindow = False
        else: self.openWithGlyphWindow = settings.get('openWithGlyphWindow', False)
        self.openWindow = self.openWithGlyphWindow

        self.hotkeys = getExtensionDefault(hotkeykey)
        if self.hotkeys is None: self.hotkeys = {}

        if toolDescription is not None: self.toolDescription = toolDescription

        self._updateTools()
        self.open()



    def initUI(self):
        self.prevSelection = [0]
        w, h = self.minSize
        self.w = HUDFloatingWindow((0, 0, w, h),self.windowTitle,minSize=self.minSize,autosaveName=key)
        self.w.getNSWindow().setHasShadow_(False)

        columnInfo = [
                dict(title='icon', cell=ImageListCell(), width=self.rowHeight+self.rowHeight/8),
                dict(title='tool', cell=VerticallyCenteredTextFieldCell('mini'), editable=False),
                dict(title='active', cell=CheckBoxListCell(), editable=True, width=17),
            ]

        self.w.palette = Group((0,0,-0,-0))
        self.w.palette.list = List((0,0,-0,-66),[], columnDescriptions=columnInfo, rowHeight=self.rowHeight, selectionCallback=self.selectionCallback,showColumnTitles=False, allowsEmptySelection=True, allowsMultipleSelection=False, drawHorizontalLines=True,drawFocusRing=True,editCallback=self.listChangedCallback)#,dragSettings=dict(type=toolOrderDragType, callback=self.dragCallback), selfDropSettings=dict(type=toolOrderDragType, operation=NSDragOperationMove, callback=self.dropListSelfCallback))
        self.selectionCallback(self.w.palette.list)
        self.w.palette.openSettings = GradientButton((5,-66+5,-5,-5),imageNamed=NSImageNameActionTemplate,sizeStyle='mini',callback=self.openSettingsCallback)
        self.w.settings = Group((-self.settingsWidth,0,self.settingsWidth,-0))
        columnInfo = [

                dict(title='hotkey', editable=True),
                dict(title='modifier',cell=PopUpButtonListCell(self.modifiers), binding="selectedValue")
            ]
        self.w.settings.list = List((5,0,-0,-66),[], columnDescriptions=columnInfo, rowHeight=self.rowHeight, showColumnTitles=False, allowsEmptySelection=True, allowsMultipleSelection=False, drawVerticalLines=True, drawFocusRing=True,editCallback=self.hotkeyEditCallback)
        self.w.settings.hideToolbar = CheckBox((5,-66+5,-5,15),'hide toolbar',sizeStyle='mini', callback=self.hideToolbarCallback,value=self.hideToolbar)
        # self.w.settings.sortDefaulr = SquareButton((self.settingsWidth/2+2.5,-66+5,-5,15),'sort default bar',sizeStyle='mini',callback=self.sortDefaultToolsCallback)
        self.w.settings.showOnLaunchChB = CheckBox((5,-44+5,-5,15),'show on launch',sizeStyle='mini', callback=self.showOnLaunchCallback,value=self.showOnLaunch)
        self.w.settings.exportBtn = SquareButton((5,-22+2,self.settingsWidth/2-5-2.5,15),'export prefs',sizeStyle='mini',callback=self.exportImportCallback)
        self.w.settings.importBtn = SquareButton((self.settingsWidth/2+2.5,-22+2,-5,15),'import prefs',sizeStyle='mini',callback=self.exportImportCallback)
        self.w.settings.show(False)
        self.hideToolbarCallback(self.w.settings.hideToolbar)
        self._rebuildToolPalette()
        self.w.palette.list.setSelection(self.prevSelection)
        self.w.bind('close', self.windowClose)
        self.w.bind('resize', self.windowResize)
        self.windowResize(self.w)
        self.w.open()

    def open(self):
        addObserver(self, 'customShortcutCallback', 'keyDown')
        addObserver(self, 'glyphWindowWillOpenCallback', 'glyphWindowWillOpen')
        addObserver(self, 'becomeActiveCallback','becomeActive')
        self.initUI()

    def removeObservers(self):
        removeObserver(self, 'keyDown')
        removeObserver(self, 'glyphWindowWillOpen')
        removeObserver(self, 'becomeActive')

    def showOnLaunchCallback(self, sender):
        if sender.get() == 1:
            self.showOnLaunch = True
        else:
            self.showOnLaunch = False
        setExtensionDefault(showOnLaunchKey, self.showOnLaunch)
    def sortDefaultToolsCallback(self, sender):
        items = self.w.palette.list.get()
        newOrder = [item['tool'] for item in items]
        setToolOrder(newOrder)
        self.w.settings.list.set(items)

    # def dropListSelfCallback(self, sender, dropInfo):
    #     isProposal = dropInfo["isProposal"]
    #     if not isProposal:
    #         indexes = [int(i) for i in sorted(dropInfo["data"])]
    #         indexes.sort()
    #         source = dropInfo["source"]
    #         rowIndex = dropInfo["rowIndex"]
            
    #         items = sender.get()
    #         toMove = [items[index] for index in indexes]
    #         for index in reversed(indexes):
    #             del items[index]
    #         rowIndex -= len([index for index in indexes if index < rowIndex])
    #         for font in toMove:
    #             items.insert(rowIndex, font)
    #             rowIndex += 1
    #         sender.set(items)
    #         self.isDropping = False
    #     return True

    # def dragCallback(self, sender, indexes):
    #     self.isDropping = True
    #     return indexes

    def hideToolbarCallback(self, sender):
        self.hideToolbarAction(sender.get())

    def glyphWindowWillOpenCallback(self, window):
        if self.hideToolbar:
            window['window'].window().getNSWindow().hideToolbar_(True)

    def selectionCallback(self, sender):
        items = sender.get()
        if len(sender.getSelection()) > 0:
            item = items[sender.getSelection()[0]]
            if item['active'] != 1:
                sender.setSelection(self.prevSelection)
            else:
                toolName = item['tool']
                if not self.isDropping:
                    setActiveEventTool(toolName)
                self.prevSelection = sender.getSelection()

    def windowResize(self, window):
        w = self.w.palette.getNSView().frameSize().width


        columsToHide = self.w.palette.list.getNSTableView().tableColumns()[1:]

        if w < self.rowHeight + 15:
            for column in columsToHide:
                column.setHidden_(True)

        else:
            for column in columsToHide:
                column.setHidden_(False)

        x,y,w,h = self.w.getPosSize()
        if w < self.rowHeight + 15:
            self.w.setTitle("")
        else:
            self.w.setTitle(self.windowTitle)

    def windowClose(self, info):
        setExtensionDefault(key, self.toolDescription)
        setExtensionDefault(hotkeykey, self.hotkeys)
        hideToolbar = False
        if self.w.settings.hideToolbar.get() == 1: hideToolbar = True
        openWithGlyphWindow = False
        setExtensionDefault(settingskey, dict(hideToolbar=hideToolbar,openWithGlyphWindow=openWithGlyphWindow))
        self.removeObservers()

    def hotkeyEditCallback(self, sender):
        items = sender.get()
        for item in items:
            self.hotkeys[item['tool']] = item.get('hotkey', "")

    def becomeActiveCallback(self, info):
        def _setToolInThePalette(tool):
            toolName = tool.__class__.__name__
            index = self.toolNames.index(toolName)
            self.w.palette.list.setSelection([index])

        tool = info['tool']
        _setToolInThePalette(tool)

    def exportImportCallback(self, sender):
        if 'export' in sender.getTitle():
            self._exportSettings()
        else:
            self._importSettings()

    def _exportSettings(self):
        path = PutFile()
        if path.split('.')[-1] != self.suffix:
            suffix = '.'+self.suffix
            path += suffix
        if self.hotkeys is None:
            hotkeys = {}
        data = dict(toolDescription=self.toolDescription,hotkeys=self.hotkeys)
        writePlist(data, path)

    def _importSettings(self):
        path = GetFile(message='Import Tool Palette', fileTypes=[self.suffix])
        if path:
            settings = readPlist(path)
            self.toolDescription = settings['toolDescription']
            self.hotkeys = settings['hotkeys']
            self._updateTools()
            self._rebuildToolPalette()

    def _rebuildToolPalette(self):
        items = []
        for toolName in self.toolNames:
            if toolName == 'EditingTool':
                if self.hotkeys is not None:
                    hotkey = self.hotkeys.get(toolName, "")
                else: hotkey = ""
                modifier = 'no-modifiers'
                if len(hotkey.split(" ")) > 1:
                    _modifier = hotkey.split(" ")[-1]
                    if _modifier in self.modifiers:
                        modifier = _modifier
                        hotkey = " ".join(hotkey.split(" ")[:-1])

                icon = self.toolIcons.get(toolName)
                if icon is not None:
                    items += [dict(hotkey=hotkey,active=True,icon=icon,tool=toolName,modifier=modifier)]

            else:
                active = self.toolDescription[toolName]

                if self.hotkeys is not None:
                    hotkey = self.hotkeys.get(toolName, "")
                else: hotkey = ""
                modifier = 'no-modifiers'
                if len(hotkey.split(" ")) > 1:
                    _modifier = hotkey.split(" ")[-1]
                    if _modifier in self.modifiers:
                        modifier = _modifier
                        hotkey = " ".join(hotkey.split(" ")[:-1])

                icon = self.toolIcons.get(toolName)
                if icon is not None:
                    items += [dict(hotkey=hotkey,active=active,icon=icon,tool=toolName,modifier=modifier)]

        self.w.palette.list.set(items)
        self.w.settings.list.set(items)

    def customShortcutCallback(self, info):
        event = extractNSEvent(info['event'])
        for toolName in self.hotkeys:
            hotkey = self.hotkeys[toolName]

            if len(hotkey.split(' ')) > 2:
                continue
            if len(hotkey.split(' ')) == 2:
                char, modifier = hotkey.split(' ')
                if event['keyDownWithoutModifiers'] == char and event[modifierDict[modifier]] != 0:
                    setActiveEventTool(toolName)
                    break
            else:
                char = hotkey.split(' ')[0]
                if event['keyDownWithoutModifiers'] == char:
                    setActiveEventTool(toolName)
                    break

    def openSettingsCallback(self, sender):
        # Open/close the hotkeys editor
        winX, winY, width, height = self.w.getPosSize()
        if not self.isEditingHotkeys:
            newWidth = width + self.settingsWidth
            w, h = self.minSize
            self.w.getNSWindow().setMinSize_((w+ self.settingsWidth, h))
            self.w.setPosSize((winX, winY, newWidth, height))
            self.w.palette.setPosSize((0,0,-self.settingsWidth,-0))
            self.w.settings.show(True)
            self.isEditingHotkeys=True
        else:

            newWidth = width - self.settingsWidth
            self.w.settings.show(False)
            self.w.getNSWindow().setMinSize_(self.minSize)
            self.w.palette.setPosSize((0,0,-0,-0))
            self.w.setPosSize((winX, winY, newWidth, height))
            self.isEditingHotkeys=False
        self.windowResize(self.w)

    def hideToolbarAction(self, value):
        for window in AllGlyphWindows():
            if value == 1 or value == True:
                window.window().getNSWindow().hideToolbar_(True)
            else:
                window.window().getNSWindow().showToolbar_(True)

    def _updateTools(self):
        for toolName in self.toolDescription:
            active = self.toolDescription[toolName]

            for toolObj in self.tools:
                if toolObj.__class__.__name__ == toolName:
                    if active:
                        installTool(toolObj)
                    else:
                        if len(getToolOrder()) > 1:
                            uninstallTool(toolObj)

    def listChangedCallback(self, sender):
        items = sender.get()
        selection = sender.getSelection()
        for index,item in enumerate(items):
            toolname = item['tool']
            oldValue = self.toolDescription[toolname]

            newValue = False
            if item['active'] == 1: newValue = True

            if newValue != oldValue:
                self.toolDescription[toolname] = newValue

                currTool = None
                for toolObj in self.tools:
                    if toolObj.__class__.__name__ == toolname:

                        if newValue:
                            installTool(toolObj)
                        else:
                            if len(getToolOrder()) > 1:
                                uninstallTool(toolObj)
                        break
                if not newValue:
                    if index in selection:
                        # if the selected tool is going to be disabled,
                        # the following code will switch to
                        # the first enabled tool
                        listOfValues = [self.toolDescription[name] for name in self.toolNames]
                        newSelection = []
                        for i, value in enumerate(listOfValues):
                            if value:
                                newSelection += [i]
                        print(newSelection)
                        if len(newSelection) > 1:
                            sender.setSelection([newSelection[0]])
                        else:
                            sender.setSelection(newSelection)

def openWindow():
    OpenWindow(ToolManagerWindow)












if __name__ == '__main__':
    if getExtensionDefault(showOnLaunchKey) is not None:
        if getExtensionDefault(showOnLaunchKey):
            openWindow()
