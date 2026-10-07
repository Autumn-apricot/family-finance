from django.contrib import admin

from finance.models import AiChatHistory, Budget, Category, Expense, SystemConfig, User
from finance.models_voice import CategoryKeyword, VoiceParseLog

admin.site.register(User)
admin.site.register(Category)
admin.site.register(Expense)
admin.site.register(Budget)
admin.site.register(AiChatHistory)
admin.site.register(SystemConfig)
admin.site.register(CategoryKeyword)
admin.site.register(VoiceParseLog)
