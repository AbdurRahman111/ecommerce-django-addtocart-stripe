from .models import Bag, BagItem
from .views import _bag_id


def counter(request):
    """
    This will count the number of products in the shopping bag
    and display next to the cart icon in the top corner.
    """
    bag_count = 0
    if 'admin' in request.path:
        return {}
    else:
        try:
            bag = Bag.objects.filter(bag_id=_bag_id(request))

            if request.user.is_authenticated:
                bag_items = BagItem.objects.all().filter(user=request.user)
            else:
                bag_items = BagItem.objects.all().filter(bag=bag[:1])
            for bag_item in bag_items:
                bag_count += bag_item.quantity
        except Bag.DoesNotExist:
            bag_count = 0
    return dict(bag_count=bag_count)