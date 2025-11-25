from django.db import models


class Rome(models.Model):
    updated_at = models.DateTimeField(auto_now=True)
    code = models.CharField(verbose_name="code ROME", max_length=5, primary_key=True)
    name = models.CharField(verbose_name="nom", max_length=255, db_index=True)

    class Meta:
        verbose_name = "ROME"
        verbose_name_plural = "ROME"

    def __str__(self):
        return f"{self.name} ({self.code})"


class Appellation(models.Model):
    updated_at = models.DateTimeField(auto_now=True)
    code = models.CharField(verbose_name="code", max_length=6, primary_key=True)
    name = models.CharField(verbose_name="nom", max_length=255, db_index=True)
    rome = models.ForeignKey(Rome, on_delete=models.CASCADE, null=True, related_name="appellations")
    sectors = models.ManyToManyField(
        "sectors.Sector",
        verbose_name="Secteurs d'activité",
        related_name="appellations",
        blank=True,
        help_text="Secteurs d'activité concernés par ce poste",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
