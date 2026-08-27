"""
شاشة المصروفات - تسجيل مصروفات المحل، وسلف، ومصروفات شهرية متكررة زي الإهلاك
"""
import flet as ft
import db
from datetime import date


def ExpensesView(page: ft.Page):
    desc_field = ft.TextField(label="وصف المصروف", rtl=True, expand=2)
    amount_field = ft.TextField(label="المبلغ", rtl=True, expand=1, keyboard_type=ft.KeyboardType.NUMBER)
    category_dd = ft.Dropdown(
        label="التصنيف", rtl=True, expand=1,
        options=[ft.dropdown.Option(c) for c in db.EXPENSE_CATEGORIES],
        value=db.EXPENSE_CATEGORIES[0],
    )
    recurring_switch = ft.Switch(label="بند شهري متكرر (زي الإهلاك) - هيتسجل تلقائي كل شهر")

    expenses_list = ft.ListView(expand=True, spacing=8, padding=ft.Padding.all(5))
    total_text = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700)
    status_text = ft.Text("", color=ft.Colors.RED)

    def refresh_list():
        today = date.today().isoformat()
        items = db.get_expenses_for_date(today)
        expenses_list.controls.clear()
        total = 0.0
        if not items:
            expenses_list.controls.append(
                ft.Container(content=ft.Text("لسه مفيش مصروفات النهاردة", color=ft.Colors.GREY), padding=20)
            )
        for exp in items:
            total += exp["amount"]
            expenses_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Row([
                                        ft.Text(exp["description"], weight=ft.FontWeight.BOLD),
                                        ft.Icon(ft.Icons.SCHEDULE, size=14, color=ft.Colors.GREY)
                                        if exp["is_recurring"] else ft.Container(),
                                    ]),
                                    ft.Text(exp["category"], size=12, color=ft.Colors.GREY_700),
                                ],
                                expand=True, spacing=2,
                            ),
                            ft.Text(f'{exp["amount"]:.2f} ج.م', color=ft.Colors.RED_700),
                            ft.IconButton(ft.Icons.DELETE, icon_size=18, icon_color=ft.Colors.RED_400,
                                          on_click=lambda e, exp=exp: remove(exp)),
                        ]
                    ),
                    padding=10, border_radius=10, bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                )
            )
        total_text.value = f"إجمالي مصروفات النهاردة: {total:.2f} ج.م"
        page.update()

    def remove(exp):
        db.delete_expense(exp["id"])
        refresh_list()

    def save(e):
        status_text.value = ""
        if not desc_field.value or not amount_field.value:
            status_text.value = "لازم تكتب الوصف والمبلغ"
            page.update()
            return
        try:
            amount = float(amount_field.value)
        except ValueError:
            status_text.value = "المبلغ لازم يكون رقم"
            page.update()
            return

        db.add_expense(desc_field.value, category_dd.value, amount, recurring_switch.value)
        desc_field.value = ""
        amount_field.value = ""
        recurring_switch.value = False
        refresh_list()
        page.update()

    save_btn = ft.ElevatedButton("تسجيل المصروف", icon=ft.Icons.ADD, on_click=save)

    refresh_list()

    return ft.Column(
        [
            ft.Text("تسجيل المصروفات والسلف", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([desc_field, amount_field]),
            ft.Row([category_dd, save_btn]),
            recurring_switch,
            status_text,
            ft.Divider(),
            total_text,
            expenses_list,
        ],
        expand=True,
    )
