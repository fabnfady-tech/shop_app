import flet as ft
import os
import db
from sales_view import SalesView
from products_view import ProductsView
from expenses_view import ExpensesView
from deferred_view import DeferredView
from returns_view import ReturnsView
from monthly_view import MonthlyView
from reports_view import ReportsView

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BG_PATH = os.path.join(BASE_DIR, "bg_logo.jpg")
ICON_PATH = os.path.join(BASE_DIR, "assets", "icon.png")

PAGES = [
    ("بيع", ft.Icons.POINT_OF_SALE, SalesView),
    ("المنتجات", ft.Icons.INVENTORY_2, ProductsView),
    ("المصروفات", ft.Icons.ACCOUNT_BALANCE_WALLET, ExpensesView),
    ("الإيرادات المؤجلة", ft.Icons.SCHEDULE_SEND, DeferredView),
    ("المرتجعات", ft.Icons.UNDO, ReturnsView),
    ("جدول الشهر", ft.Icons.TABLE_CHART, MonthlyView),
    ("التقرير", ft.Icons.BAR_CHART, ReportsView),
]


def main(page: ft.Page):
    page.title = "Aleefy Pets "
    page.rtl = True
    page.padding = 0
    page.bgcolor = "#13162d"  # لون كحلي دافئ متناسق مع اللوجو
    if os.path.exists(ICON_PATH):
        page.window_icon = ICON_PATH

    current_index = {"value": 0}

    body_container = ft.Container(expand=True, padding=15)
    title_text = ft.Text(PAGES[0][0], size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)

    sidebar_content = ft.Column([], expand=True, spacing=5)

    # سايدبار بشفافية كحلية أنيقة تسمح بظهور تفاصيل اللوجو
    sidebar_container = ft.Container(
        width=280,
        bgcolor=ft.Colors.with_opacity(0.92, "#101226"),
        padding=15,
        content=sidebar_content,
    )

    overlay_bg = ft.Container(
        expand=True,
        bgcolor=ft.Colors.BLACK54,
        on_click=lambda e: hide_sidebar(),
    )

    sidebar_overlay = ft.Stack(
        controls=[
            overlay_bg,
            ft.Row([sidebar_container], alignment=ft.MainAxisAlignment.START, expand=True),
        ],
        visible=False,
        expand=True,
    )

    def hide_sidebar():
        sidebar_overlay.visible = False
        page.update()

    def open_sidebar(e):
        sidebar_overlay.visible = True
        page.update()

    def load_page_view(view_fn):
        # تغليف الشاشة داخل Column قابل للتمرير للأسفل
        body_container.content = ft.Column(
            [view_fn(page)],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def select_page(index):
        current_index["value"] = index
        title, icon, view_fn = PAGES[index]
        load_page_view(view_fn)
        title_text.value = title
        build_menu_items()
        hide_sidebar()

    def build_menu_items():
        items = [
            ft.Container(
                padding=10,
                content=ft.Row([
                    ft.Image(src=BG_PATH, width=32, height=32, fit=ft.ImageFit.CONTAIN, border_radius=6)
                    if os.path.exists(BG_PATH) else ft.Icon(ft.Icons.PETS, size=28, color=ft.Colors.ORANGE_400),
                    ft.Text("Aleefy Pets", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ]),
            ),
            ft.Divider(color=ft.Colors.WHITE24),
        ]
        for idx, (label, icon, _) in enumerate(PAGES):
            is_selected = (idx == current_index["value"])
            items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(icon, color=ft.Colors.ORANGE_400 if is_selected else ft.Colors.WHITE70),
                        ft.Text(
                            label,
                            weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL,
                            color=ft.Colors.ORANGE_400 if is_selected else ft.Colors.WHITE,
                        ),
                    ]),
                    padding=12,
                    border_radius=8,
                    bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.ORANGE_700) if is_selected else None,
                    on_click=lambda e, i=idx: select_page(i),
                )
            )
        sidebar_content.controls = items

    # الشريط العلوي متناسق مع الخلفية الكحلية
    app_bar = ft.Container(
        height=60,
        bgcolor=ft.Colors.with_opacity(0.85, "#181b36"),
        padding=ft.Padding.only(left=15, right=15),
        content=ft.Row([
            ft.IconButton(ft.Icons.MENU, icon_color=ft.Colors.WHITE, on_click=open_sidebar),
            title_text,
        ], alignment=ft.MainAxisAlignment.START),
    )

    # تحميل الشاشة الأولى
    load_page_view(PAGES[0][2])
    build_menu_items()

    # طبقة الصورة كخلفية ثابتة للسيستم بأكمله
    background_layer = ft.Container(
        expand=True,
        bgcolor="#13162d",
        content=ft.Image(
            src=BG_PATH,
            fit=ft.ImageFit.COVER,
            opacity=0.35,  # التحكم في درجة وضوح خلفية اللوجو
        ) if os.path.exists(BG_PATH) else None,
    )

    # الهيكل الرئيسي للواجهة
    main_layout = ft.Column([app_bar, body_container], expand=True, spacing=0)

    page.add(
        ft.Stack(
            controls=[
                background_layer,  # الخلفية في القاع
                main_layout,        # المحتوى الرئيسي
                sidebar_overlay,    # القائمة الجانبية المنزلقة
            ],
            expand=True,
        )
    )


if __name__ == "__main__":
    db.init_db()
    db.apply_recurring_expenses()
    ft.app(target=main)