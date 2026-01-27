from django.contrib import admin
from .models import User, GameSession, Investment


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'nickname', 'best_profit_rate', 'total_games']
    search_fields = ['username', 'nickname']


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_capital', 'remaining_chances', 'is_finished', 'final_profit_rate', 'created_at']
    list_filter = ['is_finished', 'created_at']
    search_fields = ['user__nickname']


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ['session', 'character_name', 'idea_title', 'invest_amount', 'is_success', 'profit_rate']
    list_filter = ['is_success', 'character_name']
