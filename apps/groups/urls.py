from django.urls import path, include

from .views import *


urlpatterns = [
    path('', GroupViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('<int:pk>/', GroupViewSet.as_view({'get': 'retrieve', 'put': 'partial_update', 'delete': 'destroy'})),
    path('<int:pk>/invitelink/', GroupInviteLinkViewSet.as_view({'get': 'retrieve'})),

    path('<int:pk>/members/', GroupMembersViewSet.as_view({'get': 'list'})),
    path('<int:pk>/members/<int:member_id>/', GroupMembersViewSet.as_view({'put': 'partial_update'})),
    path('<int:pk>/members/banned/', GroupMembersViewSet.as_view({'get': 'ban_list'})),

    path('membership/', GroupMemberViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('membership/<int:pk>/', GroupMemberViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})),
]
