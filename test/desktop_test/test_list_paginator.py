import unittest
from desktop.list_paginator import ListPaginator

class TestListPaginator(unittest.TestCase):

    def test_get_number_of_pages_given_empty_list(self):
        test_object = ListPaginator([], 4)
        self.assertEquals(0, test_object.number_of_pages())

    def test_get_number_of_pages_given_small_list(self):
        test_object = ListPaginator([1, 2], 4)
        self.assertEquals(1, test_object.number_of_pages())

    def test_get_number_of_pages_given_list_exact_size(self):
        test_object = ListPaginator([1, 2, 3, 4], 4)
        self.assertEquals(1, test_object.number_of_pages())

    def test_get_number_of_pages_given_list(self):
        test_object = ListPaginator([1, 2, 3, 4, 5], 4)
        self.assertEquals(2, test_object.number_of_pages())
        
    def test_paginator_defaults_to_first_page(self):
        test_object = ListPaginator([1, 2, 3, 4, 5], 4)
        self.assertEquals([1, 2, 3, 4], test_object.current_page())
        
    def test_go_to_page(self):
        test_object = ListPaginator([1, 2, 3, 4, 5, 6, 7, 8, 9], 4)
        self.assertEquals(3, test_object.number_of_pages())
        test_object.go_to_page(1)
        self.assertEquals([5, 6, 7, 8], test_object.current_page())
        test_object.go_to_page(2)
        self.assertEquals([9], test_object.current_page())
        
    def test_next(self):
        test_object = ListPaginator([1, 2, 3, 4, 5, 6, 7, 8, 9], 4)
        self.assertEquals(3, test_object.number_of_pages())
        test_object.next()
        self.assertEquals([5, 6, 7, 8], test_object.current_page())
        test_object.next()
        self.assertEquals([9], test_object.current_page())
        
    def test_prev(self):
        test_object = ListPaginator([1, 2, 3, 4, 5, 6, 7, 8, 9], 4)
        self.assertEquals(3, test_object.number_of_pages())
        test_object.go_to_page(2)
        self.assertEquals([9], test_object.current_page())
        test_object.prev()
        self.assertEquals([5, 6, 7, 8], test_object.current_page())
        test_object.prev()
        self.assertEquals([1, 2, 3, 4], test_object.current_page())
        
    def test_next_rolls_around_to_start(self):
        test_object = ListPaginator([1, 2, 3, 4, 5, 6, 7, 8, 9], 4)
        self.assertEquals(3, test_object.number_of_pages())
        self.assertEquals(0, test_object.current_page_index())
        test_object.next()
        self.assertEquals(1, test_object.current_page_index())
        self.assertEquals([5, 6, 7, 8], test_object.current_page())
        test_object.next()
        self.assertEquals(2, test_object.current_page_index())
        self.assertEquals([9], test_object.current_page())
        test_object.next()
        self.assertEquals(0, test_object.current_page_index())
        self.assertEquals([1, 2, 3, 4], test_object.current_page())
        
    def test_prev_rolls_around_to_end(self):
        test_object = ListPaginator([1, 2, 3, 4, 5, 6, 7, 8, 9], 4)
        self.assertEquals(3, test_object.number_of_pages())
        self.assertEquals(0, test_object.current_page_index())
        test_object.prev()
        self.assertEquals(2, test_object.current_page_index())
        self.assertEquals([9], test_object.current_page())
        test_object.prev()
        self.assertEquals(1, test_object.current_page_index())
        self.assertEquals([5, 6, 7, 8], test_object.current_page())
        test_object.prev()
        self.assertEquals(0, test_object.current_page_index())
        self.assertEquals([1, 2, 3, 4], test_object.current_page())
        
    def test_list_index_for_current_page(self):
        test_object = ListPaginator([1, 2, 3, 4, 5, 6, 7, 8, 9], 4)
        self.assertEquals(0, test_object.list_index_for_current_page())
        test_object.prev()
        self.assertEquals(8, test_object.list_index_for_current_page())
        test_object.prev()
        self.assertEquals(4, test_object.list_index_for_current_page())
        test_object.prev()
        self.assertEquals(0, test_object.list_index_for_current_page())
