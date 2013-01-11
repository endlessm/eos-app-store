
class MemUtils():
   SCALE = {'kB': 1024.0, 'mB': 1024.0*1024.0,
            'KB': 1024.0, 'MB': 1024.0*1024.0}

   def process_mem_size(self, pid, mem_units):
      with open("/proc/" + str(pid) + "/status", "r") as f:
         proc_status = f.read()

      index = proc_status.index("VmSize")
      vm_data = proc_status[index:].split(None, 3)
      value = vm_data[1]
      units = vm_data[2]

      return self._convert_to(value, units, mem_units)

   def _convert_to(self, size, from_units, to_units):
      size_in_bytes = float(size) * self.SCALE[from_units]
      converted_size = size_in_bytes / self.SCALE[to_units]
      return int(converted_size)
