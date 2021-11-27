from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from .models import Bag, BagItem
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
import stripe


def view_bag(request, total=0, quantity=0, bag_items=None):
    """ A view to see the contents of the shopping bag """
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            bag_items = BagItem.objects.filter(user=request.user, is_active=True)    
        else:
            bag = Bag.objects.get(bag_id=_bag_id(request))
            bag_items = BagItem.objects.filter(bag=bag, is_active=True)
        for bag_item in bag_items:
            total += (bag_item.product.price * bag_item.quantity)
            quantity += bag_item.quantity
        tax = (5 * total) / 100
        grand_total = total + tax
    except ObjectDoesNotExist:
            pass

    context = {
        'total': total,
        'quantity': quantity,
        'bag_items': bag_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/bag.html', context)


def _bag_id(request):
    """
    Bag ID will be the session ID for the Add to bag view,
    this is why this view will request the session ID.
    If there is none, this will create a session ID
    """
    bag = request.session.session_key
    if not bag:
        bag = request.session.create()
    return bag


def add_to_bag(request, product_id):
    """ 
    This view will add the product into the
    shopping bag in the given quantity, in the selected variation.
    """
    current_user = request.user
    product = Product.objects.get(id=product_id)
    
    # If-Else whether user is authenticated or not
    if current_user.is_authenticated:
        product_variation = []
        if request.method == 'POST':
            # This will store the category and value in key-value pairs,
            # for example color-white, size-medium;
            for item in request.POST:
                key = item
                value = request.POST[key]
                
                try:
                    variation = Variation.objects.get(variation_category__iexact=key,
                        variation_value__iexact=value, product=product)
                    product_variation.append(variation)
                except:
                    pass

        # This section will group Bag Item variations, for example if the same
        # size and colours are added again, it will not be a new line but will
        # increase the quantity of the existing bag item

        is_bag_item_exists = BagItem.objects.filter(product=product, user=current_user).exists()
        if is_bag_item_exists:
            bag_item = BagItem.objects.filter(product=product, user=current_user)
            existing_variation_list = []
            bag_item_id = []
            for item in bag_item:
                existing_variation = item.variations.all()
                existing_variation_list.append(list(existing_variation))
                bag_item_id.append(item.id)

            if product_variation in existing_variation_list:
                # Increase the bag item quantity 
                index = existing_variation_list.index(product_variation)
                item_id = bag_item_id[index]
                item = BagItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()
            else:
                item = BagItem.objects.create(product=product, quantity=1, user=current_user)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        else:
            bag_item = BagItem.objects.create(
                product = product,
                quantity = 1,
                user = current_user,
            )
            if len(product_variation) > 0:
                bag_item.variations.clear()
                bag_item.variations.add(*product_variation)
            bag_item.save()
        return redirect('bag')

    else:
        product_variation = []
        if request.method == 'POST':
            # This will store the category and value in key-value pairs,
            # for example color-white, size-medium;
            for item in request.POST:
                key = item
                value = request.POST[key]
                
                try:
                    variation = Variation.objects.get(variation_category__iexact=key,
                        variation_value__iexact=value, product=product)
                    product_variation.append(variation)
                except:
                    pass
        
        try:
            # Get the Bag ID present in the session
            bag = Bag.objects.get(bag_id=_bag_id(request))
        except Bag.DoesNotExist:
            bag = Bag.objects.create(
                bag_id = _bag_id(request)
            )
        bag.save()

        # This section will group Bag Item variations, for example if the same
        # size and colours are added again, it will not be a new line but will
        # increase the quantity of the existing bag item

        is_bag_item_exists = BagItem.objects.filter(product=product, bag=bag).exists()
        if is_bag_item_exists:
            bag_item = BagItem.objects.filter(product=product, bag=bag)
            existing_variation_list = []
            bag_item_id = []
            for item in bag_item:
                existing_variation = item.variations.all()
                existing_variation_list.append(list(existing_variation))
                bag_item_id.append(item.id)

            if product_variation in existing_variation_list:
                # Increase the bag item quantity 
                index = existing_variation_list.index(product_variation)
                item_id = bag_item_id[index]
                item = BagItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()
            else:
                item = BagItem.objects.create(product=product, quantity=1, bag=bag)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        else:
            bag_item = BagItem.objects.create(
                product = product,
                quantity = 1,
                bag = bag,
            )
            if len(product_variation) > 0:
                bag_item.variations.clear()
                bag_item.variations.add(*product_variation)
            bag_item.save()
        return redirect('bag')


def remove_from_bag(request, product_id, bag_item_id):
    """ 
    This view will decrease the product from the 
    shopping bag, or remove if the amount reaches 0
    """    
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            bag_item = BagItem.objects.get(product=product, user=request.user, id=bag_item_id)
        else:
            bag = Bag.objects.get(bag_id=_bag_id(request))
            bag_item = BagItem.objects.get(product=product, bag=bag, id=bag_item_id)
        if bag_item.quantity > 1:
            bag_item.quantity -= 1
            bag_item.save()
        else:
            bag_item.delete()
    except:
        pass
    return redirect('bag')


def remove_bag_item(request, product_id, bag_item_id):
    """ 
    This view will act as a Delete Button to delete the product
    from the shopping bag, regardless of the quantity.
    """    
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        bag_item = BagItem.objects.get(product=product, user=request.user, id=bag_item_id)
    else:
        bag = Bag.objects.get(bag_id=_bag_id(request))
        bag_item = BagItem.objects.get(product=product, bag=bag, id=bag_item_id)
    bag_item.delete()
    return redirect('bag')


