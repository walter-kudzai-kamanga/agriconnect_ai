TRANSLATIONS = {
    'en': {
        'welcome': 'Welcome to AgriConnect USSD',
        'select_product': 'Select product to transport:',
        'enter_quantity': 'Enter quantity:',
        'booking_confirmed': 'Booking confirmed!',
        'tracking_started': 'GPS tracking started',
        'milestone_reached': 'Milestone reached',
        'price_forecast': 'Price Forecast',
        'spoilage_risk': 'Spoilage Risk',
        'market_insights': 'Market Insights',
        'active_trackings': 'Active Trackings',
        'offline_requests': 'Offline Requests',
    },
    'sn': {  # Shona
        'welcome': 'Mauya kuAgriConnect USSD',
        'select_product': 'Sarudza chigadzirwa chekutakura:',
        'enter_quantity': 'Pinda huwandu:',
        'booking_confirmed': 'Kubhuka kwakasimbiswa!',
        'tracking_started': 'GPS tracking yatanga',
        'milestone_reached': 'Milestone yasvikwa',
        'price_forecast': 'Kufanotaura kwemitengo',
        'spoilage_risk': 'Njodzi yekuora',
        'market_insights': 'Zvinoonekwa zvemusika',
        'active_trackings': 'Tracking dziri kushanda',
        'offline_requests': 'Zvikumbiro zveoffline',
    },
    'nd': {  # Ndebele
        'welcome': 'Siyakwamukela kuAgriConnect USSD',
        'select_product': 'Khetha umkhiqizo wokuthutha:',
        'enter_quantity': 'Faka inani:',
        'booking_confirmed': 'Ukubhuka kuqinisekisiwe!',
        'tracking_started': 'GPS tracking iqalile',
        'milestone_reached': 'Milestone ifinyelelwe',
        'price_forecast': 'Ukubikezelwa kwentengo',
        'spoilage_risk': 'Ingozi yokubola',
        'market_insights': 'Ukubona kwemakethe',
        'active_trackings': 'Ukulandelela okuyisebenzayo',
        'offline_requests': 'Izicelo ezingaxhunyiwe',
    }
}

class TranslationService:
    """Service for multi-language support"""
    
    def __init__(self, default_lang: str = 'en'):
        self.default_lang = default_lang
        self.translations = TRANSLATIONS
    
    def translate(self, key: str, lang: str = None) -> str:
        """Get translation for key"""
        lang = lang or self.default_lang
        return self.translations.get(lang, self.translations['en']).get(
            key, 
            self.translations['en'].get(key, key)
        )
    
    def format_message(self, template_key: str, lang: str, **kwargs) -> str:
        """Format message with variables"""
        template = self.translate(template_key, lang)
        return template.format(**kwargs)

# Global instance
translator = TranslationService()

