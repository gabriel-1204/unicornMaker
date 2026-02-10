import random
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import GameSession, Investment
from .gemini_service import generate_idea, generate_result, get_random_character


# ============================================================
# 확률 → 단계 변환 함수
# ============================================================
def get_prob_level(prob):
    percent = prob * 100
    if percent >= 100:
        return {'text': '확정', 'class': 'prob-perfect'}
    elif percent >= 81:
        return {'text': '훌륭', 'class': 'prob-great'}
    elif percent >= 61:
        return {'text': '좋음', 'class': 'prob-good'}
    elif percent >= 41:
        return {'text': '보통', 'class': 'prob-normal'}
    elif percent >= 21:
        return {'text': '낮음', 'class': 'prob-low'}
    else:
        return {'text': '최악', 'class': 'prob-worst'}


# ============================================================
# 메인 페이지
# ============================================================
def main_view(request):
    top3 = get_top3()
    nickname = request.session.get('player_nickname', '')

    active_session = None
    if nickname:
        active_session = GameSession.objects.filter(
            nickname=nickname,
            is_finished=False
        ).first()

    context = {
        'top3': top3,
        'active_session': active_session,
        'nickname': nickname,
    }
    return render(request, 'game/main.html', context)


# ============================================================
# 게임 시작 (닉네임 입력 → 세션 생성)
# ============================================================
def game_start_view(request):
    if request.method == 'POST':
        nickname = request.POST.get('nickname', '').strip()
        if not nickname:
            nickname = '익명투자자'
        if len(nickname) > 20:
            nickname = nickname[:20]

        request.session['player_nickname'] = nickname

        active_session = GameSession.objects.filter(
            nickname=nickname,
            is_finished=False
        ).first()

        if active_session:
            return redirect('game:play', session_id=active_session.pk)

        session = GameSession.objects.create(
            nickname=nickname,
            current_capital=10000,
            remaining_chances=5
        )
        return redirect('game:play', session_id=session.pk)

    return redirect('game:main')


# ============================================================
# 투자 화면
# ============================================================
def play_view(request, session_id):
    session = get_object_or_404(GameSession, pk=session_id)

    if session.is_finished:
        return redirect('game:main')

    if session.current_capital <= 0:
        session.is_finished = True
        session.final_profit_rate = session.calculate_profit_rate()
        session.save()
        return redirect('game:ranking')

    character = request.session.get('current_character')
    idea = request.session.get('current_idea')

    if not character or not idea:
        character = get_random_character()
        idea = generate_idea(character)
        request.session['current_character'] = character
        request.session['current_idea'] = idea
        success_prob = character.get('success_rate', 0.5)
        request.session['success_prob'] = success_prob
        request.session['enchant_used'] = False
    else:
        success_prob = request.session.get('success_prob', 0.5)

    prob_level = get_prob_level(success_prob)
    enchant_used = request.session.get('enchant_used', False)
    can_enchant = not enchant_used and session.current_capital >= 2000

    context = {
        'session': session,
        'character': character,
        'idea': idea,
        'prob_text': prob_level['text'],
        'prob_class': prob_level['class'],
        'can_enchant': can_enchant,
        'enchant_used': enchant_used,
    }
    return render(request, 'game/play.html', context)


# ============================================================
# 투자 처리
# ============================================================
def invest_view(request, session_id):
    session = get_object_or_404(GameSession, pk=session_id)

    if session.is_finished:
        return redirect('game:main')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'invest':
            try:
                invest_amount = int(request.POST.get('amount', 0))
            except ValueError:
                return redirect('game:play', session_id=session_id)

            if invest_amount < 2000 and invest_amount != session.current_capital:
                return redirect('game:play', session_id=session_id)
            if invest_amount > session.current_capital:
                return redirect('game:play', session_id=session_id)

            character = request.session.get('current_character', {})
            idea = request.session.get('current_idea', {})

            if not character:
                return redirect('game:play', session_id=session_id)

            success_prob = request.session.get('success_prob', 0.5)
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

            result = generate_result(character, idea.get('title', '무제'), is_success)

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

            session.remaining_chances -= 1
            if session.remaining_chances <= 0 or session.current_capital <= 0:
                session.is_finished = True
                session.final_profit_rate = session.calculate_profit_rate()
            session.save()

            request.session.pop('current_character', None)
            request.session.pop('current_idea', None)
            request.session.pop('success_prob', None)
            request.session.pop('enchant_used', None)

            return redirect('game:result', investment_id=investment.pk)

        elif action == 'enchant':
            enchant_used = request.session.get('enchant_used', False)
            if enchant_used:
                return redirect('game:play', session_id=session_id)
            if session.current_capital < 2000:
                return redirect('game:play', session_id=session_id)

            session.current_capital -= 2000
            session.save()

            prob_add = random.randint(10, 50) / 100
            success_prob = request.session.get('success_prob', 0.5)
            success_prob = min(1.0, success_prob + prob_add)

            request.session['success_prob'] = success_prob
            request.session['enchant_used'] = True

            return redirect('game:play', session_id=session_id)

    return redirect('game:play', session_id=session_id)


# ============================================================
# 패스
# ============================================================
def pass_view(request, session_id):
    session = get_object_or_404(GameSession, pk=session_id)
    if session.remaining_reroles > 0:
        session.remaining_reroles -= 1
        session.save()
        request.session.pop('current_character', None)
        request.session.pop('current_idea', None)
        request.session.pop('success_prob', None)
        request.session.pop('enchant_used', None)
    return redirect('game:play', session_id=session_id)


# ============================================================
# 결과 화면
# ============================================================
def result_view(request, investment_id):
    investment = get_object_or_404(Investment, pk=investment_id)
    session = investment.session

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
# 랭킹
# ============================================================
def ranking_view(request):
    today_ranking = get_today_ranking()
    hall_of_fame = get_hall_of_fame()

    context = {
        'today_ranking': today_ranking,
        'hall_of_fame': hall_of_fame,
    }
    return render(request, 'game/ranking.html', context)


def get_today_ranking():
    today = timezone.now().date()
    return GameSession.objects.filter(
        is_finished=True,
        created_at__date=today
    ).order_by('-final_profit_rate')[:20]


def get_top3():
    today = timezone.now().date()
    return GameSession.objects.filter(
        is_finished=True,
        created_at__date=today
    ).order_by('-final_profit_rate')[:3]


def get_hall_of_fame():
    return GameSession.objects.filter(
        is_finished=True
    ).order_by('-final_profit_rate')[:10]
