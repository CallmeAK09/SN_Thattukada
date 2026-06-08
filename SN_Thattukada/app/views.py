from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
import json
from .models import Item
from .forms import ItemForm

def dashboard_view(request):
    items = Item.objects.all().order_by('name')
    return render(request, 'app/dashboard.html', {'items': items})

def add_item_view(request):
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Item '{form.cleaned_data['name']}' added successfully!")
            return redirect('dashboard')
        else:
            messages.error(request, "Failed to add item. Please correct the errors below.")
    else:
        form = ItemForm()
    return render(request, 'app/add_item.html', {'form': form})

def calculate_view(request):
    items = Item.objects.all().order_by('name')
    return render(request, 'app/calculate.html', {'items': items})

def edit_item_view(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f"Item '{form.cleaned_data['name']}' updated successfully!")
            return redirect('dashboard')
        else:
            messages.error(request, "Failed to update item. Please correct the errors below.")
    else:
        form = ItemForm(instance=item)
    return render(request, 'app/add_item.html', {'form': form, 'is_edit': True, 'item': item})

@csrf_protect
@require_POST
def send_whatsapp_view(request):
    try:
        data = json.loads(request.body)
        phone = data.get('phone')
        message = data.get('message')
        
        if not phone or not message:
            return JsonResponse({'success': False, 'error': 'Missing phone number or message content.'}, status=400)
        
        # Clean phone number: keep only digits
        clean_phone = ''.join(c for c in phone if c.isdigit())
        if len(clean_phone) < 10:
            return JsonResponse({'success': False, 'error': 'Invalid phone number. Must contain at least 10 digits.'}, status=400)
        
        # Log to the console as requested (simulating backend WhatsApp dispatch)
        print("\n" + "="*50)
        print(f"▶ AUTOMATIC BACKEND WHATSAPP OUTBOUND DISPATCH")
        print(f"▶ Recipient: {clean_phone}")
        print(f"▶ Message:\n{message}")
        print("="*50 + "\n")
        
        return JsonResponse({'success': True})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

