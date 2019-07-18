from AppKit import NSTextFieldCell, NSFont, NSRegularControlSize, NSSmallControlSize, NSMiniControlSize
import objc

_sizeStyleMap = {
    "regular": NSRegularControlSize,
    "small": NSSmallControlSize,
    "mini": NSMiniControlSize
}

def _setSizeStyle(obj, value):
        value = _sizeStyleMap[value]
        obj.setControlSize_(value)
        font = NSFont.systemFontOfSize_(NSFont.systemFontSizeForControlSize_(value))
        obj.setFont_(font)

class _VerticallyCenteredTextFieldCell(NSTextFieldCell):
    mIsEditingOrSelecting = False

    # def init(self):
    #     self = objc.super(_VerticallyCenteredTextFieldCell, self).init()
    #     if self is None: return None
    #
    #     # code here
    #     font = self.font()
    #     font.fontWithSize_(2)
    #     self.setFont_(font)
    #     return self

    def drawingRectForBounds_(self, theRect):
        # Get the parent's idea of where we should draw
        newRect = super().drawingRectForBounds_(theRect)

        # When the text field is being
        # edited or selected, we have to turn off the magic because it screws up
        # the configuration of the field editor.  We sneak around this by
        # intercepting selectWithFrame and editWithFrame and sneaking a
        # reduced, centered rect in at the last minute.
        if self.mIsEditingOrSelecting is False:
            # Get our ideal size of current text
            textSize = self.cellSizeForBounds_(theRect)

            # Center in the proposed rect
            heightDelta = newRect.size.height - textSize.height
            if heightDelta > 0:
                newRect.size.height -= heightDelta
                newRect.origin.y += heightDelta/2

        return newRect

def VerticallyCenteredTextFieldCell(sizeStyle='regular',singleLine=True,editable=False):
    cell = _VerticallyCenteredTextFieldCell.alloc().init()
    cell.setUsesSingleLineMode_(singleLine)
    cell.setEditable_(editable)
    _setSizeStyle(cell,sizeStyle)
    return cell
