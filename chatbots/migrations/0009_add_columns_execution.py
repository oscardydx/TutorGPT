# Generated by Django 5.0.10 on 2025-03-15 21:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chatbots", "0008_models_api"),
    ]

    operations = [
   
        migrations.AddField(
            model_name="executionmodeltime",
            name="good_feedback",
            field=models.BooleanField(blank=True, null=True),
        ),    
        migrations.AddField(
            model_name="executionmodeltime",
            name="bug_report",
            field=models.BooleanField(blank=True, null=True),
        ),
    ]
 
              