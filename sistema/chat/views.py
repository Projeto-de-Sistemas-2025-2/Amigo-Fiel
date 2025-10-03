from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q, Max
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now

from .models import Conversation, Message

User = get_user_model()

@login_required
def inbox(request):
    qs = (Conversation.objects
          .filter(Q(user_a=request.user) | Q(user_b=request.user))
          .annotate(last_ts=Max('messages__created_at'))
          .order_by('-last_ts', '-last_message_at', '-updated_at'))
    return render(request, 'chat/inbox.html', {'conversations': qs})


@login_required
def thread_by_username(request, username):
    if username == request.user.username:
        raise Http404("Não é possível conversar consigo mesmo.")
    other = get_object_or_404(User, username=username)
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
