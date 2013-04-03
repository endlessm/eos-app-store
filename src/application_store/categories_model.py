from application_store.category_model import CategoryModel

class CategoriesModel():
    def __init__(self):
        self.categories = {}
    
    def get_categories_set(self):
        return frozenset(self.categories.values())
    
    def add_application(self, application):
        application.visit_categories(self.add)
        
    def add(self, category_name, application):
        category = self.categories.get(category_name, CategoryModel(category_name)) 
        category.add_application(application)
        self.categories[category_name] = category

    def get_updated_category(self, stale_category):
        return self.categories.get(stale_category.name())