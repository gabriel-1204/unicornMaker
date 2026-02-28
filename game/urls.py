from django.urls import path
from . import views

app_name = 'game'

urlpatterns = [
    path('', views.main_view, name='main'),

    # 게임
    path('game/start/', views.game_start_view, name='game_start'),
    path('game/<int:session_id>/play/', views.play_view, name='play'),
    path('game/<int:session_id>/invest/', views.invest_view, name='invest'),
    path('game/<int:session_id>/pass/', views.pass_view, name='pass'),
    path('result/<int:investment_id>/', views.result_view, name='result'),

    # 랭킹
    path('ranking/', views.ranking_view, name='ranking'),

    # 헬스체크 (슬립 방지)
    path('health/', views.health_check, name='health_check'),
]
