import wx, wx.grid

class GridData(wx.grid.PyGridTableBase):
    _cols = "a b c".split()
    _data = [
        "1 2 3".split(),
        "4 5 6".split(),
        "7 8 9".split()
    ]

    def GetColLabelValue(self, col):
        return self._cols[col]

    def GetNumberRows(self):
        return len(self._data)

    def GetNumberCols(self):
        return len(self._cols)

    def GetValue(self, row, col):
        return self._data[row][col]

    def SetValue(self, row, col, val):
        self._data[row][col] = val

class Test(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None)
        self.data = GridData()
        grid = wx.grid.Grid(self)
        grid.SetTable(self.data)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Show()

    def OnClose(self, event):
        print self.data._data
        event.Skip()

app = wx.PySimpleApp()
app.TopWindow = Test()
app.MainLoop()