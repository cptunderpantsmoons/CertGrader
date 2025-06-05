"""
PokéCertify Gradio Frontend

This module implements the Gradio UI for card upload, verification, trading, collection viewing, and certificate generation.

Author: PokéCertify Team
"""

import gradio as gr
import requests
import qrcode
import io
import base64
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Shared config (to be imported from shared/config.py in production)
API_URL = "http://localhost:8000"

def upload_card(image, card_name, card_info, owner):
    """Upload a card for grading and storage."""
    try:
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        response = requests.post(
            f"{API_URL}/upload",
            files={"file": ("card.jpg", buffered.getvalue(), "image/jpeg")},
            data={"card_name": card_name, "card_info": card_info, "owner": owner}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def verify_card(card_id):
    """Retrieve card details for verification."""
    try:
        response = requests.get(f"{API_URL}/card/{card_id}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def trade_card(card_id, to_owner):
    """Initiate a card trade."""
    try:
        response = requests.post(f"{API_URL}/trade", json={"card_id": card_id, "to_owner": to_owner})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_collection(owner):
    """Retrieve all cards owned by a user."""
    try:
        response = requests.get(f"{API_URL}/collection/{owner}")
        response.raise_for_status()
        cards = response.json()
        return [
            (card["image_path"], f"{card['card_name']} ({card['grade']})")
            for card in cards
        ]
    except Exception as e:
        return [{"error": str(e)}]

def generate_certificate(card_id):
    """Generate a PDF certificate with QR code."""
    try:
        card = verify_card(card_id)
        if "error" in card:
            return None
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph(f"Card: {card['card_name']}", styles["Title"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Grade: {card['grade']}", styles["Normal"]))
        story.append(Paragraph(f"Owner: {card['owner']}", styles["Normal"]))
        story.append(Paragraph(f"Date: {card['date_added']}", styles["Normal"]))
        story.append(Spacer(1, 12))
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(f"{API_URL}/card/{card_id}")
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        story.append(Image(qr_buffer, width=100, height=100))
        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        return None

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# PokéCertify: AI-Powered Card Grading")

    with gr.Tab("Upload Card"):
        image_input = gr.Image(type="pil", label="Card Image")
        card_name_input = gr.Textbox(label="Card Name")
        card_info_input = gr.Textbox(label="Card Info")
        owner_input = gr.Textbox(label="Owner")
        upload_button = gr.Button("Upload and Grade", variant="primary")
        upload_output = gr.JSON(label="Grading Result")
        upload_button.click(
            fn=upload_card,
            inputs=[image_input, card_name_input, card_info_input, owner_input],
            outputs=upload_output
        )

    with gr.Tab("Verify Card"):
        card_id_input = gr.Textbox(label="Card ID")
        verify_button = gr.Button("Verify", variant="primary")
        verify_output = gr.JSON(label="Card Details")
        verify_button.click(
            fn=verify_card,
            inputs=card_id_input,
            outputs=verify_output
        )

    with gr.Tab("Trade Card"):
        trade_card_id_input = gr.Textbox(label="Card ID")
        to_owner_input = gr.Textbox(label="New Owner")
        trade_button = gr.Button("Trade", variant="primary")
        trade_output = gr.JSON(label="Trade Details")
        trade_button.click(
            fn=trade_card,
            inputs=[trade_card_id_input, to_owner_input],
            outputs=trade_output
        )

    with gr.Tab("My Collection"):
        collection_owner_input = gr.Textbox(label="Owner")
        collection_button = gr.Button("View Collection", variant="primary")
        collection_output = gr.Gallery(label="Your Cards", preview=True)
        collection_button.click(
            fn=get_collection,
            inputs=collection_owner_input,
            outputs=collection_output
        )

    with gr.Tab("Certificate"):
        cert_card_id_input = gr.Textbox(label="Card ID")
        cert_button = gr.Button("Generate Certificate", variant="primary")
        cert_output = gr.File(label="Certificate PDF")
        cert_button.click(
            fn=generate_certificate,
            inputs=cert_card_id_input,
            outputs=cert_output
        )

if __name__ == "__main__":
    demo.launch()