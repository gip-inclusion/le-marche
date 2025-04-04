from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.models import Page

from content_manager.models import ContentPage, Tag


class ArticleList(RoutablePageMixin, Page):
    def get_context(self, request, *args, **kwargs):
        context = super(ArticleList, self).get_context(request, *args, **kwargs)
        context["article_list"] = self.posts
        context["search_type"] = getattr(self, "search_type", "")
        context["search_term"] = getattr(self, "search_term", "")
        context["categories"] = (
            Tag.objects.filter(contentpage__in=ContentPage.objects.descendant_of(self).live())
            .annotate(usecount=Count("contentpage"))
            .filter(usecount__gte=1)
            .order_by("name")
        )

        return context

    def get_posts(self):
        return ContentPage.objects.descendant_of(self).live().prefetch_related("tags").order_by("-last_published_at")

    @route(r"^$")
    def post_list(self, request, *args, **kwargs):
        self.posts = self.get_posts()
        return self.render(
            request,
        )

    @route(r"^categories/(?P<cat_slug>[-\w]*)/$", name="category_view")
    def category_view(self, request, cat_slug, *args, **kwargs):
        """Find blog posts based on a category."""
        self.posts = self.get_posts()
        context = self.get_context(request)

        tag = get_object_or_404(Tag, slug=cat_slug)
        context["article_list"] = self.posts.filter(tags__in=[tag])
        context["category"] = tag
        return self.render(request, context_overrides=context)

    @route(r"^search/$")
    def post_search(self, request, *args, **kwargs):
        search_query = request.GET.get("q", None)
        self.posts = self.get_posts()
        if search_query:
            self.posts = self.posts.filter(
                Q(body__icontains=search_query) | Q(title__icontains=search_query) | Q(excerpt__icontains=search_query)
            )

        self.search_term = search_query
        self.search_type = "search"
        return self.render(
            request,
        )

    subpage_types = ["content_manager.ContentPage"]
