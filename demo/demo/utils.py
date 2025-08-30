from django.shortcuts import render


def render_themed(request, view_type, context):
    theme = request.theme
    context.update({
        'tpl_head': f'_head{theme}.html',
        'tpl_realm': f'{view_type}{theme}.html'
    })
    return render(request, f'{view_type}.html', context)
