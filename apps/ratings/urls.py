# apps/ratings/urls.py

from django.urls import path
from . import views

app_name = 'ratings'

urlpatterns = [
    # Rating URLs
    path('movie/<slug:movie_slug>/rate/',
         views.add_or_update_rating,
         name='add_or_update_rating'),
    path('rating/<int:rating_id>/delete/',
         views.delete_rating,
         name='delete_rating'),

    # Comment URLs
    path('movie/<slug:movie_slug>/comment/',
         views.add_or_update_comment,
         name='add_or_update_comment'),
    path('comment/<int:comment_id>/delete/',
         views.delete_comment,
         name='delete_comment'),

    # User ratings list
    path('my-ratings/',
         views.UserRatingsListView.as_view(),
         name='my_ratings'),
]
