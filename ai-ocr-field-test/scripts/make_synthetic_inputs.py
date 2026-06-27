"""Generate SYNTHETIC stand-in documents for every test case into inputs/.

These are placeholders so you can run the full pipeline end-to-end today. They
are NOT real-world documents -- replace them with genuine messy files before
publishing (the whole point of the experiment is real-world data). Filenames and
test ids match the PRD so the scoring/report flow works unchanged.

Usage:
    python scripts/make_synthetic_inputs.py
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

INPUTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "inputs")
FONTS = r"C:\Windows\Fonts"


def font(name: str, size: int):
    for candidate in (os.path.join(FONTS, name), name):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


# Reusable fonts
F_TITLE = lambda s=40: font("arialbd.ttf", s)
F_BODY = lambda s=20: font("arial.ttf", s)
F_BOLD = lambda s=20: font("arialbd.ttf", s)
F_HAND = lambda s=26: font("inkfree.ttf", s)
F_CJK = lambda s=22: font("msyh.ttc", s)
F_JP = lambda s=22: font("YuGothR.ttc", s)


def base_invoice(total="96.47", invoice_no="INV-2026-0042",
                 items=None, title="INVOICE", vendor="Acme Office Supplies Ltd"):
    """Draw a standard single-page invoice and return the PIL image."""
    items = items or [
        ("A4 Paper (ream)", "5", "4.50", "22.50"),
        ("Stapler", "2", "6.00", "12.00"),
        ("Ink Cartridge", "3", "18.00", "54.00"),
    ]
    W, H = 850, 1100
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.text((50, 40), vendor, font=F_TITLE(38), fill="black")
    d.text((50, 95), "123 Industrial Rd, Singapore 049315", font=F_BODY(18), fill="black")
    d.text((600, 45), title, font=F_TITLE(40), fill=(20, 60, 140))
    d.text((50, 160), f"Invoice #: {invoice_no}", font=F_BODY(), fill="black")
    d.text((50, 190), "Date: 2026-06-15", font=F_BODY(), fill="black")
    d.text((50, 220), "Bill to: Zimplistic Pte Ltd", font=F_BODY(), fill="black")
    y = 300
    d.rectangle([50, y, 800, y + 36], fill=(235, 235, 235))
    for x, label in ((60, "Description"), (480, "Qty"), (570, "Unit"), (690, "Amount")):
        d.text((x, y + 6), label, font=F_BOLD(), fill="black")
    y += 50
    subtotal = 0.0
    for desc, qty, unit, amt in items:
        d.text((60, y), desc, font=F_BODY(), fill="black")
        d.text((480, y), qty, font=F_BODY(), fill="black")
        d.text((570, y), unit, font=F_BODY(), fill="black")
        d.text((690, y), amt, font=F_BODY(), fill="black")
        subtotal += float(amt)
        y += 36
    y += 30
    tax = round(subtotal * 0.09, 2)
    d.text((560, y), "Subtotal:", font=F_BODY(), fill="black")
    d.text((700, y), f"{subtotal:.2f}", font=F_BODY(), fill="black"); y += 32
    d.text((560, y), "GST (9%):", font=F_BODY(), fill="black")
    d.text((700, y), f"{tax:.2f}", font=F_BODY(), fill="black"); y += 32
    d.text((560, y), "TOTAL (SGD):", font=F_BOLD(22), fill="black")
    d.text((700, y), total, font=F_BOLD(22), fill="black")
    d.text((50, H - 80), "Thank you for your business.", font=F_BODY(18), fill=(110, 110, 110))
    return img


def save_pdf(img, path, extra_pages=None):
    pages = extra_pages or []
    img.save(path, "PDF", resolution=150, save_all=bool(pages), append_images=pages)


def gen():
    os.makedirs(INPUTS, exist_ok=True)
    p = lambda n: os.path.join(INPUTS, n)

    # T1 clean invoice (PNG)
    clean = base_invoice()
    clean.save(p("T1_clean_invoice.png"))

    # T2 blurry invoice (JPG)
    base_invoice().filter(ImageFilter.GaussianBlur(2.4)).save(p("T2_blurry_invoice.jpg"), quality=70)

    # T3 rotated invoice (JPG) - rotate with white fill, expand canvas
    base_invoice().rotate(-13, expand=True, fillcolor="white").save(p("T3_rotated_invoice.jpg"), quality=85)

    # T4 low-contrast scan (JPG)
    low = ImageEnhance.Contrast(base_invoice()).enhance(0.32)
    low = ImageEnhance.Brightness(low).enhance(1.15)
    low.save(p("T4_low_contrast_scan.jpg"), quality=80)

    # T5 table-heavy packing list (PDF)
    big_items = [
        ("A4 Paper (ream)", "5", "4.50", "22.50"),
        ("Stapler", "2", "6.00", "12.00"),
        ("Ink Cartridge", "3", "18.00", "54.00"),
        ("Whiteboard Marker (box)", "4", "9.20", "36.80"),
        ("Sticky Notes (pack)", "10", "2.10", "21.00"),
        ("USB-C Cable", "6", "7.50", "45.00"),
        ("Desk Lamp", "2", "29.00", "58.00"),
        ("Notebook A5", "12", "3.40", "40.80"),
        ("Binder Clips (box)", "8", "1.75", "14.00"),
        ("Printer Toner", "1", "89.00", "89.00"),
        ("Mouse Pad", "5", "4.00", "20.00"),
        ("Highlighter (set)", "7", "5.25", "36.75"),
    ]
    save_pdf(base_invoice(title="PACKING LIST", items=big_items, total="500.00"), p("T5_table_invoice.pdf"))

    # T6 long 10-page PDF
    pages = []
    for i in range(2, 11):
        pg = Image.new("RGB", (850, 1100), "white")
        dd = ImageDraw.Draw(pg)
        dd.text((50, 40), f"Statement of Account — Page {i} of 10", font=F_TITLE(28), fill="black")
        for line in range(20):
            dd.text((50, 110 + line * 38),
                    f"2026-06-{(i+line) % 28 + 1:02d}  Txn #{1000+i*20+line}  "
                    f"Amount: {((i*7+line*3) % 90)+10}.{(line*7) % 100:02d}  SGD",
                    font=F_BODY(18), fill="black")
        pages.append(pg)
    cover = Image.new("RGB", (850, 1100), "white")
    dc = ImageDraw.Draw(cover)
    dc.text((50, 60), "Acme Office Supplies Ltd", font=F_TITLE(36), fill="black")
    dc.text((50, 130), "Monthly Statement of Account (10 pages)", font=F_BODY(22), fill="black")
    save_pdf(cover, p("T6_long_10_page.pdf"), extra_pages=pages)

    # T7 mixed text + image PDF
    mix = Image.new("RGB", (850, 1100), "white")
    dm = ImageDraw.Draw(mix)
    dm.text((50, 40), "Product Brochure — SmartDesk Pro", font=F_TITLE(32), fill="black")
    dm.rectangle([50, 110, 420, 380], fill=(70, 120, 200))
    dm.text((90, 230), "[ product photo ]", font=F_BOLD(22), fill="white")
    para = ("The SmartDesk Pro is an adjustable standing desk with a built-in\n"
            "controller, cable management, and three memory presets. Designed\n"
            "for hybrid offices, it supports up to 120kg and adjusts in 8 seconds.")
    dm.multiline_text((450, 120), para, font=F_BODY(18), fill="black", spacing=8)
    dm.text((50, 430), "Specifications", font=F_BOLD(24), fill="black")
    for i, spec in enumerate(["Height range: 70–120 cm", "Max load: 120 kg",
                              "Motor: dual, 8s full travel", "Warranty: 5 years",
                              "Price: SGD 749.00"]):
        dm.text((50, 480 + i * 36), f"• {spec}", font=F_BODY(18), fill="black")
    save_pdf(mix, p("T7_mixed_layout.pdf"))

    # T8 handwritten field on printed form (JPG)
    form = Image.new("RGB", (850, 1100), "white")
    df = ImageDraw.Draw(form)
    df.text((50, 40), "DELIVERY RECEIPT", font=F_TITLE(34), fill="black")
    fields = [("Received by:", "John Tan"), ("Date:", "15 / 6 / 2026"),
              ("Items:", "3 boxes, 1 pallet"), ("Condition:", "Good — no damage"),
              ("Amount paid:", "$ 96.47"), ("Signature:", "J. Tan")]
    y = 160
    for label, hand in fields:
        df.text((50, y), label, font=F_BODY(22), fill="black")
        df.line([(300, y + 32), (760, y + 32)], fill=(150, 150, 150), width=1)
        df.text((320, y - 4), hand, font=F_HAND(30), fill=(20, 40, 120))
        y += 90
    form.save(p("T8_handwritten_form.jpg"), quality=88)

    # T9 wrong-total invoice (PDF) — printed total 100.00, should be 96.47
    save_pdf(base_invoice(total="100.00"), p("T9_wrong_total_invoice.pdf"))

    # T10 multilingual document (PDF) — EN / FR / ZH / JP
    ml = Image.new("RGB", (850, 1100), "white")
    dl = ImageDraw.Draw(ml)
    dl.text((50, 40), "INVOICE / FACTURE / 发票 / 請求書", font=F_CJK(30), fill="black")
    rows = [
        ("English:  Office chair, qty 2, total SGD 240.00", F_BODY(22)),
        ("Français: Chaise de bureau, qté 2, total 240,00 SGD", F_BODY(22)),
        ("中文：     办公椅，数量 2，合计 240.00 新元", F_CJK(22)),
        ("日本語：   オフィスチェア、数量 2、合計 240.00 シンガポールドル", F_JP(22)),
        ("Vendor / Fournisseur / 供应商 / 仕入先: Acme Pte Ltd", F_CJK(20)),
        ("Date / 日期 / 日付: 2026-06-15", F_CJK(20)),
    ]
    y = 130
    for text, fnt in rows:
        dl.text((50, y), text, font=fnt, fill="black")
        y += 70
    save_pdf(ml, p("T10_multilingual_doc.pdf"))

    print("Generated synthetic inputs:")
    for n in sorted(os.listdir(INPUTS)):
        if n != "README.md":
            print("  ", n)


if __name__ == "__main__":
    gen()
