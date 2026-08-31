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

    def order_card(order):
        sale_id = order["id"]
        total_amount = order.get("total_amount", 0.0)
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

                # 3. رقم الطلب والتاريخ
                ft.Column([
                    ft.Text(f"طلب #{sale_id}", weight=ft.FontWeight.BOLD, size=15, color=ft.Colors.WHITE),
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
            ft.IconButton(ft.Icons.REFRESH, icon_color=ft.Colors.ORANGE_400, on_click=lambda e: refresh_orders()),
            phone_search_field,
            ft.Row([
                ft.Text("إدارة التوصيل والدليفري 🛵", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Icon(ft.Icons.DELIVERY_DINING, color=ft.Colors.ORANGE_400, size=30),
            ], spacing=10),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        
        ft.Divider(color=ft.Colors.WHITE24),
        orders_list
    ], expand=True, spacing=10)