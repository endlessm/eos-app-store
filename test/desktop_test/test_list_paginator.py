import unittest
from desktop.list_paginator import ListPaginator

class TestListPaginator(unittest.TestCase):

    def test_get_number_of_pages_given_empty_list(self):
        test_object = ListPaginator([], lambda:4)
        self.assertEquals(0, test_object.number_of_pages())

    def test_get_number_of_pages_given_small_list(self):
        test_object = ListPaginator([1, 2], lambda:4)
        self.assertEquals(1, test_object.number_of_pages())

    def test_get_number_of_pages_given_list_exact_size(self):
        test_object = ListPaginator([1, 2, 3, 4], lambda:4)
        self.assertEquals(1, test_object.number_of_pages())

    def test_get_number_of_pages_given_list(self):
        test_object = ListPaginator([1, 2, 3, 4, 5], lambda:4)
        self.assertEquals(2, test_object.number_of_pages())
        
    def test_paginator_defaults_to_first_page(self):
        test_object = ListPaginator([1, 2, 3, 4, 5], lambda:4)
        self.assertEquals([1, 2, 3, 4], test_object.current_page())
        
    def test_go_to_page(self):
        test_object = ListPaginator([1, 2, 3, 4, 5, 6, 7, 8, 9], lambda:4)
        self.assertEquals(3, test_object.number_of_pages())
        test_object.go_to_page(2)
        self.assertEquals([5, 6, 7, 8], test_object.current_page())
        test_object.go_to_page(3)
        self.assertEquals([9], test_object.current_page())
        
    def test_next(self):
        test_object = ListPaginator([1, 2, 3, 4, 5, 6, 7, 8, 9], lambda:4)
        self.assertEquals(3, test_object.number_of_pages())
        test_object.next()
        self.assertEquals([5, 6, 7, 8], test_object.current_page())
        test_object.next()
        self.assertEquals([9], test_object.current_page())
        
    def test_prev(self):
        test_object = ListPaginator([1, 2, 3, 4, 5, 6, 7, 8, 9], lambda:4)
        self.assertEquals(3, test_object.number_of_pages())
        test_object.go_to_page(3)
        self.assertEquals([9], test_object.current_page())
        test_object.prev()
        self.assertEquals([5, 6, 7, 8], test_object.current_page())
        test_object.prev()
        self.assertEquals([1, 2, 3, 4], test_object.current_page())
        
    def test_next_rolls_around_to_start(self):
        test_object = ListPaginator([1, 2, 3, 4, 5, 6, 7, 8, 9], lambda:4)
        self.assertEquals(3, test_object.number_of_pages())
        self.assertEquals(1, test_object.current_page_number())
        test_object.next()
        self.assertEquals(2, test_object.current_page_number())
        self.assertEquals([5, 6, 7, 8], test_object.current_page())
        test_object.next()
        self.assertEquals(3, test_object.current_page_number())
        self.assertEquals([9], test_object.current_page())
        test_object.next()
        self.assertEquals(1, test_object.current_page_number())
        self.assertEquals([1, 2, 3, 4], test_object.current_page())
        
    def test_prev_rolls_around_to_end(self):
        test_object = ListPaginator([1, 2, 3, 4, 5, 6, 7, 8, 9], lambda:4)
        self.assertEquals(3, test_object.number_of_pages())
        self.assertEquals(1, test_object.current_page_number())
        test_object.prev()
        self.assertEquals(3, test_object.current_page_number())
        self.assertEquals([9], test_object.current_page())
        test_object.prev()
        self.assertEquals(2, test_object.current_page_number())
        self.assertEquals([5, 6, 7, 8], test_object.current_page())
        test_object.prev()
        self.assertEquals(1, test_object.current_page_number())
        self.assertEquals([1, 2, 3, 4], test_object.current_page())
        
    def test_list_index_for_current_page(self):
        test_object = ListPaginator([1, 2, 3, 4, 5, 6, 7, 8, 9], lambda:4)
        self.assertEquals(0, test_object.list_index_for_current_page())
        test_object.prev()
        self.assertEquals(8, test_object.list_index_for_current_page())
        test_object.prev()
        self.assertEquals(4, test_object.list_index_for_current_page())
        test_object.prev()
        self.assertEquals(0, test_object.list_index_for_current_page())
        
    def test_next_page_circles_to_the_beginning(self):
        test_object = ListPaginator([1, 2, 3, 4, 5, 6, 7, 8, 9], lambda:4)
        test_object.go_to_page(test_object.number_of_pages())
        test_object.next()
        self.assertEquals(1, test_object.current_page_number())
        self.assertFalse(test_object.is_last_page())
    
    def test_last_page(self):
        test_object = ListPaginator([1,2], lambda:1)
        self.assertFalse(test_object.is_last_page())
        test_object.go_to_page(test_object.number_of_pages())
        self.assertTrue(test_object.is_last_page())
        
    def test_page_index_set_to_last_page_if_no_items_on_current_page(self):
        test_object = ListPaginator([1, 2], lambda:1)
        test_object.go_to_page(1)
        
        test_object.adjust_list_of_items([1])
        
        self.assertEquals(1, test_object.current_page_number())
        
        test_object.go_to_page(3)
        test_object.adjust_list_of_items([1, 2])
        
        self.assertEquals(test_object.number_of_pages(), test_object.current_page_number())

    def test_return_all_items(self):
        test_object = ListPaginator([1, 2], lambda:1)

        self.assertEquals([1, 2], test_object.all_items())

