# forms.py
from django import forms
from .models import BlogPost

class BlogPostForm(forms.ModelForm):
    
    content = forms.CharField()

    class Meta:
        model = BlogPost
        fields = [
            'title',
            'content',
            'featured_image',
            'youtube_url',
            'attachment',
            'is_featured',
        ]
        widgets = {
            'youtube_url': forms.URLInput(attrs={
                'class': 'border rounded w-full p-2',
                'placeholder': 'https://www.youtube.com/embed/…'
            }),
            'attachment': forms.ClearableFileInput(attrs={
                'class': 'border rounded w-full p-2'
            }),
        }
