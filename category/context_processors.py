from .models import Category

def menu_links(request):
    """ This function will fetch all categories from the database """
    links = Category.objects.all()
    return dict(links=links)