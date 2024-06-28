from django.db import models


class UserGuide(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class GuideStep(models.Model):
    guide = models.ForeignKey(UserGuide, related_name="steps", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    text = models.TextField()
    element = models.CharField(max_length=200)
    position = models.CharField(
        max_length=50, choices=[("top", "Top"), ("bottom", "Bottom"), ("left", "Left"), ("right", "Right")]
    )

    def __str__(self):
        return self.title
