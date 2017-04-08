from django.shortcuts import render


def render_themed(request, view_type, context):
    theme = request.theme
    context.update({
        'tpl_head': '_head%s.html' % theme,
        'tpl_realm': '%s%s.html' % (view_type, theme)
    })
    return render(request, '%s.html' % view_type, context)
