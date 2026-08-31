"""
شاشة المرتجعات - تسجيل إرجاع منتج وإرجاعه للمخزون
"""
import flet as ft
import db


def ReturnsView(page: ft.Page):
    products = db.get_products()
    product_dd = ft.Dropdown(
        label="المنتج", rtl=True, expand=2,
        options=[ft.dropdown.Option(str(p["id"]), text=p["name"]) for p in products],
    )
    qty_field = ft.TextField(label="الكمية", rtl=True, expand=1, keyboard_type=ft.KeyboardType.NUMBER)
    refund_field = ft.TextField(label="قيمة الاسترجاع (ج.م)", rtl=True, expand=1,
                                 keyboard_type=ft.KeyboardType.NUMBER)
    reason_field = ft.TextField(label="السبب (اختياري)", rtl=True)

    status_text = ft.Text("", color=ft.Colors.RED)
    returns_list = ft.ListView(expand=True, spacing=8, padding=ft.Padding.all(5))

    available_text = ft.Text("", size=12, color=ft.Colors.GREY_700)

    def on_product_change(e):
        pid = int(product_dd.value) if product_dd.value else None
        p = next((p for p in products if p["id"] == pid), None)
        if p:
            qty_field.value = "1"
            refund_field.value = f'{p["price"]:.2f}'
            returnable = db.get_product_returnable_quantity(pid)
            unit_label = "كجم" if p["unit"] == "كيلو" else "قطعة"
            available_text.value = f"أقصى كمية ممكن ترجعها من المنتج ده: {returnable:g} {unit_label}"
        else:
            available_text.value = ""
        page.update()

    product_dd.on_change = on_product_change

    def refresh_list():
        returns_list.controls.clear()
        items = db.get_returns(limit=30)
        if not items:
            returns_list.controls.append(
                ft.Container(content=ft.Text("مفيش مرتجعات مسجلة", color=ft.Colors.GREY), padding=20)
            )
        for r in items:
            returns_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(r["product_name"], weight=ft.FontWeight.BOLD),
                                    ft.Text(f'{r["created_at"][:16]}' + (f' - {r["reason"]}' if r["reason"] else ""),
                                            size=11, color=ft.Colors.GREY_600),
                                ],
                                expand=True, spacing=2,
                            ),
                            ft.Text(f'{r["quantity"]:g}', size=12, color=ft.Colors.GREY_700),
                            ft.Text(f'-{r["refund_amount"]:.2f} ج.م', color=ft.Colors.RED_700),
                        ]
                    ),
                    padding=10, border_radius=10, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                )
            )
        page.update()

    def save(e):
        status_text.value = ""
        if not product_dd.value or not qty_field.value or not refund_field.value:
            status_text.value = "اختار المنتج واكتب الكمية وقيمة الاسترجاع"
            page.update()
            return
        try:
            qty = float(qty_field.value)
            refund = float(refund_field.value)
        except ValueError:
            status_text.value = "الكمية والقيمة لازم يكونوا أرقام"
            page.update()
            return

        pid = int(product_dd.value)
        p = next((p for p in products if p["id"] == pid), None)
        try:
            db.add_return(pid, p["name"] if p else "منتج محذوف", qty, refund, reason_field.value)
        except db.ReturnValidationError as ex:
            status_text.value = str(ex)
            page.update()
            return

        product_dd.value = None
        qty_field.value = ""
        refund_field.value = ""
        reason_field.value = ""
        available_text.value = ""
        refresh_list()
        page.update()

    save_btn = ft.ElevatedButton("تسجيل المرتجع", icon=ft.Icons.UNDO, on_click=save)

    refresh_list()

    return ft.Column(
        [
            ft.Text("المرتجعات", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([product_dd, qty_field]),
            available_text,
            ft.Row([refund_field, reason_field]),
            save_btn,
            status_text,
            ft.Divider(),
            ft.Text("آخر المرتجعات", size=14, color=ft.Colors.GREY_700),
            returns_list,
        ],
        expand=True,
    )
