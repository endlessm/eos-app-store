import math

class ListPaginator:
    def __init__(self, list_of_items, page_size):
        self._list_of_items = list_of_items
        self._page_size = page_size
        self._page_count = math.ceil(len(self._list_of_items) / float(self._page_size))
        self._page_num = 0
        
    def number_of_pages(self):
        return int(self._page_count)
    
    def current_page(self):
        index = self.list_index_for_current_page()
        return self._list_of_items[index : index+self._page_size]
    
    def current_page_index(self):
        return self._page_num 
    
    def list_index_for_current_page(self):
        return self._page_num*self._page_size
    
    def go_to_page(self, page_num):
        self._page_num = page_num
        
    def next(self):
        self._page_num = int((self._page_num + 1) % self._page_count)  
        
    def prev(self):
        self._page_num = int((self._page_num + self._page_count - 1) % self._page_count)
        
    def is_last_page(self):
        return self.current_page_index() == (self.number_of_pages() - 1)