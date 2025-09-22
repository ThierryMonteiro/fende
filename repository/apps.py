from django.apps import AppConfig

from watson import search as watson

class RepositoryConfig(AppConfig):
    name = 'repository'

    def ready(self):
        Product = self.get_model('Catalog')
        watson.register(Product)
