"""
شاشة المنتجات - قائمة الأسعار والمخزون والتصنيفات
"""
import flet as ft
import db


def ProductsView(page: ft.Page):
    products_list = ft.ListView(expand=True, spacing=8, padding=ft.Padding.all(5))

    name_field = ft.TextField(label="اسم المنتج", rtl=True, expand=2)
    price_field = ft.TextField(label="السعر", rtl=True, expand=1, keyboard_type=ft.KeyboardType.NUMBER)
    stock_field = ft.TextField(label="الكمية بالمخزن", rtl=True, expand=1, keyboard_type=ft.KeyboardType.NUMBER)
    category_dd = ft.Dropdown(
        label="التصنيف", rtl=True, expand=1,
        options=[ft.dropdown.Option(c) for c in db.PRODUCT_CATEGORIES],
        value=db.PRODUCT_CATEGORIES[0],
    )
    unit_dd = ft.Dropdown(
        label="الوحدة", rtl=True, expand=1,
        options=[ft.dropdown.Option(u) for u in db.UNITS],
        value=db.UNITS[0],
    )

    # شريط البحث الجديد
    search_field = ft.TextField(
        hint_text="ابحث باسم المنتج أو التصنيف...",
        prefix_icon=ft.Icons.SEARCH,
        rtl=True,
        expand=True,
        on_change=lambda e: refresh_list()  # تصفية القائمة فور الكتابة
    )

    editing_id = {"value": None}
    status_text = ft.Text("", color=ft.Colors.RED)

    def clear_form():
        name_field.value = ""
        price_field.value = ""
        stock_field.value = ""
        category_dd.value = db.PRODUCT_CATEGORIES[0]
        unit_dd.value = db.UNITS[0]
        editing_id["value"] = None
        save_btn.text = "إضافة المنتج"
        cancel_btn.visible = False
        page.update()

    def refresh_list():
        products_list.controls.clear()
        items = db.get_products()
        
        # تصفية القائمة حسب نص البحث
        query = search_field.value.strip().lower() if search_field.value else ""
        if query:
            items = [p for p in items if query in p["name"].lower() or query in p["category"].lower()]

        if not items:
            msg = "لا توجد نتائج مطابقة للبحث" if query else "لسه معملتش أي منتجات، ضيف أول منتج من فوق"
            products_list.controls.append(
                ft.Container(
                    content=ft.Text(msg, color=ft.Colors.GREY),
                    padding=20, alignment=ft.Alignment.CENTER,
                )
            )
        for p in items:
            products_list.controls.append(product_row(p))
        page.update()

    def product_row(p):
        low = p["stock"] <= 3
        unit_label = "كجم" if p["unit"] == "كيلو" else "قطعة"
        stock_str = f'{p["stock"]:g} {unit_label}'
        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Row([
                                ft.Text(p["name"], size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(
                                    content=ft.Text(p["category"], size=11, color=ft.Colors.WHITE),
                                    bgcolor=ft.Colors.ORANGE_400, padding=ft.Padding.only(left=8, right=8, top=2, bottom=2),
                                    border_radius=20,
                                ),
                            ]),
                            ft.Row(
                                [
                                    ft.Text(f'{p["price"]:.2f} ج.م / {unit_label}', size=13, color=ft.Colors.GREY_700),
                                    ft.Text(
                                        f'المخزون: {stock_str}',
                                        size=13,
                                        color=ft.Colors.RED if low else ft.Colors.GREY_700,
                                        weight=ft.FontWeight.BOLD if low else None,
                                    ),
                                ],
                                spacing=15,
                            ),
                        ],
                        expand=True, spacing=4,
                    ),
                    ft.IconButton(ft.Icons.EDIT, icon_size=20, on_click=lambda e, p=p: start_edit(p)),
                    ft.IconButton(ft.Icons.DELETE, icon_size=20, icon_color=ft.Colors.RED_400,
                                  on_click=lambda e, p=p: remove(p)),
                ]
            ),
            padding=12, border_radius=10, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        )

    def start_edit(p):
        editing_id["value"] = p["id"]
        name_field.value = p["name"]
        price_field.value = str(p["price"])
        stock_field.value = str(p["stock"])
        category_dd.value = p["category"]
        unit_dd.value = p["unit"]
        save_btn.text = "حفظ التعديل"
        cancel_btn.visible = True
        page.update()

    def remove(p):
        db.delete_product(p["id"])
        refresh_list()

    def save(e):
        status_text.value = ""
        if not name_field.value or not price_field.value:
            status_text.value = "لازم تكتب اسم المنتج والسعر"
            page.update()
            return
        try:
            price = float(price_field.value)
            stock = float(stock_field.value) if stock_field.value else 0
        except ValueError:
            status_text.value = "السعر والكمية لازم يكونوا أرقام"
            page.update()
            return

        if editing_id["value"]:
            db.update_product(editing_id["value"], name_field.value, price, stock,
                               category_dd.value, unit_dd.value)
        else:
            db.add_product(name_field.value, price, stock, category_dd.value, unit_dd.value)

        clear_form()
        refresh_list()

    save_btn = ft.ElevatedButton("إضافة المنتج", icon=ft.Icons.ADD, on_click=save)
    cancel_btn = ft.TextButton("إلغاء", visible=False, on_click=lambda e: clear_form())

    refresh_list()

    return ft.Column(
        [
            ft.Text("قائمة الأسعار والمنتجات", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([name_field, price_field]),
            ft.Row([stock_field, category_dd, unit_dd]),
            ft.Row([save_btn, cancel_btn]),
            status_text,
            ft.Divider(),
            # عنوان المنتجات الحالية وجانبه شريط البحث
            ft.Row(
                [
                    ft.Text("المنتجات الحالية", size=14, color=ft.Colors.GREY_700),
                    search_field,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            products_list,
        ],
        expand=True,
    )