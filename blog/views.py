from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import BlogCategory, BlogPost
from .serializers import BlogCategorySerializer, BlogPostSerializer

# Frontend views
def blog_list(request):
    """
    Blog listing view.
    """
    # Get query parameters
    category_slug = request.GET.get('category')
    search_query = request.GET.get('q')
    page = request.GET.get('page', 1)
    
    # Base queryset - only show published posts
    posts = BlogPost.objects.filter(status='published')
    
    # Filter by category if provided
    if category_slug:
        category = get_object_or_404(BlogCategory, slug=category_slug)
        posts = posts.filter(category=category)
    
    # Filter by search query if provided
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) | 
            Q(content__icontains=search_query) |
            Q(meta_keywords__icontains=search_query)
        )
    
    # Get featured posts for slider
    featured_posts = BlogPost.objects.filter(status='published', is_featured=True).order_by('-published_at')[:5]
    
    # Paginate results
    paginator = Paginator(posts, 10)  # Show 10 posts per page
    page_obj = paginator.get_page(page)
    
    # Get all categories for sidebar
    categories = BlogCategory.objects.all()
    
    context = {
        'featured_posts': featured_posts,
        'all_posts': page_obj,
        'categories': categories,
        'category_slug': category_slug,
        'search_query': search_query,
    }
    
    return render(request, 'blog/blog_list.html', context)

def blog_detail(request, slug):
    """
    Blog detail view.
    """
    post = get_object_or_404(BlogPost, slug=slug, status='published')
    
    # Get related posts from same category
    related_posts = []
    if post.category:
        related_posts = BlogPost.objects.filter(
            status='published', 
            category=post.category
        ).exclude(id=post.id).order_by('-published_at')[:3]
    
    # Get recent posts for sidebar
    recent_posts = BlogPost.objects.filter(
        status='published'
    ).exclude(id=post.id).order_by('-published_at')[:5]
    
    context = {
        'post': post,
        'related_posts': related_posts,
        'recent_posts': recent_posts,
    }
    
    return render(request, 'blog/blog_detail.html', context)

def category_list(request):
    """
    Category listing view.
    """
    categories = BlogCategory.objects.all()
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'blog/category_list.html', context)

def category_detail(request, slug):
    """
    Category detail view.
    """
    category = get_object_or_404(BlogCategory, slug=slug)
    posts = BlogPost.objects.filter(category=category, status='published')
    
    # Paginate results
    page = request.GET.get('page', 1)
    paginator = Paginator(posts, 10)  # Show 10 posts per page
    page_obj = paginator.get_page(page)
    
    context = {
        'category': category,
        'posts': page_obj,
    }
    
    return render(request, 'blog/category_detail.html', context)

# API viewsets
class BlogCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for blog categories.
    """
    queryset = BlogCategory.objects.all()
    serializer_class = BlogCategorySerializer
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

class BlogPostViewSet(viewsets.ModelViewSet):
    """
    API endpoint for blog posts.
    """
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'content', 'meta_keywords']
    
    def get_queryset(self):
        """
        Filter queryset based on query parameters.
        """
        queryset = BlogPost.objects.all().order_by('-published_at', '-created_at')
        
        # Filter by status if provided in query params
        status = self.request.query_params.get('status', None)
        if status == 'published':
            queryset = queryset.filter(status='published')
        
        # Filter by category slug if provided
        category_slug = self.request.query_params.get('category', None)
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filter by featured flag if provided
        featured = self.request.query_params.get('featured', None)
        if featured == 'true':
            queryset = queryset.filter(is_featured=True)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Get featured posts.
        """
        featured_posts = BlogPost.objects.filter(status='published', is_featured=True).order_by('-published_at')[:5]
        serializer = self.get_serializer(featured_posts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get recent posts.
        """
        recent_posts = BlogPost.objects.filter(status='published').order_by('-published_at')[:10]
        serializer = self.get_serializer(recent_posts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def related(self, request, slug=None):
        """
        Get related posts for a specific post.
        """
        post = self.get_object()
        if post.category:
            related_posts = BlogPost.objects.filter(
                status='published',
                category=post.category
            ).exclude(id=post.id).order_by('-published_at')[:3]
            
            serializer = self.get_serializer(related_posts, many=True)
            return Response(serializer.data)
        
        return Response([])
    