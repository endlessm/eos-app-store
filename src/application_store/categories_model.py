from application_store.category_model import CategoryModel
from sets import ImmutableSet

class CategoriesModel():
    def __init__(self):
        self.categories = {}
    
    def get_categories_set(self):
        return ImmutableSet(self.categories.values())
    
    def add_application(self, application):
        application.visit(self.add)
    
    def add(self, category_name, application):
        category = self.categories.get(category_name, CategoryModel(category_name)) 
        category.add_application(application)
        self.categories[category_name] = category
