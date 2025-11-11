from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from clinic.decorators import staff_required, staff_or_admin_required
from core.choices import Role


@staff_required
def staff_board(request):
    """Bảng điều khiển cho nhân viên"""
    context = {
        'title': 'Bảng điều khiển nhân viên',
    }
    return render(request, 'billing/staff_board.html', context)


@staff_required
def invoice_create_from_appt(request, appointment_id):
    """Tạo hóa đơn từ lịch hẹn"""
    # TODO: Implement invoice creation logic
    messages.success(request, f"Tạo hóa đơn cho lịch hẹn {appointment_id}")
    return redirect('billing:staff_board')


@staff_required
def invoice_detail(request, invoice_id):
    """Chi tiết hóa đơn"""
    # TODO: Implement invoice detail logic
    context = {
        'title': f'Chi tiết hóa đơn #{invoice_id}',
        'invoice_id': invoice_id,
    }
    return render(request, 'billing/invoice_detail.html', context)


@staff_required
def invoice_pay_cash(request, invoice_id):
    """Thanh toán tiền mặt"""
    if request.method == 'POST':
        # TODO: Implement cash payment logic
        messages.success(request, f"Thanh toán tiền mặt cho hóa đơn #{invoice_id}")
        return redirect('billing:invoice_detail', invoice_id=invoice_id)
    
    context = {
        'title': f'Thanh toán tiền mặt - Hóa đơn #{invoice_id}',
        'invoice_id': invoice_id,
    }
    return render(request, 'billing/invoice_pay_cash.html', context)


@staff_required
def invoice_print(request, invoice_id):
    """In hóa đơn"""
    # TODO: Implement invoice printing logic
    messages.success(request, f"In hóa đơn #{invoice_id}")
    return redirect('billing:invoice_detail', invoice_id=invoice_id)


@staff_or_admin_required
def invoice_list(request):
    """Danh sách hóa đơn"""
    # TODO: Implement invoice list logic
    context = {
        'title': 'Danh sách hóa đơn',
    }
    return render(request, 'billing/invoice_list.html', context)
