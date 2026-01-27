import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta

from .models import User, GameSession, Investment
from .forms import SignupForm, LoginForm
# gemini_service에서 함수들 임포트
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
            login(request, user)  # 회원가입 후 자동 로그인
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
    
    # 최근 게임 기록 조회 (완료된 게임만)
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
    
    # 로그인한 유저의 진행 중인 게임 확인
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
    # 기존 진행 중인 게임이 있으면 그 게임으로 이동
    active_session = GameSession.objects.filter(
        user=request.user,
        is_finished=False
    ).first()
    
    if active_session:
        return redirect('game:play', session_id=active_session.pk)
    
    # 새 게임 세션 생성 (초기자본 1억 = 10000만원, 기회 5회)
    session = GameSession.objects.create(
        user=request.user,
        current_capital=10000,
        remaining_chances=5
    )
    
    return redirect('game:play', session_id=session.pk)


@login_required
def play_view(request, session_id):
    """투자 화면 - 캐릭터가 아이디어 제시"""
    session = get_object_or_404(GameSession, pk=session_id, user=request.user)
    
    # 게임 종료 체크
    if session.is_finished:
        return redirect('game:main')
    
    # 자본금 부족 체크 (2000만원 미만이면 게임 종료)
    if session.current_capital < 2000:
        session.is_finished = True
        session.final_profit_rate = session.calculate_profit_rate()
        session.save()
        
        # 유저 통계 업데이트 (최고 수익률 갱신 등)
        update_user_stats(request.user, session.final_profit_rate)
        
        return redirect('game:ranking')
    
    # 1. 랜덤 캐릭터 선택 (get_random_character가 가중치 적용)
    character = get_random_character()
    
    # 2. AI 아이디어 생성
    idea = generate_idea(character)
    
    # 3. 세션에 현재 캐릭터와 아이디어 임시 저장 (invest 단계에서 사용)
    request.session['current_character'] = character
    request.session['current_idea'] = idea
    
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
            # 최소 투자금 미달 (올인 제외)
            return redirect('game:play', session_id=session_id)
        
        if invest_amount > session.current_capital:
            # 보유금 초과
            return redirect('game:play', session_id=session_id)
        
        # 세션에서 저장된 캐릭터/아이디어 불러오기
        character = request.session.get('current_character', {})
        idea = request.session.get('current_idea', {})
        
        # 캐릭터 정보가 없으면 다시 플레이 화면으로
        if not character:
            return redirect('game:play', session_id=session_id)
        
        # ========================================================
        # [수정] 캐릭터별 확률 및 수익률 로직 적용
        # ========================================================
        
        # 1. 성공 확률 가져오기 (기본값 0.5)
        success_prob = character.get('success_rate', 0.5)
        
        # 2. 성공 여부 판정 (True/False)
        is_success = random.random() < success_prob
        
        if is_success:
            # 성공 시: 캐릭터별 min_roi ~ max_roi 사이의 랜덤 수익률 (무조건 이득)
            min_roi = character.get('min_roi', 10)
            max_roi = character.get('max_roi', 50)
            
            # 랜덤 범위 수익률 적용
            profit_rate = random.randint(min_roi, max_roi)
            profit = int(invest_amount * (profit_rate / 100))
            session.current_capital += profit
        else:
            # 실패 시: 전액 손실
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
            # [수정된 부분] success_prob(실수)가 아니라 is_success(불리언)를 저장해야 함
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
        
        # 결과 화면으로 이동
        return redirect('game:result', investment_id=investment.pk)
    
    return redirect('game:play', session_id=session_id)


@login_required
def pass_view(request, session_id):
    """패스 - 기회 차감 없이 다음 캐릭터"""
    # 단순 리다이렉트만 하면 play_view에서 새로운 캐릭터를 뽑음
    return redirect('game:play', session_id=session_id)


@login_required
def result_view(request, investment_id):
    """결과 화면"""
    investment = get_object_or_404(Investment, pk=investment_id)
    session = investment.session
    
    # 본인 게임인지 확인
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