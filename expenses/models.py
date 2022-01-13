from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

# Create your models here.


class Expense(models.Model):
    amount = models.FloatField()
    date = models.DateField(default=now)
    description = models.TextField()
    owner = models.ForeignKey(to=User, on_delete=models.CASCADE)
    category = models.CharField(max_length=266)

    def __str__(self):
        return self.category

    class Meta:
        ordering: ['-date']


class Category(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Splits(models.Model):
    username = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_splits")
    name = models.TextField()
    datecreated = models.DateField()

class Splitmembers(models.Model):
    splitid = models.ForeignKey(Splits, related_name="Split_members", on_delete=models.CASCADE)
    member = models.ForeignKey(User, related_name="memeber_splits", on_delete=models.CASCADE)

class Splittransactions(models.Model):
    splitid = models.ForeignKey(Splits, on_delete=models.CASCADE, related_name="split_transactions")
    spentby = models.ForeignKey(User, on_delete=models.CASCADE, related_name="split_spentby")
    amount = models.IntegerField()
    spentfor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="split_spentfor")
    datespent = models.DateField()
    spentat = models.TextField()
    mode = models.CharField(max_length=1)