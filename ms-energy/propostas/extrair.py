import pypdfium2 as pdfium, sys, os
src = sys.argv[1]; out = sys.argv[2]
pdf = pdfium.PdfDocument(src)
for i, page in enumerate(pdf):
    page.render(scale=2).to_pil().save(os.path.join(out, f"pag{i+1}.png"))
    n = 0
    for obj in page.get_objects(filter=[pdfium.raw.FPDF_PAGEOBJ_IMAGE]):
        try:
            im = obj.get_bitmap(render=False).to_pil()
            l, b, r, t = obj.get_pos()
            im.convert("RGB").save(os.path.join(out, f"p{i+1}_{n}_{im.width}x{im.height}_{int(l)}_{int(t)}.jpg"), quality=92)
            n += 1
        except Exception as e:
            print("erro", i+1, e)
    print(i+1, n)
