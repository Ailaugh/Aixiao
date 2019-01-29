# Generated by Django 2.1.5 on 2019-01-16 07:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Buyer', '0002_emailvalid'),
    ]

    operations = [
        migrations.CreateModel(
            name='BuyCar',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('goods_id', models.CharField(max_length=32)),
                ('goods_name', models.CharField(max_length=32)),
                ('goods_price', models.FloatField()),
                ('goods_picture', models.ImageField(upload_to='image')),
                ('goods_num', models.IntegerField()),
                ('user', models.ForeignKey(on_delete=True, to='Buyer.Buyer')),
            ],
        ),
    ]
