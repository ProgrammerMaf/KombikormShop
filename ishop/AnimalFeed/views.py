from django.utils import timezone
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import HttpResponseRedirect
from django.views import generic
from django.views.generic.base import View
from django.views.generic import DetailView
from django.views.generic.edit import FormView
from cart.cart import Cart
from .models import Commodity, OrderPart, Order, Photos
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.shortcuts import render
import re


class RegisterFormView(FormView):
    form_class = UserCreationForm
    success_url = "/login/"
    template_name = "AnimalFeed/register.html"

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect('../login')


class LoginFormView(FormView):
    form_class = AuthenticationForm
    template_name = "AnimalFeed/login.html"
    success_url = "/"

    def form_valid(self, form):
        # Получаем объект пользователя на основе введённых в форму данных.
        self.user = form.get_user()

        # Выполняем аутентификацию пользователя.
        login(self.request, self.user)
        return HttpResponseRedirect('../')


class LogoutView(View):
    def get(self, request):
        # Выполняем выход для пользователя, запросившего данное представление.
        logout(request)

        # После чего, перенаправляем пользователя на главную страницу.
        return HttpResponseRedirect("/")


def update_cart(post_dict, cart, erase_previous_value):
    for item in post_dict.items():
        if item[0].startswith('count_') and item[1] and int(item[1]) > 0:
            id = item[0][len('count_'):]
            addition_value = int(item[1])
            obj = Commodity.objects.get(id=id)
            if obj:
                cart.update(id, obj.commodity_name, obj.cost_per_item, addition_value, erase_previous_value)


class IndexView(generic.ListView):
    template_name = 'AnimalFeed/index.html'

    def get_context_data(self, **kwargs):
        context = dict()
        context['commodities'] = self.get_queryset()
        return context

    def get_queryset(self):
        return Commodity.objects.order_by('commodity_name')

    def post(self, request):
        return self.get(request)


class OrderConfirmation(generic.ListView):
    template_name = 'AnimalFeed/cart.html'

    def get_chosen_items(self, cart):
        keys = (i for i in filter(lambda i: re.match(r'\d+', i),cart))
        all_items = [(i, cart[i]['name'], cart[i]['quantity'], cart[i]['cost_per_one']) for i in keys]
        all_items.sort()
        return all_items

    def get_context_data(self, error_msg='', delivery_address='', customer_name='', phone=''):
        context = dict()
        context['error_msg'] = error_msg
        context['chosen'] = self.get_chosen_items(Cart(self.request).cart)
        context['delivery_address'] = delivery_address
        context['customer_name'] = customer_name
        context['customer_phone'] = phone
        return context

    def get_queryset(self):
        pass

    def check_cart(self, request):
        c = Cart(request)
        total_cost = 0
        for item in filter(lambda x: re.match(r'\d+', x[0]) is not None, c.cart.items()):
            quantity = item[1]['quantity']
            if quantity < 0:
                return total_cost, 'Попытка заказать отрицательное количество товара "{0}".'.format(item[1]['name'])
            id = item[0]
            obj = Commodity.objects.get(id=id)
            if not obj:
                return total_cost, 'Неверный id товара. Пожалуйста, напишите администратору.'
            if quantity > obj.remained_count:
                return total_cost, 'Заказ невозможен, на складе недостаточно товара "{0}".'.format(item[1]['name'])
            total_cost += quantity * obj.cost_per_item
        if total_cost == 0:
            return total_cost, 'Отправлен пустой заказ.'
        return total_cost, ''

    def get(self, request, **kwargs):
        auth_error =''
        if not request.user.is_authenticated():
            auth_error = 'Для оформления заказа нужно <a href="{0}">Авторизоваться</a>'.format('/login')
        cart = Cart(request).cart
        return render(request, self.template_name,
                      self.get_context_data(
                          error_msg=auth_error,
                          customer_name=cart['customer_name'],
                          delivery_address=cart['customer_address'],
                          phone=cart['customer_phone']
                      ))

    def page_with_error(self, request, error_message):
        return render(request, self.template_name,
                      self.get_context_data(
                          error_msg=error_message,
                          delivery_address=request.POST['delivery_address'],
                          customer_name=request.POST['customer_name'],
                          phone=request.POST['customer_phone']
                      ))

    def save_order(self, cart, total_cost, with_delivery, delivery_address, customer_name, customer_phone):
        new_order = Order(
            with_delivery=with_delivery,
            total_cost=total_cost,
            creation_time=timezone.now(),
            customer_name=customer_name,
            delivery_address=delivery_address,
            delivery_completion_time=timezone.now(),
            customer_phone=customer_phone,
            order_status='Создан'
        )
        new_order.save()

        for item in filter(lambda x: re.match(r'\d+', x[0]) is not None, cart.cart.items()):
            quantity = item[1]['quantity']
            id = item[0]

            obj = Commodity.objects.get(id=id)

            op = OrderPart(
                commodity_id=id,
                cost_per_one=obj.cost_per_item,
                count=quantity,
                order=new_order
            )
            op.save()

            obj.remained_count -= quantity
            obj.save()

        cart.cart.clear()

    def post(self, request):
        delivery_address = request.POST['delivery_address']
        customer_name = request.POST['customer_name']
        customer_phone = request.POST['customer_phone']

        cart = Cart(request)
        cart.save_parameters(
            customer_name=customer_name, customer_phone=customer_phone, customer_address=delivery_address)

        update_cart(request.POST, cart, True)
        if not request.user.is_authenticated():
            return self.page_with_error(request, 'Для оформления заказа нужно <a href="{0}">Авторизоваться</a>'.format('/login'))
        total_cost, error_message = self.check_cart(request)
        if error_message:
            return self.page_with_error(request, error_message)

        if not re.match(r'^\+?[0-9]+$', customer_phone):
            return self.page_with_error(request, 'Введите номер телефона в формате +79123456789')

        with_delivery = False
        if delivery_address:
            with_delivery = True
        else:
            delivery_address = 'Без доставки'

        self.save_order(cart, total_cost, with_delivery, delivery_address, customer_name, customer_phone)
        return HttpResponseRedirect('../accepted/')


class AcceptedOrderView(generic.ListView):
    template_name = 'AnimalFeed/acceptedOrder.html'

    def get_queryset(self):
        pass


class CommodityView(DetailView):
    model = Commodity
    template_name = 'AnimalFeed/commodity.html'

    def post(self, request, **kwargs):
        update_cart(request.POST, Cart(request), False)
        cart_path = '/confirmation'
        return render(request, self.template_name,
                      self.get_context_data(
                          pk=kwargs['pk'],
                          accept_msg="Товар успешно добавлен. Перейти в <a href='{0}'>корзину</a>".format(cart_path)
                      ))

    def get_context_data(self, **kwargs):
        current_commodity = Commodity.objects.get(pk=self.kwargs['pk'])
        context = dict()
        context['accept_msg'] = ''
        if 'accept_msg' in kwargs:
            context['accept_msg'] = kwargs['accept_msg']
        context['Commodity'] = current_commodity
        context['images'] = Photos.objects.filter(commodity=current_commodity)
        return context


class CommodityStaffView(generic.ListView):
    template_name = 'AnimalFeed/staffCommodity.html'

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(CommodityStaffView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = dict()
        context['username'] = self.request.user.username
        context['commodities'] = self.get_queryset()
        return context

    def get_queryset(self):
        return Commodity.objects.order_by('commodity_name')

    def modify_old(self, data):
        for comm in Commodity.objects.all():
            new_name = data["name_{0}".format(comm.id)]
            new_rem = data["rem_{0}".format(comm.id)]
            new_cpi = data["cpi_{0}".format(comm.id)]
            if new_name and new_rem and new_cpi:
                comm.commodity_name = new_name
                comm.remained_count = new_rem
                comm.cost_per_item = new_cpi
                comm.save()

    def add_new(self, data):
        new_name = data["new_name"]
        new_rem = data["new_remained_count"]
        new_cpi = data["new_cost"]
        if new_name and new_rem and new_cpi:
            c = Commodity(
                commodity_name=new_name,
                commodity_info='',
                remained_count=new_rem,
                cost_per_item=new_cpi
            )
            c.save()

    def post(self, request):
        self.modify_old(request.POST)
        self.add_new(request.POST)
        return self.get(request)


class OrderStaffView(generic.ListView):
    template_name = 'AnimalFeed/staffOrders.html'

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(OrderStaffView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = dict()
        context['username'] = self.request.user.username
        context['orders'] = self.get_queryset()
        return context

    def get_queryset(self):
        return Order.objects.order_by('creation_time')

    def modify_orders(self, data):
        for order in Order.objects.all():
            new_status = data['status_{0}'.format(order.id)]
            if new_status:
                order.order_status = new_status
                order.save()

    def post(self, request):
        self.modify_orders(request.POST)
        return self.get(request)


class CommodityEditView(DetailView):
    model = Commodity
    template_name = 'AnimalFeed/commodityEdit.html'

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(CommodityEditView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        current_commodity = Commodity.objects.get(pk=self.kwargs['pk'])
        context = dict()
        context['Commodity'] = current_commodity
        return context

    def post(self, request, **kwargs):
        new_info = request.POST['new_info']
        if new_info:
            current_commodity = Commodity.objects.get(pk=kwargs['pk'])
            current_commodity.commodity_info = new_info
            current_commodity.save()

        return self.get(request, kwargs)
