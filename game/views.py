import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta

from .models import User, GameSession, Investment
from .forms import SignupForm, LoginForm
from .gemini_service import generate_idea, generate_result, get_random_character


# ============================================================
# 회원 시스템 (유동주 담당)
# ============================================================

def signup_view(request):
    """회원가입"""
    if request.method == 'POST':
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('game:main')
    else:
        form = SignupForm()
    
    return render(request, 'game/signup.html', {'form': form})


def login_view(request):
    """로그인"""
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('game:main')
    else:
        form = LoginForm()
    
    return render(request, 'game/login.html', {'form': form})


def logout_view(request):
    """로그아웃"""
    logout(request)
    return redirect('game:main')


@login_required
def mypage_view(request):
    """마이페이지"""
    user = request.user
    
    recent_games = GameSession.objects.filter(
        user=user,
        is_finished=True
    ).order_by('-created_at')[:10]
    
    context = {
        'user': user,
        'recent_games': recent_games,
    }
    return render(request, 'game/mypage.html', context)


# ============================================================
# 게임 로직 (박기상 담당)
# ============================================================

def main_view(request):
    """메인 페이지"""
    top3 = get_top3()
    
    context = {
        'top3': top3,
    }
    
    if request.user.is_authenticated:
        active_session = GameSession.objects.filter(
            user=request.user,
            is_finished=False
        ).first()
        context['active_session'] = active_session
    
    return render(request, 'game/main.html', context)


@login_required
def game_start_view(request):
    """게임 시작 - 새 세션 생성"""
    active_session = GameSession.objects.filter(
        user=request.user,
        is_finished=False
    ).first()
    
    if active_session:
        return redirect('game:play', session_id=active_session.pk)

    session = GameSession.objects.create(
        user=request.user,
        current_capital=10000,
        remaining_chances=5
    )
    
    return redirect('game:play', session_id=session.pk)


@login_required
def play_view(request, session_id):
    """투자 화면"""
    session = get_object_or_404(GameSession, pk=session_id, user=request.user)
    
    # 게임 종료 체크
    if session.is_finished:
        return redirect('game:main')
    
    # 자본금 부족 체크 (0원 이하면 게임 종료)
    if session.current_capital <= 0:
        session.is_finished = True
        session.final_profit_rate = session.calculate_profit_rate()
        session.save()
        update_user_stats(request.user, session.final_profit_rate)
        return redirect('game:ranking')
    
    # ========== 새로고침 방지 ==========
    # 세션에 저장된 캐릭터/아이디어가 있으면 재사용
    character = request.session.get('current_character')
    idea = request.session.get('current_idea')
    
    # 없을 때만 새로 생성
    if not character or not idea:
        character = get_random_character()
        idea = generate_idea(character)
        request.session['current_character'] = character
        request.session['current_idea'] = idea
    # ==================================
    
    context = {
        'session': session,
        'character': character,
        'idea': idea,
    }
    return render(request, 'game/play.html', context)


@login_required
def invest_view(request, session_id):
    """투자 처리"""
    session = get_object_or_404(GameSession, pk=session_id, user=request.user)
    
    if request.method == 'POST':
        try:
            invest_amount = int(request.POST.get('amount', 0))
        except ValueError:
            return redirect('game:play', session_id=session_id)
        
        # 투자금 검증 로직
        if invest_amount < 2000 and invest_amount != session.current_capital:
            return redirect('game:play', session_id=session_id)
        
        if invest_amount > session.current_capital:
            return redirect('game:play', session_id=session_id)
        
        # 세션에서 저장된 캐릭터/아이디어 불러오기
        character = request.session.get('current_character', {})
        idea = request.session.get('current_idea', {})
        
        if not character:
            return redirect('game:play', session_id=session_id)
        
        # 캐릭터별 확률 및 수익률 로직
        success_prob = character.get('success_rate', 0.5)
        is_success = random.random() < success_prob
        
        if is_success:
            min_roi = character.get('min_roi', 10)
            max_roi = character.get('max_roi', 50)
            profit_rate = random.randint(min_roi, max_roi)
            profit = int(invest_amount * (profit_rate / 100))
            session.current_capital += profit
        else:
            profit_rate = -100
            session.current_capital -= invest_amount
        
        # AI 결과 메시지 생성
        result = generate_result(character, idea.get('title', '무제'), is_success)
        
        # 투자 기록 저장
        investment = Investment.objects.create(
            session=session,
            character_name=character.get('name', '알 수 없음'),
            idea_title=idea.get('title', '제목 없음'),
            idea_description=idea.get('description', ''),
            invest_amount=invest_amount,
            is_success=is_success,
            profit_rate=profit_rate,
            result_system_msg=result.get('system_msg', ''),
            result_character_reaction=result.get('reaction', '')
        )
        
        # 기회 차감
        session.remaining_chances -= 1
        
        # 게임 종료 조건 체크
        if session.remaining_chances <= 0 or session.current_capital <= 0:
            session.is_finished = True
            session.final_profit_rate = session.calculate_profit_rate()
            session.save()
            update_user_stats(request.user, session.final_profit_rate)
        else:
            session.save()
        
        # 세션 데이터 삭제 (다음 턴에 새 캐릭터 나오게)
        request.session.pop('current_character', None)
        request.session.pop('current_idea', None)

        return redirect('game:result', investment_id=investment.pk)
    
    return redirect('game:play', session_id=session_id)


@login_required
def pass_view(request, session_id):
    """패스 - 기회 차감 없이 다음 캐릭터"""
    # 세션 데이터 삭제 (새 캐릭터 나오게)
    request.session.pop('current_character', None)
    request.session.pop('current_idea', None)
    return redirect('game:play', session_id=session_id)


@login_required
def result_view(request, investment_id):
    """결과 화면"""
    investment = get_object_or_404(Investment, pk=investment_id)
    session = investment.session
    
    if session.user != request.user:
        return redirect('game:main')
    
    # 캐릭터 이름 → 키 매핑 (이미지 파일명용)
    name_to_key = {
        '김잼민': 'jaemin',
        '성수동': 'hipster',
        '유능한': 'elite',
        '공필태(G.P.T)': 'ai_fan',
        '왕소심': 'shy',
    }
    character_key = name_to_key.get(investment.character_name, 'jaemin')
    
    context = {
        'investment': investment,
        'session': session,
        'character_key': character_key,
    }
    return render(request, 'game/result.html', context)


# ============================================================
# 랭킹 및 유틸리티 (김정원 담당)
# ============================================================

def ranking_view(request):
    """랭킹 페이지"""
    today_ranking = get_today_ranking()
    hall_of_fame = get_hall_of_fame()
    
    context = {
        'today_ranking': today_ranking,
        'hall_of_fame': hall_of_fame,
    }
    return render(request, 'game/ranking.html', context)


def get_today_ranking():
    """오늘의 랭킹 조회"""
    today = timezone.now().date()
    ranking = GameSession.objects.filter(
        is_finished=True,
        created_at__date=today
    ).order_by('-final_profit_rate')[:20]
    return ranking


def get_top3():
    """메인 페이지용 Top 3"""
    today = timezone.now().date()
    top3 = GameSession.objects.filter(
        is_finished=True,
        created_at__date=today
    ).order_by('-final_profit_rate')[:3]
    return top3


def get_hall_of_fame():
    """명예의 전당 - 역대 Top 10"""
    hall_of_fame = GameSession.objects.filter(
        is_finished=True
    ).order_by('-final_profit_rate')[:10]
    return hall_of_fame


def update_user_stats(user, profit_rate):
    """유저 통계 업데이트 (게임 종료 시 호출)"""
    user.total_games += 1
    if profit_rate > user.best_profit_rate:
        user.best_profit_rate = profit_rate
    user.save()