import flet as ft
import db


def DeliveryView(page: ft.Page):
    search_query = {"phone": ""}

    # قائمة الطلبات
    orders_list = ft.ListView(expand=True, spacing=8, padding=5)

    # حقل البحث برقم الهاتف
    phone_search_field = ft.TextField(
        hint_text="بحث برقم الهاتف",
        rtl=True,
        text_size=12,
        height=38,
        width=250,
        color=ft.Colors.WHITE,
        hint_style=ft.TextStyle(color=ft.Colors.WHITE38, size=11),
        border_color=ft.Colors.WHITE24,
        focused_border_color=ft.Colors.ORANGE_400,
        content_padding=5,
        on_change=lambda e: (search_query.update({"phone": e.control.value.strip()}), refresh_orders()),
    )

    # ------------------ حماية الأدمن بكلمة المرور ------------------
    admin_password_field = ft.TextField(
        label="كلمة المرور",
        password=True,
        can_reveal_password=True,
        rtl=True,
        autofocus=True,
    )
    admin_status_text = ft.Text("", color=ft.Colors.RED_400, size=12)

    def close_admin_dialog(e=None):
        admin_dialog.open = False
        admin_password_field.value = ""
        admin_status_text.value = ""
        page.update()

    admin_dialog = ft.AlertDialog(
        title=ft.Row([ft.Icon(ft.Icons.LOCK, color=ft.Colors.ORANGE_400), ft.Text("تأكيد الأدمن")]),
        content=ft.Column(
            [
                ft.Text("الحذف محصور على الأدمن فقط - ادخل كلمة المرور", size=12, color=ft.Colors.GREY_400),
                admin_password_field,
                admin_status_text,
            ],
            tight=True,
            spacing=8,
            width=300,
        ),
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.overlay.append(admin_dialog)

    def is_session_unlocked():
        if hasattr(page, "data") and isinstance(page.data, dict):
            return page.data.get("admin_unlocked", False)
        return False

    def with_admin_confirm(on_confirmed):
        if is_session_unlocked():
            on_confirmed()
            return

        def try_confirm(e=None):
            pw_val = admin_password_field.value or ""
            is_valid = False
            if hasattr(db, "verify_admin_password"):
                is_valid = db.verify_admin_password(pw_val)
            else:
                is_valid = (pw_val == "123")

            if is_valid:
                if not hasattr(page, "data") or page.data is None:
                    page.data = {}
                page.data["admin_unlocked"] = True
                close_admin_dialog()
                on_confirmed()
            else:
                admin_status_text.value = "كلمة المرور غلط"
                page.update()

        admin_password_field.on_submit = try_confirm
        admin_dialog.actions = [
            ft.TextButton("إلغاء", on_click=close_admin_dialog),
            ft.ElevatedButton(
                "تأكيد",
                icon=ft.Icons.CHECK,
                on_click=try_confirm,
                bgcolor=ft.Colors.ORANGE_600,
                color=ft.Colors.WHITE,
            ),
        ]
        admin_dialog.open = True
        page.update()

    def delete_order(order_id):
        def do_delete():
            db.delete_sale(order_id)
            refresh_orders()
        with_admin_confirm(do_delete)

    # ------------------ نافذة إضافة طلب دليفري ------------------
    add_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Row([ft.Icon(ft.Icons.ADD_BUSINESS, color=ft.Colors.ORANGE_400), ft.Text("إضافة طلب دليفري")]),
        content=ft.Container(height=10),
    )
    page.overlay.append(add_dialog)

    def close_add_dialog(e=None):
        add_dialog.open = False
        page.update()

    def open_add_order_dialog(e=None):
        name_field = ft.TextField(label="اسم العميل", rtl=True, autofocus=True)
        phone_field = ft.TextField(label="رقم التليفون", rtl=True, keyboard_type=ft.KeyboardType.NUMBER)
        address_field = ft.TextField(label="العنوان", rtl=True)
        total_field = ft.TextField(label="إجمالي الطلب (ج.م)", rtl=True, keyboard_type=ft.KeyboardType.NUMBER)
        fee_field = ft.TextField(label="رسوم التوصيل (ج.م)", rtl=True, value="0", keyboard_type=ft.KeyboardType.NUMBER)
        status = ft.Text("", color=ft.Colors.RED_400, size=12)

        def save_order(e):
            if not name_field.value or not phone_field.value or not address_field.value:
                status.value = "لازم تكتب الاسم والتليفون والعنوان"
                page.update()
                return
            try:
                total_amount = float(total_field.value) if total_field.value else 0.0
                fee = float(fee_field.value) if fee_field.value else 0.0
            except ValueError:
                status.value = "المبلغ والرسوم لازم يكونوا أرقام"
                page.update()
                return
            if total_amount <= 0:
                status.value = "لازم تدخل إجمالي أكبر من صفر"
                page.update()
                return

            db.create_manual_delivery_order(
                name_field.value.strip(),
                phone_field.value.strip(),
                address_field.value.strip(),
                total_amount,
                fee,
            )
            close_add_dialog()
            refresh_orders()

        add_dialog.content = ft.Column(
            [name_field, phone_field, address_field, total_field, fee_field, status],
            tight=True, spacing=8, width=320, scroll="auto",
        )
        add_dialog.actions = [
            ft.TextButton("إلغاء", on_click=close_add_dialog),
            ft.ElevatedButton(
                "حفظ الطلب",
                icon=ft.Icons.SAVE,
                on_click=save_order,
                bgcolor=ft.Colors.GREEN_700,
                color=ft.Colors.WHITE,
            ),
        ]
        add_dialog.actions_alignment = ft.MainAxisAlignment.END
        add_dialog.open = True
        page.update()

    # ------------------ عرض الطلبات ورسم البطاقات ------------------
    def order_card(order):
        sale_id = order["id"]
        total_amount = order.get("total_amount", 0.0)
        delivery_fee = order.get("delivery_fee", 0.0)
        created_time = (order.get("created_at") or "").replace("T", " ")
        customer_name = order.get("customer_name") or "عميل عام"
        customer_phone = order.get("customer_phone") or "بدون رقم"
        address = order.get("address") or "غير محدد"

        return ft.Container(
            padding=12,
            border_radius=8,
            bgcolor="#12152e",
            border=ft.Border.all(1, "#22264d"),
            content=ft.Row([
                # 1. إجمالي الطلب
                ft.Column([
                    ft.Text("إجمالي الطلب:", size=12, color=ft.Colors.WHITE70, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{total_amount:.2f} ج.م", size=15, color=ft.Colors.GREEN_400, weight=ft.FontWeight.BOLD),
                    ft.Text(f"رسوم التوصيل: {delivery_fee:.2f} ج.م", size=10, color=ft.Colors.WHITE54) if delivery_fee else ft.Container(),
                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),

                # 2. بيانات العميل والعنوان
                ft.Column([
                    ft.Row([
                        ft.Text(customer_phone, color=ft.Colors.GREEN_400, size=13, weight=ft.FontWeight.BOLD),
                        ft.Icon(ft.Icons.PHONE, size=15, color=ft.Colors.GREEN_400),
                        ft.Container(width=10),
                        ft.Text(customer_name, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE, size=13),
                        ft.Icon(ft.Icons.PERSON, size=15, color=ft.Colors.ORANGE_400),
                    ], spacing=4, alignment=ft.MainAxisAlignment.END),
                    ft.Row([
                        ft.Text(f"العنوان: {address}", color=ft.Colors.WHITE70, size=12),
                        ft.Icon(ft.Icons.LOCATION_ON, size=15, color=ft.Colors.RED_400),
                    ], spacing=4, alignment=ft.MainAxisAlignment.END),
                ], spacing=4, alignment=ft.MainAxisAlignment.CENTER, expand=True),

                # 3. رقم الطلب والتاريخ وزرار الحذف
                ft.Column([
                    ft.Row([
                        ft.IconButton(
                            ft.Icons.DELETE_OUTLINE,
                            icon_size=18,
                            icon_color=ft.Colors.RED_400,
                            tooltip="مسح الطلب (أدمن فقط)",
                            on_click=lambda e, sid=sale_id: delete_order(sid),
                        ),
                        ft.Text(f"طلب #{sale_id}", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.WHITE),
                    ], spacing=4),
                    ft.Row([
                        ft.Icon(ft.Icons.CALENDAR_TODAY, size=12, color=ft.Colors.WHITE54),
                        ft.Text(f"({created_time})", size=11, color=ft.Colors.WHITE54),
                    ], spacing=4),
                ], spacing=4, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.END),

            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def refresh_orders():
        orders_list.controls.clear()
        orders = db.get_delivery_orders_by_phone(search_query["phone"])

        if not orders:
            orders_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.INBOX, size=45, color=ft.Colors.WHITE38),
                        ft.Text("لا توجد طلبات مطابقة للبحث", color=ft.Colors.WHITE54, size=14)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=30, alignment=ft.Alignment.CENTER
                )
            )
        else:
            for o in orders:
                orders_list.controls.append(order_card(o))
        page.update()

    refresh_orders()

    return ft.Column([
        # شريط العنوان والبحث
        ft.Row([
            ft.Row([
                ft.IconButton(ft.Icons.REFRESH, icon_color=ft.Colors.ORANGE_400, on_click=lambda e: refresh_orders()),
                ft.IconButton(ft.Icons.ADD_CIRCLE, icon_color=ft.Colors.GREEN_400, tooltip="إضافة طلب",
                              on_click=open_add_order_dialog),
                phone_search_field,
            ], spacing=4),
            ft.Row([
                ft.Text("إدارة التوصيل والدليفري 🛵", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Icon(ft.Icons.DELIVERY_DINING, color=ft.Colors.ORANGE_400, size=30),
            ], spacing=10),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

        ft.Divider(color=ft.Colors.WHITE24),
        orders_list
    ], expand=True, spacing=10)