import flet as ft
import db

def DeferredView(page: ft.Page):
    search_input = ft.TextField(
        hint_text="ابحث باسم العميل، التليفون، أو رقم الفاتورة (مثال: INV-00001)...",
        prefix_icon=ft.Icons.SEARCH,
        rtl=True,
        expand=True,
        bgcolor="#1c1f3b",
        border_color=ft.Colors.WHITE24,
        focused_border_color=ft.Colors.ORANGE_400,
        color=ft.Colors.WHITE,
    )
    
    show_paid_switch = ft.Switch(
        label="عرض الفواتير المسددة بالكامل",
        value=False,
        active_color=ft.Colors.ORANGE_400,
    )
    
    summary_text = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE_400)
    list_container = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    pay_dialog = ft.AlertDialog(modal=True)

    def open_pay_dialog(item):
        row = dict(item)
        total_amount = float(row.get("total", 0))
        paid_amount = float(row.get("paid_amount", 0))
        remaining = total_amount - paid_amount

        pay_field = ft.TextField(
            label="المبلغ المدفوع الآن (ج.م)",
            value=f"{remaining:.2f}",
            keyboard_type=ft.KeyboardType.NUMBER,
            rtl=True,
            autofocus=True,
            border_color=ft.Colors.ORANGE_400,
        )
        status_text = ft.Text("", color=ft.Colors.RED_400, size=12)

        def save_payment(e):
            try:
                amount_to_pay = float(pay_field.value)
                db.add_payment(row["id"], amount_to_pay)
                pay_dialog.open = False
                page.update()
                load_deferred_data()
            except db.PaymentValidationError as err:
                status_text.value = str(err)
                page.update()
            except ValueError:
                status_text.value = "برجاء كتابة رقم صحيح"
                page.update()

        customer_display = row.get("customer_name") or "بدون اسم"

        pay_dialog.title = ft.Row([
            ft.Icon(ft.Icons.PAYMENT, color=ft.Colors.ORANGE_400),
            ft.Text("تسجيل دفعة للعميل"),
        ])
        
        pay_dialog.content = ft.Column([
            ft.Text(f"العميل: {customer_display}", weight=ft.FontWeight.BOLD),
            ft.Text(f"إجمالي الفاتورة: {total_amount:.2f} ج.م"),
            ft.Text(f"المدفوع سابقاً: {paid_amount:.2f} ج.م", color=ft.Colors.GREEN_400),
            ft.Text(f"المتبقي عليه: {remaining:.2f} ج.م", color=ft.Colors.RED_400, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            pay_field,
            status_text
        ], tight=True, spacing=8, width=340)

        pay_dialog.actions = [
            ft.TextButton("إلغاء", on_click=lambda e: setattr(pay_dialog, 'open', False) or page.update()),
            ft.ElevatedButton("تأكيد الدفع", icon=ft.Icons.CHECK, on_click=save_payment,
                             bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
        ]
        
        if pay_dialog not in page.overlay:
            page.overlay.append(pay_dialog)
            
        pay_dialog.open = True
        page.update()

    def load_deferred_data(e=None):
        query = search_input.value.strip().lower() if search_input.value else ""
        include_paid = show_paid_switch.value

        raw_data = db.get_deferred_sales(only_unpaid=not include_paid)

        list_container.controls.clear()
        total_remaining_all = 0.0

        for item in raw_data:
            row = dict(item)
            c_name = str(row.get("customer_name") or "غير محدد")
            c_phone = str(row.get("customer_phone") or "")
            inv_no = db.invoice_serial(row["id"])
            date_str = str(row.get("created_at", ""))

            total = float(row.get("total", 0))
            paid = float(row.get("paid_amount", 0))
            rem = total - paid

            if query and not (query in c_name.lower() or query in c_phone or query in inv_no.lower()):
                continue

            if rem > 0.00001:
                total_remaining_all += rem

            is_fully_paid = rem <= 0.00001

            card = ft.Container(
                bgcolor="#181b36",
                border_radius=10,
                padding=12,
                content=ft.Row([
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.RECEIPT_LONG, size=18, color=ft.Colors.ORANGE_400),
                            ft.Text(f"فاتورة {inv_no}", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Container(
                                content=ft.Text("مسدد بالكامل" if is_fully_paid else "مستحق سداد", size=10, color=ft.Colors.WHITE),
                                bgcolor=ft.Colors.GREEN_700 if is_fully_paid else ft.Colors.RED_700,
                                padding=ft.Padding(8, 2, 8, 2),
                                border_radius=10
                            )
                        ], spacing=6),
                        ft.Text(f"العميل: {c_name} {f'({c_phone})' if c_phone else ''}", size=13, color=ft.Colors.WHITE70),
                        ft.Text(f"التاريخ: {date_str}", size=11, color=ft.Colors.WHITE38),
                    ], expand=True, spacing=4),

                    ft.Row([
                        ft.Column([
                            ft.Text("الإجمالي", size=11, color=ft.Colors.WHITE54),
                            ft.Text(f"{total:.2f}", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Column([
                            ft.Text("المدفوع", size=11, color=ft.Colors.WHITE54),
                            ft.Text(f"{paid:.2f}", weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Column([
                            ft.Text("المتبقي", size=11, color=ft.Colors.WHITE54),
                            ft.Text(f"{rem:.2f}", weight=ft.FontWeight.BOLD, color=ft.Colors.RED_400),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ], spacing=15),

                    ft.ElevatedButton(
                        "تم السداد" if is_fully_paid else "تسجيل دفعة",
                        icon=ft.Icons.PAYMENT,
                        disabled=is_fully_paid,
                        bgcolor=ft.Colors.ORANGE_600 if not is_fully_paid else ft.Colors.GREY_800,
                        color=ft.Colors.WHITE,
                        on_click=lambda e, it=item: open_pay_dialog(it)
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            )
            list_container.controls.append(card)

        summary_text.value = f"إجمالي الديون المتبقية على العملاء: {total_remaining_all:.2f} ج.م"
        page.update()

    search_input.on_change = load_deferred_data
    show_paid_switch.on_change = load_deferred_data

    load_deferred_data()

    return ft.Column([
        ft.Row([search_input, show_paid_switch], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        summary_text,
        ft.Divider(color=ft.Colors.WHITE24),
        list_container
    ], expand=True, spacing=10)