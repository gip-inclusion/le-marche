import logging
from django.shortcuts import render

logger = logging.getLogger(__name__)


def home(request, template_name="home/home.html"):
    context = {}
    return render(request, template_name, context)
