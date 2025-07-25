# Generated by Django 5.2.4 on 2025-07-24 18:23

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField()),
                ('country', models.CharField(default='Indonesia', max_length=100)),
                ('province', models.CharField(max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'Cities',
            },
        ),
        migrations.CreateModel(
            name='DestinationCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True)),
                ('icon', models.CharField(help_text='FontAwesome icon class', max_length=50)),
            ],
            options={
                'verbose_name_plural': 'Destination Categories',
            },
        ),
        migrations.CreateModel(
            name='Destination',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('address', models.TextField()),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('average_cost', models.DecimalField(decimal_places=2, help_text='Average cost in IDR', max_digits=10)),
                ('estimated_duration_hours', models.DecimalField(decimal_places=2, help_text='Estimated visit duration in hours', max_digits=4)),
                ('rating', models.DecimalField(decimal_places=2, default=0, max_digits=3, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)])),
                ('popularity_score', models.IntegerField(default=0, help_text='Higher score = more popular')),
                ('opening_hours', models.CharField(help_text="e.g., '08:00-17:00' or '24 hours'", max_length=200)),
                ('best_time_to_visit', models.CharField(help_text="e.g., 'Morning', 'Evening', 'Anytime'", max_length=100)),
                ('image_url', models.URLField(blank=True, help_text='Main image URL')),
                ('website', models.URLField(blank=True)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('city', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='destinations', to='destinations.city')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='destinations', to='destinations.destinationcategory')),
            ],
            options={
                'ordering': ['-popularity_score', '-rating'],
            },
        ),
        migrations.CreateModel(
            name='DestinationImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image_url', models.URLField()),
                ('caption', models.CharField(blank=True, max_length=200)),
                ('is_primary', models.BooleanField(default=False)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('destination', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='destinations.destination')),
            ],
        ),
        migrations.CreateModel(
            name='DestinationReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reviewer_name', models.CharField(max_length=100)),
                ('rating', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('comment', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('destination', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='destinations.destination')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
