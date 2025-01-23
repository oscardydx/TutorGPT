from django.core.management.base import BaseCommand
from chatbots.telegram_bot import main  # Importa tu script del bot

class Command(BaseCommand):
    help = "Inicia el bot de Telegram"

    def handle(self, *args, **kwargs):
        main()