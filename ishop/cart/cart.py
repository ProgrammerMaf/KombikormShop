from decimal import Decimal
from django.conf import settings

class Cart(object):
    def __init__(self, request):
        # Инициализация корзины пользователя
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # Сохраняем корзину пользователя в сессию
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        self.my_field = '42'

    # Сохранение данных в сессию
    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart
        # Указываем, что сессия изменена
        self.session.modified = True

    # Добавление товара в корзину пользователя или обновление количества товара
    def update(self, id, name, cost_per_one, quantity=1, erase_previous_value=False):

        if id not in self.cart:
            self.cart[id] = {'quantity': 0,
                             'name': name,
                             'cost_per_one': cost_per_one
                            }
        if erase_previous_value:
            self.cart[id]['quantity'] = quantity
        else:
            self.cart[id]['quantity'] += quantity
        if self.cart[id]['quantity'] <= 0:
            self.cart.pop(id)
        self.save()