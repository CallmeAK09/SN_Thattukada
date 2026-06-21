from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from decimal import Decimal
import json
from .models import Item
from .forms import ItemForm

class ItemModelTest(TestCase):
    def test_item_creation(self):
        item = Item.objects.create(name="Masala Dosa", price=Decimal("45.50"))
        self.assertEqual(item.name, "Masala Dosa")
        self.assertEqual(item.price, Decimal("45.50"))
        self.assertEqual(str(item), "Masala Dosa - ₹45.50")

    def test_item_price_validation(self):
        item = Item(name="Porotta", price=Decimal("-2.00"))
        with self.assertRaises(ValidationError):
            item.full_clean()


class ItemFormTest(TestCase):
    def test_valid_form(self):
        form_data = {'name': 'Porotta', 'price': '10.00'}
        form = ItemForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_name_numbers(self):
        form_data = {'name': 'Porotta 123', 'price': '10.00'}
        form = ItemForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertEqual(form.errors['name'][0], "Item name must contain only alphabets, spaces, underscores, and parentheses.")

    def test_valid_name_special_allowed(self):
        form_data = {'name': 'Chicken Fry (Half)_Special', 'price': '120.00'}
        form = ItemForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_name_special_chars(self):
        form_data = {'name': 'Porotta!', 'price': '10.00'}
        form = ItemForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_invalid_name_only_spaces(self):
        form_data = {'name': '   ', 'price': '10.00'}
        form = ItemForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_invalid_price_negative(self):
        form_data = {'name': 'Idli', 'price': '-1.50'}
        form = ItemForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('price', form.errors)


class ViewsTest(TestCase):
    def setUp(self):
        self.item1 = Item.objects.create(name="Chilli Chicken", price=Decimal("120.00"))
        self.item2 = Item.objects.create(name="Tea", price=Decimal("12.00"))

    def test_dashboard_view(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chilli Chicken")
        self.assertContains(response, "Tea")
        self.assertContains(response, "₹120.00")
        self.assertContains(response, "₹12.00")

    def test_add_item_view_get(self):
        response = self.client.get(reverse('add_item'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Add Menu Item")

    def test_add_item_view_post_valid(self):
        response = self.client.post(reverse('add_item'), {
            'name': 'Omelette',
            'price': '15.00'
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(Item.objects.filter(name='Omelette').exists())

    def test_add_item_view_post_invalid(self):
        response = self.client.post(reverse('add_item'), {
            'name': 'Omelette 123',
            'price': '-5.00'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Item.objects.filter(name='Omelette 123').exists())

    def test_calculate_view(self):
        response = self.client.get(reverse('calculate'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chilli Chicken")
        self.assertContains(response, "Tea")
        self.assertContains(response, "Calculate Bill")

    def test_edit_item_view_get(self):
        url = reverse('edit_item', kwargs={'pk': self.item1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit Menu Item")
        self.assertContains(response, "Chilli Chicken")

    def test_edit_item_view_post_valid(self):
        url = reverse('edit_item', kwargs={'pk': self.item1.pk})
        response = self.client.post(url, {
            'name': 'Chilli Chicken (Special)_Edited',
            'price': '130.00'
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.item1.refresh_from_db()
        self.assertEqual(self.item1.name, 'Chilli Chicken (Special)_Edited')
        self.assertEqual(self.item1.price, Decimal('130.00'))

    def test_send_whatsapp_view_valid(self):
        url = reverse('send_whatsapp')
        response = self.client.post(url, json.dumps({
            'phone': '919876543210',
            'message': 'Test bill content'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)

    def test_send_whatsapp_view_invalid_phone(self):
        url = reverse('send_whatsapp')
        response = self.client.post(url, json.dumps({
            'phone': '123',
            'message': 'Test bill content'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['success'], False)

    def test_orders_list_view_redirect(self):
        response = self.client.get(reverse('orders_list'))
        self.assertRedirects(response, reverse('calculate'))

    def test_orders_json_view_empty(self):
        response = self.client.get(reverse('orders_json'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['orders'], [])

    def test_save_order_view_create_and_list(self):
        # Save a new order
        url = reverse('save_order')
        order_data = {
            'customer_name': 'Table 5',
            'items': {
                '1': {'id': '1', 'name': 'Chilli Chicken', 'price': '120.00', 'qty': 2}
            }
        }
        response = self.client.post(url, json.dumps(order_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data['success'])
        order_id = json_data['order_id']

        # Verify it lists in the orders JSON endpoint
        response = self.client.get(reverse('orders_json'))
        self.assertEqual(response.status_code, 200)
        orders = response.json()['orders']
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]['name'], 'Table 5')
        self.assertEqual(orders[0]['items']['1']['name'], 'Chilli Chicken')
        self.assertEqual(float(orders[0]['total']), 240.0)

    def test_save_order_view_update(self):
        # First save an order in the session
        session = self.client.session
        session['orders'] = {
            'test_id': {
                'id': 'test_id',
                'name': 'Table 10',
                'items': {
                    '1': {'id': '1', 'name': 'Chilli Chicken', 'price': '120.00', 'qty': 1, 'subtotal': 120.0}
                },
                'total': 120.0,
                'created_at': '2026-06-21 08:30 PM'
            }
        }
        session.save()

        # Update it via POST
        url = reverse('save_order')
        order_data = {
            'order_id': 'test_id',
            'customer_name': 'Table 10 Updated',
            'items': {
                '1': {'id': '1', 'name': 'Chilli Chicken', 'price': '120.00', 'qty': 3}
            }
        }
        response = self.client.post(url, json.dumps(order_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

        # Check update reflected in session
        updated_session = self.client.session
        order = updated_session['orders']['test_id']
        self.assertEqual(order['name'], 'Table 10 Updated')
        self.assertEqual(float(order['total']), 360.0)

    def test_pay_order_view(self):
        # Create an order in session
        session = self.client.session
        session['orders'] = {
            'pay_me_id': {
                'id': 'pay_me_id',
                'name': 'Table 12',
                'items': {
                    '2': {'id': '2', 'name': 'Tea', 'price': '12.00', 'qty': 2, 'subtotal': 24.0}
                },
                'total': 24.0,
                'created_at': '2026-06-21 08:30 PM'
            }
        }
        session.save()

        # Mark paid
        url = reverse('pay_order', kwargs={'order_id': 'pay_me_id'})
        response = self.client.post(url)
        self.assertRedirects(response, reverse('calculate'))

        # Verify it has been deleted from session
        updated_session = self.client.session
        self.assertNotIn('pay_me_id', updated_session.get('orders', {}))

