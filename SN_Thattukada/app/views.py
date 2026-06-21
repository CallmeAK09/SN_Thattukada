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
    edit_id = request.GET.get('edit')
    edit_order = None
    edit_order_json = None
    if edit_id:
        orders = request.session.get('orders', {})
        edit_order = orders.get(str(edit_id))
        if edit_order:
            # Create a clean copy to JSON serialize
            edit_order_json = json.dumps(edit_order)
            
    return render(request, 'app/calculate.html', {
        'items': items,
        'edit_order': edit_order,
        'edit_order_json': edit_order_json
    })

def orders_list_view(request):
    return redirect('calculate')

def orders_json_view(request):
    orders_dict = request.session.get('orders', {})
    orders_list = sorted(orders_dict.values(), key=lambda x: x.get('id', ''), reverse=True)
    return JsonResponse({'success': True, 'orders': orders_list})


@csrf_protect
@require_POST
def save_order_view(request):
    try:
        data = json.loads(request.body)
        items = data.get('items', {})
        customer_name = data.get('customer_name', '').strip()
        order_id = data.get('order_id')
        
        if not items:
            return JsonResponse({'success': False, 'error': 'Cannot save an empty order.'}, status=400)
        
        # Calculate total and store subtotal per item
        total = 0.0
        for item_id, item in items.items():
            price = float(item.get('price', 0.0))
            qty = int(float(item.get('qty', 1)))
            sub = price * qty
            item['price'] = price
            item['qty'] = qty
            item['subtotal'] = sub
            total += sub
            
        orders = request.session.get('orders', {})
        
        import datetime
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
        
        if order_id and str(order_id) in orders:
            order_id_str = str(order_id)
            orders[order_id_str]['items'] = items
            orders[order_id_str]['total'] = total
            if customer_name:
                orders[order_id_str]['name'] = customer_name
            saved_id = order_id_str
        else:
            import time
            new_id = str(int(time.time() * 1000))
            if not customer_name:
                order_num = len(orders) + 1
                customer_name = f"Order #{order_num}"
            orders[new_id] = {
                'id': new_id,
                'name': customer_name,
                'items': items,
                'total': total,
                'created_at': now_str
            }
            saved_id = new_id
            
        request.session['orders'] = orders
        request.session.modified = True
        
        return JsonResponse({'success': True, 'order_id': saved_id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_protect
@require_POST
def pay_order_view(request, order_id):
    orders = request.session.get('orders', {})
    order_id_str = str(order_id)
    success = False
    message = ""
    if order_id_str in orders:
        del orders[order_id_str]
        request.session['orders'] = orders
        request.session.modified = True
        success = True
        message = "Order marked as Paid and removed from session."
    else:
        message = "Order not found."

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('accept') == 'application/json' or request.content_type == 'application/json':
        return JsonResponse({'success': success, 'message': message})

    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    return redirect('calculate')


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

