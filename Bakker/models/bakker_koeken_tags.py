from django.db import models

class Bakker(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class KoekenTag(models.Model):
    bakker = models.ForeignKey(Bakker, on_delete=models.CASCADE, related_name='koeken_tags')
    tag_name = models.CharField(max_length=100)

    def __str__(self):
        return self.tag_name