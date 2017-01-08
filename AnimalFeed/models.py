from django.db import models
from django.contrib.auth.models import User

class Commodity(models.Model):
    commodity_name = models.CharField(max_length=200)
    commodity_info = models.TextField()
    remained_count = models.IntegerField(default=0)
    cost_per_item = models.FloatField()

    def __str__(self):
        return "{0}".format(self.commodity_name)


class Photos(models.Model):
    commodity = models.ForeignKey(Commodity)
    picture = models.ImageField(upload_to='pictures')

    def __str__(self):
        return "{0} for {1}".format(self.id, self.commodity.commodity_name)


class Order(models.Model):
    with_delivery = models.BooleanField()
    total_cost = models.FloatField()
    creation_time = models.DateTimeField()
    delivery_completion_time = models.DateTimeField()
    delivery_address = models.CharField(max_length=150)
    order_status = models.CharField(max_length=30)
    customer_name = models.CharField(max_length=150)
    customer_phone = models.CharField(max_length=15)

    def __str__(self):
        return "{0} in {1}".format(self.id, self.creation_time)


class OrderPart(models.Model):
    order = models.ForeignKey(Order)
    commodity = models.ForeignKey(Commodity)
    count = models.IntegerField()
    cost_per_one = models.FloatField()

    def __str__(self):
        return "Order {0}: {1} - {2} items per {3}".format(
            self.order.id,
            self.commodity.id,
            self.count,
            self.cost_per_one
        )


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    address = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=15)
