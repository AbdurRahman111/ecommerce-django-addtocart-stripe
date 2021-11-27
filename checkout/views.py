from django.shortcuts import render, redirect
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from bag.models import Bag, BagItem
from .forms import OrderForm
from .models import Order, OrderProduct, Payment
import datetime
import stripe
import random
from django.views.generic import ListView, DetailView, View
from django.contrib import messages
from bag.views import _bag_id



stripe.api_key = settings.STRIPE_SECRET_KEY



"""
def payments(request):
    return render(request, 'checkout/payments.html')
"""




def place_order(request, total=0, quantity=0):
    stripe_public_key = settings.STRIPE_PUBLIC_KEY
    stripe_secret_key = settings.STRIPE_SECRET_KEY
    current_user = request.user
    bag_items = BagItem.objects.filter(user=current_user)
    bag_count = bag_items.count()
    if bag_count <= 0:
        return redirect ('store')

    grand_total = 0
    tax = 0
    for item in bag_items:
        total += (item.product.price * item.quantity)
        quantity += item.quantity
    tax = (5 * total) / 100
    grand_total = total + tax
    stripe_total = round(grand_total * 100)
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # Generating Order Number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d") #20210305
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            # Stripe
            stripe.api_key = stripe_secret_key
            intent = stripe.PaymentIntent.create(
                amount=stripe_total,
                currency=settings.STRIPE_CURRENCY,
            )

            print(intent)

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'bag_items': bag_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
                'stripe_public_key': stripe_public_key,
                'client_secret': intent.client_secret,
            }
            return render(request, 'checkout/payments.html', context)
    else:
        return redirect('checkout')


@login_required(login_url='login')
def checkout(request, total=0, quantity=0, bag_items=None):
    print('ssss')
    """ A view to process checkout functionality """
    stripe_public_key = settings.STRIPE_PUBLIC_KEY
    stripe_secret_key = settings.STRIPE_SECRET_KEY

    if request.method == 'POST':
        if request.user.is_authenticated:
            bag_items = BagItem.objects.filter(user=request.user, is_active=True)    
        else:
            bag = Bag.objects.get(bag_id=_bag_id(request))
            bag_items = BagItem.objects.filter(bag=bag, is_active=True)

        for bag_item in bag_items:
            total += (bag_item.product.price * bag_item.quantity)
            quantity += bag_item.quantity

        print(total, quantity)

        tax = (5 * total) / 100
        grand_total = total + tax

        first_name = request.POST.get('first_name')
        last_name= request.POST.get('last_name')
        email= request.POST.get('email')
        phone= request.POST.get('phone')
        address_line_1= request.POST.get('address_line_1')
        address_line_2= request.POST.get('address_line_2')
        city= request.POST.get('city')
        country=request.POST.get('country')
        order_note= request.POST.get('order_note')

        print('first_name, last_name, email, phone, address_line_1, address_line_2, city, country, order_note')
        print(first_name, last_name, email, phone, address_line_1, address_line_2, city, country, order_note)

        # make random order ID
        random_num = random.randint(2345678909800, 9923456789000)

        uniqe_confirm = Order.objects.filter(order_number=random_num)
        # print(random_num)
        while uniqe_confirm:
            random_num = random.randint(234567890980000, 992345678900000)
            if not Order.objects.filter(order_number=random_num):
                break
        # print(random_num)

        new_Order = Order(user = request.user, order_number=random_num, first_name=first_name, last_name=last_name, phone=email, email=phone, address_line_1=address_line_1, address_line_2=address_line_2, country=country, city=city, order_note=order_note, order_total=total, tax=tax, ip=request.META.get('REMOTE_ADDR') , is_ordered=False)
        new_Order.save()

        for bag_item in bag_items:
            total += (bag_item.product.price * bag_item.quantity)
            quantity += bag_item.quantity

            print('bag_item vari')
            print(bag_item)

            New_OrderProduct = OrderProduct(order=new_Order, user=request.user, product=bag_item.product, quantity=bag_item.quantity, product_price=bag_item.product.price)
            New_OrderProduct.save()



            for vari in bag_item.variations.all():
                print('varivari')
                print(vari)
                New_OrderProduct.variations.add(vari)


        return redirect('payment')

    else:
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
    return render(request, 'store/checkout.html', context)




class PaymentView(View):
    def get(self, *args, **kwargs):
        total = 0
        quantity = 0
        tax = 0
        grand_total = 0
        if self.request.user.is_authenticated:
            bag_items = BagItem.objects.filter(user=self.request.user, is_active=True)
        else:
            bag = Bag.objects.get(bag_id=_bag_id(request))
            bag_items = BagItem.objects.filter(bag=bag, is_active=True)


        for bag_item in bag_items:
            total += (bag_item.product.price * bag_item.quantity)
            quantity += bag_item.quantity
        tax = (5 * total) / 100
        grand_total = total + tax

        stripe_public_key = settings.STRIPE_PUBLIC_KEY

        context = {
            'total': total,
            'quantity': quantity,
            'bag_items': bag_items,
            'tax': tax,
            'grand_total': grand_total,
            'stripe_public_key':stripe_public_key,
        }
        return render(self.request, 'store/final_checkout.html', context)

    def post(self, *args, **kwargs):
        total = 0
        quantity = 0
        tax = 0
        grand_total = 0
        if self.request.user.is_authenticated:
            bag_items = BagItem.objects.filter(user=self.request.user, is_active=True)
        else:
            bag = Bag.objects.get(bag_id=_bag_id(request))
            bag_items = BagItem.objects.filter(bag=bag, is_active=True)

        for bag_item in bag_items:
            total += (bag_item.product.price * bag_item.quantity)
            quantity += bag_item.quantity
        tax = (5 * total) / 100
        grand_total = total + tax

        user = self.request.user
        order = Order.objects.filter(user=user, is_ordered=False).last()

        print(order.order_number)
        try:
            customer = stripe.Customer.create(
                email=self.request.user.email,
                description=self.request.user.username,
                source=self.request.POST['stripeToken']
            )
            amount = round(total)
            charge = stripe.Charge.create(
                amount=(amount * 100),
                currency="usd",
                customer=customer,
                description="Payment for online Shop",
            )

            new_Payment = Payment(user=self.request.user, payment_id=order.order_number, payment_method="Stripe", amount_paid=amount, status="Complete")
            new_Payment.save()

            order.is_ordered = True
            order.payment = new_Payment
            order.save()

            filter_OrderProduct  = OrderProduct.objects.filter(order=order)
            for prd in filter_OrderProduct:
                prd.payment=new_Payment
                prd.ordered=True
                prd.save()

            try:
                bag = Bag.objects.filter(bag_id=_bag_id(self.request))
                if self.request.user.is_authenticated:
                    bag_items = BagItem.objects.all().filter(user=self.request.user)
                    print(bag_items)
                else:
                    bag_items = BagItem.objects.all().filter(bag=bag[:1])
                    print(bag_items)

                for bag_item in bag_items:
                    print(bag_item)
                    bag_item.delete()


            except Bag.DoesNotExist:
                pass

            messages.success(self.request, 'Payment was Successfull !!')
            return redirect('home')


        except stripe.error.CardError as e:
            messages.info(self.request, f"{e.error.message}")
            return redirect('home')

        except stripe.error.RateLimitError as e:
            messages.info(self.request, f"{e.error.message}")
            return redirect('home')
        except stripe.error.InvalidRequestError as e:
            messages.info(self.request, "Invalid Request !")
            return redirect('home')
        except stripe.error.AuthenticationError as e:
            messages.info(self.request, "Authentication Error !!")
            return redirect('home')
        except stripe.error.APIConnectionError as e:
            messages.info(self.request, "Check Your Connection !")
            return redirect('home')
        except stripe.error.StripeError as e:
            messages.info(self.request, "There was an error please try again !")
            return redirect('home')
        except Exception as e:
            messages.info(self.request, "A serious error occured we were notified !")
            return redirect('home')

