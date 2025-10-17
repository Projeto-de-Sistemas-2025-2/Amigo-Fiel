from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q, Max, Count
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from django.templatetags.static import static

from .models import Conversation, Message

User = get_user_model()


def get_user_display_info(user):
    """Retorna informações de exibição do usuário (nome, avatar, tipo)"""
    info = {
        'username': user.username,
        'name': user.username,
        'avatar_url': static('img/defaults/avatar_comum.png'),
        'type': 'comum',
        'location': None,
    }
    
    if hasattr(user, 'perfil_empresa') and user.perfil_empresa:
        perfil = user.perfil_empresa
        info['name'] = perfil.razao_social
        info['type'] = 'empresa'
        info['location'] = perfil.cidade if perfil.cidade else None
        if perfil.foto:
            info['avatar_url'] = perfil.foto.url
        else:
            info['avatar_url'] = static('img/defaults/avatar_empresa.png')
    elif hasattr(user, 'perfil_ong') and user.perfil_ong:
        perfil = user.perfil_ong
        info['name'] = perfil.nome_fantasia
        info['type'] = 'ong'
        info['location'] = perfil.cidade if perfil.cidade else None
        if perfil.foto:
            info['avatar_url'] = perfil.foto.url
        else:
            info['avatar_url'] = static('img/defaults/avatar_ong.png')
    elif hasattr(user, 'perfil_comum') and user.perfil_comum:
        perfil = user.perfil_comum
        # UsuarioComum não tem nome_completo, usa apenas username
        info['name'] = user.username
        info['type'] = 'comum'
        info['location'] = perfil.cidade if perfil.cidade else None
        if perfil.foto:
            info['avatar_url'] = perfil.foto.url
    
    return info


@login_required
def inbox(request):
    # Obter filtros da query string
    filter_type = request.GET.get('type', 'all')  # all, empresa, ong, comum
    filter_status = request.GET.get('status', 'all')  # all, unread, read
    search_query = request.GET.get('q', '').strip()
    
    conversations = (Conversation.objects
                    .filter(Q(user_a=request.user) | Q(user_b=request.user))
                    .annotate(last_ts=Max('messages__created_at'))
                    .prefetch_related('messages')
                    .order_by('-last_ts', '-last_message_at', '-updated_at'))
    
    # Preparar dados para o template
    threads = []
    for conv in conversations:
        other_user = conv.other_of(request.user)
        other_info = get_user_display_info(other_user)
        
        # Última mensagem
        last_msg = conv.messages.order_by('-created_at').first()
        
        # Contar mensagens não lidas
        unread_count = conv.messages.filter(
            read_at__isnull=True
        ).exclude(sender=request.user).count()
        
        thread_data = {
            'id': conv.id,
            'other_username': other_user.username,
            'other_name': other_info['name'],
            'other_avatar_url': other_info['avatar_url'],
            'other_type': other_info['type'],
            'other_location': other_info['location'],
            'last_message': last_msg,
            'updated_at': conv.last_message_at or conv.updated_at,
            'unread_count': unread_count,
        }
        
        # Aplicar filtro por tipo
        if filter_type != 'all' and other_info['type'] != filter_type:
            continue
        
        # Aplicar filtro por status (não lidas/lidas)
        if filter_status == 'unread' and unread_count == 0:
            continue
        elif filter_status == 'read' and unread_count > 0:
            continue
        
        # Aplicar busca por nome/username
        if search_query:
            if (search_query.lower() not in other_info['name'].lower() and 
                search_query.lower() not in other_user.username.lower()):
                continue
        
        threads.append(thread_data)
    
    # Estatísticas para badges
    total_threads = len(threads)
    total_unread = sum(1 for t in threads if t['unread_count'] > 0)
    
    context = {
        'threads': threads,
        'filter_type': filter_type,
        'filter_status': filter_status,
        'search_query': search_query,
        'total_threads': total_threads,
        'total_unread': total_unread,
    }
    
    return render(request, 'chat/inbox.html', context)


@login_required
def thread_by_username(request, username):
    if username == request.user.username:
        raise Http404("Não é possível conversar consigo mesmo.")
    other = get_object_or_404(User, username=username)
    other_info = get_user_display_info(other)
    conv = Conversation.for_users(request.user, other)

    # enviar mensagem
    if request.method == 'POST':
        text = (request.POST.get('text') or '').strip()
        if text:
            msg = Message.objects.create(conversation=conv, sender=request.user, text=text)
            conv.last_message_at = msg.created_at
            conv.save(update_fields=['last_message_at'])
        return redirect('chat:thread-by-username', username=other.username)

    # marcar mensagens recebidas como lidas
    (conv.messages
         .filter(read_at__isnull=True)
         .exclude(sender=request.user)
         .update(read_at=now()))

    messages = conv.messages.select_related('sender')
    return render(request, 'chat/thread.html', {
        'conversation': conv,
        'messages': messages,
        'other': other,
        'other_info': other_info,
    })


@login_required
def api_thread_since(request, username):
    """Endpoint simples para polling: retorna mensagens novas desde ?since=ISO"""
    other = get_object_or_404(User, username=username)
    conv = Conversation.for_users(request.user, other)

    since_str = request.GET.get('since')
    since_dt = parse_datetime(since_str) if since_str else None

    msgs = conv.messages.select_related('sender')
    if since_dt:
        msgs = msgs.filter(created_at__gt=since_dt)

    data = [{
        'id': m.id,
        'sender': m.sender.username,
        'text': m.text,
        'created_at': m.created_at.isoformat()
    } for m in msgs]

    # marca como lidas as recebidas
    (conv.messages
         .filter(read_at__isnull=True)
         .exclude(sender=request.user)
         .update(read_at=now()))

    return JsonResponse({'messages': data})
