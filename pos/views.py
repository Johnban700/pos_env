from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import models as django_models   # Fix for F()
import json
from decimal import Decimal
from .models import Product, Sale, SaleItem, CashierShift


@login_required
def pos_terminal(request):
    products = Product.objects.filter(is_active=True)
    
    # Fixed low stock count
    low_stock_count = Product.objects.filter(
        stock__lte=django_models.F('low_stock_threshold')
    ).count()
    
    # Get current shift for this cashier
    current_shift = CashierShift.objects.filter(
        cashier=request.user, 
        end_time__isnull=True
    ).first()
    
    return render(request, 'pos/terminal.html', {
        'products': products,
        'low_stock_count': low_stock_count,
        'current_shift': current_shift
    })


@csrf_exempt
@login_required
def complete_sale(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cart = data.get('cart', [])
            payment_method = data.get('payment_method')
            tendered = Decimal(str(data.get('tendered', 0)))

            if not cart:
                return JsonResponse({'error': 'Cart is empty'}, status=400)

            subtotal = Decimal('0')
            sale_items_data = []

            for item in cart:
                product = get_object_or_404(Product, id=item['id'])
                if product.stock < item['qty']:
                    return JsonResponse({'error': f'Insufficient stock for {product.name}'}, status=400)

                qty = item['qty']
                price = product.price
                item_sub = qty * price
                subtotal += item_sub

                sale_items_data.append({
                    'product': product,
                    'qty': qty,
                    'price': price,
                    'subtotal': item_sub
                })

            tax_rate = Decimal('0.00')   # Change if needed (Taiwan VAT is usually 5%)
            tax_amount = (subtotal * tax_rate) / 100
            total = subtotal + tax_amount

            # Create Sale
            sale = Sale.objects.create(
                cashier=request.user,
                subtotal=subtotal,
                tax_amount=tax_amount,
                total=total,
                payment_method=payment_method,
                tendered=tendered if payment_method == 'cash' else total,
                change=max(Decimal('0'), tendered - total) if payment_method == 'cash' else Decimal('0')
            )

            # Save items and update inventory
            for item_data in sale_items_data:
                SaleItem.objects.create(
                    sale=sale,
                    product=item_data['product'],
                    quantity=item_data['qty'],
                    unit_price=item_data['price'],
                    subtotal=item_data['subtotal']
                )
                item_data['product'].stock -= item_data['qty']
                item_data['product'].save()

            # Update current shift total sales
            shift = CashierShift.objects.filter(
                cashier=request.user, 
                end_time__isnull=True
            ).first()
            if shift:
                shift.total_sales += total
                shift.save()

            return JsonResponse({
                'success': True,
                'transaction_id': sale.transaction_id,
                'total': float(total),
                'change': float(sale.change),
                'receipt_url': f'/pos/receipt/{sale.id}/'
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def receipt_view(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    items = sale.items.select_related('product').all()
    return render(request, 'pos/receipt.html', {'sale': sale, 'items': items})


@login_required
def start_shift(request):
    if not CashierShift.objects.filter(cashier=request.user, end_time__isnull=True).exists():
        CashierShift.objects.create(cashier=request.user, opening_balance=Decimal('0'))
    return redirect('pos:terminal')


@login_required
def end_shift(request):
    shift = CashierShift.objects.filter(cashier=request.user, end_time__isnull=True).first()
    if shift:
        shift.end_time = timezone.now()   # Need to import timezone
        shift.closing_balance = shift.total_sales
        shift.save()
    return redirect('pos:terminal')