from django.db import models
from django.contrib.auth.models import AbstractUser


# ============================================================
# User 모델 (레거시 - 마이그레이션 호환용으로 유지)
# ============================================================
class User(AbstractUser):
    nickname = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='닉네임'
    )
    img_profile = models.ImageField(
        upload_to='profile/',
        blank=True,
        null=True,
        verbose_name='프로필 이미지'
    )
    best_profit_rate = models.FloatField(
        default=0.0,
        verbose_name='최고 수익률'
    )
    total_games = models.IntegerField(
        default=0,
        verbose_name='총 플레이 횟수'
    )

    def __str__(self):
        return self.nickname


# ============================================================
# GameSession 모델
# ============================================================
class GameSession(models.Model):
    """
    게임 한 판 (세션)
    - 닉네임 기반 (로그인 불필요)
    - 자본금 1억(10000만원), 기회 5회로 시작
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='game_sessions',
        verbose_name='플레이어',
        null=True,
        blank=True,
    )
    nickname = models.CharField(
        max_length=20,
        default='익명투자자',
        verbose_name='닉네임'
    )
    current_capital = models.BigIntegerField(
        default=10000,
        verbose_name='현재 자본금(만원)'
    )
    remaining_chances = models.IntegerField(
        default=5,
        verbose_name='남은 기회'
    )
    is_finished = models.BooleanField(
        default=False,
        verbose_name='종료 여부'
    )
    final_profit_rate = models.FloatField(
        null=True,
        blank=True,
        verbose_name='최종 수익률(%)'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='생성 시간'
    )
    remaining_reroles = models.IntegerField(
        default=5,
        verbose_name='남은 패스 횟수'
    )

    def __str__(self):
        return f"{self.nickname}의 게임 ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

    def calculate_profit_rate(self):
        """수익률 계산: (현재자본 - 10000) / 10000 * 100"""
        return (self.current_capital - 10000) / 10000 * 100


# ============================================================
# Investment 모델
# ============================================================
class Investment(models.Model):
    """
    투자 기록
    - 한 게임 세션 내 여러 투자 기록 저장
    """
    session = models.ForeignKey(
        GameSession,
        on_delete=models.CASCADE,
        related_name='investments',
        verbose_name='게임 세션'
    )
    character_name = models.CharField(
        max_length=20,
        verbose_name='캐릭터 이름'
    )
    idea_title = models.CharField(
        max_length=100,
        verbose_name='아이디어 제목'
    )
    idea_description = models.TextField(
        blank=True,
        verbose_name='아이디어 설명'
    )
    invest_amount = models.BigIntegerField(
        verbose_name='투자 금액(만원)'
    )
    is_success = models.BooleanField(
        verbose_name='성공 여부'
    )
    profit_rate = models.IntegerField(
        default=0,
        verbose_name='수익률(%)'
    )
    result_system_msg = models.TextField(
        blank=True,
        verbose_name='[SYSTEM] 메시지'
    )
    result_character_reaction = models.TextField(
        blank=True,
        verbose_name='[캐릭터] 반응'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='투자 시간'
    )

    def __str__(self):
        result = "성공" if self.is_success else "실패"
        return f"{self.character_name} - {self.idea_title} ({result})"
