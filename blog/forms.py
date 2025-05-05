from django import forms
from .models import BlogPost
from tinymce.widgets import TinyMCE

class BlogPostForm(forms.ModelForm):
    content = forms.CharField(widget=TinyMCE(attrs={'cols': 80, 'rows': 30}))
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