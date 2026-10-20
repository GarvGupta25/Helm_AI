from io import BytesIO

import pytest
from fastapi import HTTPException
from reportlab.pdfgen import canvas

from app.documents import extract_claim_attachment, extract_identity


@pytest.mark.parametrize("kind", ["claim", "identity"])
@pytest.mark.parametrize("fixture", ["corrupt", "unsupported", "too_many_pages", "oversized_page", "too_large"])
def test_documents_reject_unsafe_inputs_before_ocr(kind, fixture):
    if fixture in {"too_many_pages", "oversized_page"}:
        output = BytesIO()
        pdf = canvas.Canvas(output, pagesize=(100000, 100000) if fixture == "oversized_page" else (500, 700))
        for _ in range(6 if fixture == "too_many_pages" else 1):
            pdf.showPage()
        pdf.save()
        content = output.getvalue()
    else:
        content = {"corrupt": b"%PDF-corrupt", "unsupported": b"<html>not a document</html>",
                   "too_large": b"x" * (10 * 1024 * 1024 + 1)}[fixture]
    with pytest.raises(HTTPException) as error:
        if kind == "claim":
            extract_claim_attachment(content, "invoice.pdf", "bill")
        else:
            extract_identity(content)
    assert error.value.status_code == (413 if fixture == "too_large" else 422)
