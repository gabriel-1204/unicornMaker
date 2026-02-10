from django.contrib import admin
from .models import GameSession, Investment


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['nickname', 'current_capital', 'remaining_chances', 'is_finished', 'final_profit_rate', 'created_at']
    list_filter = ['is_finished', 'created_at']
    search_fields = ['nickname']


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ['session', 'character_name', 'idea_title', 'invest_amount', 'is_success', 'profit_rate']
    list_filter = ['is_success', 'character_name']
