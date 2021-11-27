from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Review
from category.models import Category
from bag.models import BagItem
from django.db.models import Q

from bag.views import _bag_id
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from .forms import ReviewForm
from django.contrib import messages
from checkout.models import OrderProduct


def store(request, category_slug=None):
    """
    This view will display the products by category.
    """
    categories = None
    products = None

    # Paginator created based on https://docs.djangoproject.com/en/3.2/topics/pagination/

    if category_slug != None:
        # This section is for All Products page
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True)
        product_count = products.count()
        paginator = Paginator(products, 6)
        page_number = request.GET.get('page')
        paged_products = paginator.get_page(page_number)
    else:
        # When a Category filter has been selected 
        products = Product.objects.all().filter(is_available=True).order_by('id')
        paginator = Paginator(products, 6)
        page_number = request.GET.get('page')
        paged_products = paginator.get_page(page_number)
        product_count = products.count()

    context = {
        'products': paged_products,
        'product_count': product_count,
    }

    return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
    """
    This view will display the individual products on a separate
    product detail page.
    """
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        # in_bag is to establish whether the item has already been added to the bag
        in_bag = BagItem.objects.filter(bag__bag_id=_bag_id(request), product=single_product).exists()
    except Exception as e:
        raise e

    # Checking if the user purchased the product to be able to leave the review
    if request.user.is_authenticated:
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None

    # Getting the reviews
    reviews = Review.objects.filter(product_id=single_product.id, status=True)

    context = {
        'single_product': single_product,
        'in_bag': in_bag,
        'orderproduct': orderproduct,
        'reviews': reviews,
    }

    return render(request, 'store/product_detail.html', context)


def search(request):
    """
    Search functionality for the given keyword in the product name and description
    """
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_date').filter(
                Q(product_description__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count = products.count()
    context = {
        'products': products,
        'product_count': product_count
    }
    return render(request, 'store/store.html', context)


def submit_review(request, product_id):
    """
    This view will update or create a review for an individual product.
    """
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            # Update review, if review exists
            reviews = Review.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you, your review has been updated!')
            return redirect(url)
        except Review.DoesNotExist:
            # Creates a new review
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = Review()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you for reviewing the product!')
                return redirect(url)