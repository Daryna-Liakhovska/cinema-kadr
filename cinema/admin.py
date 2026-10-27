from django.contrib import admin

from .models import Director, Genre, Hall, Movie, Session

admin.site.register(Genre)
admin.site.register(Director)
admin.site.register(Movie)
admin.site.register(Hall)
admin.site.register(Session)
