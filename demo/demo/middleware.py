from django.utils.translation import activate


def language_activator(get_response):

    def middleware(request):

        lang = request.GET.get('lang', 'en')
        activate(lang)

        request.lang = lang

        return get_response(request)

    return middleware


def theme_activator(get_response):

    def middleware(request):

        theme = request.GET.get('theme', 'none')
        if theme:
            theme = '_' + theme

        request.theme = theme

        return get_response(request)

    return middleware
