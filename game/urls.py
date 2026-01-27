from django.urls import path
from . import views

app_name = 'game'

urlpatterns = [
    # 메인
    path('', views.main_view, name='main'),
    
    # 회원 (유동주)
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('mypage/', views.mypage_view, name='mypage'),
    
    # 게임 (박기상)
    path('game/start/', views.game_start_view, name='game_start'),
    path('game/<int:session_id>/play/', views.play_view, name='play'),
    path('game/<int:session_id>/invest/', views.invest_view, name='invest'),
    path('game/<int:session_id>/pass/', views.pass_view, name='pass'),
    path('result/<int:investment_id>/', views.result_view, name='result'),
    
    # 랭킹 (김정원)
    path('ranking/', views.ranking_view, name='ranking'),
]
