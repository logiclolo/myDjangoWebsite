# -*- coding: utf-8 -*-
from django import forms
from django.forms import ModelForm
from .models import VivoCgiRule 

#class DocumentForm(forms.Form):
    #docfile = forms.FileField(
        #label='Select a file',
        #help_text='max. 42 megabytes'
    #)

class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()

class ModelFormWithFileField(ModelForm):
    class Meta:
        model = VivoCgiRule 
        fields = ['apiversion', 'rulefile']
        labels = {
            'apiversion': 'http api version:',
            'rulefile': 'Rule file:'
        }
        help_texts = {
            'rulefile': '...it should be a JSON format'
        }
        error_messages = {
            'apiversion': {
                'max_length': "This name is too long."
            },
        }
