import gtk
import glib

class UatHelper():
   REQUEST_FILE="/tmp/endless_uat_helper.request"
   DATA_FILE="/tmp/endless_uat_helper.data"

   def __init__(self):
      self._data = {}

   def setup(self, root_node):
      self._root_node = root_node
      glib.io_add_watch(open(self.REQUEST_FILE, "r"), 
            glib.IO_IN || glib.IO_HUP, self._handle_request_for_data)

   def _handle_request_for_data(self, source, condition)
      if condition == glib.IO_HUP:
         source.close()
      else:
         self._gather_info()
         with open(self.DATA_FILE, "w") as f:
            json_data = json.dumps(self._data)
            f.write(json_data)

   def _gather_info(self):
      self._traverse(self._root_node)

   def _traverse(self, current_node):
      if isinstance(current_node, gtk.Widget):
         self._extract_info(current_node)

      if isinstance(current_node, gtk.Container):
         for node in current_node.get_children():
            self._traverse(node)

   def _extract_info(self, widget):
      ...
      self._data[key] = { "coord": (x, y) }
