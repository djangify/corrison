# forms.py
from django import forms
from .models import BlogPost
from markdownx.widgets import MarkdownxWidget

class BlogPostForm(forms.ModelForm):
    # Use MarkdownX’s two-pane editor
    content = forms.CharField(widget=MarkdownxWidget())

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
