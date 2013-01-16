import gtk
import json
import operator
import dbus
import dbus.service

class UatHelper(dbus.service.Object):
    def __init__(self):
        bus_name = dbus.service.BusName('com.endlessm.uat.Desktop', dbus.SessionBus())
        dbus.service.Object.__init__(self, bus_name, "/com/endlessm/uat/Desktop")
    
    def setup(self, root_node):
        self._root_node = root_node

    @dbus.service.method('com.endlessm.uat.Desktop', in_signature='', out_signature='s')
    def get_gtk_tree_info(self):
        self._data = {}
        self._traverse(self._root_node)
        for window in gtk.window_list_toplevels():
            self._traverse(window)

        return json.dumps(self._data)

    def _traverse(self, current_node):
        if isinstance(current_node, gtk.Widget):
            if hasattr(current_node, "uat_id"):
                self._extract_info(current_node)
    
        if isinstance(current_node, gtk.Container):
            for node in current_node.get_children():
                self._traverse(node)
                
    def _extract_info(self, widget):
        window_coords = self._root_node.window.get_root_origin()
        widget_coords = widget.translate_coordinates(widget.get_toplevel(), 0, 0)
        absolute_coords = tuple(map(operator.add, window_coords, widget_coords))

        widget_size = widget.get_size_request()
        if widget_size == (-1, -1):
            widget_size = (widget.allocation.width,widget.allocation.height)
             
        widget_middle = tuple(map(operator.div, widget_size, (2.0, 2.0)))
             
        click_area = tuple(map(operator.add, absolute_coords, widget_middle))
        
        if hasattr(widget, "uat_offset"):
            widget_offset = widget.uat_offset
            click_area = tuple(map(operator.add, click_area, widget_offset))
            
        self._data[widget.uat_id] = { "coord": click_area }
