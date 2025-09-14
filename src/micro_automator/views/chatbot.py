import os
import logging
import google.generativeai as genai
from flask import Blueprint, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# This will use the API key already configured in your app.py
chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/ask', methods=['POST'])
def ask_chatbot():
    data = request.get_json()
    if not data or not data.get('question'):
        return jsonify({"error": "A 'question' is required."}), 400

    user_question = data['question']
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # This is a system prompt that gives the AI context about its role.
        prompt = f"""
        You are "Insure-Agent AI Assistant," a friendly and helpful chatbot integrated into an insurance agent's dashboard. Your purpose is to guide the user on how to use the application. Be concise and helpful.

        Here are the app's main features:
        - Dashboard: Shows an overview with stats and follow-ups.
        - Clients: A CRM to manage Active, Engaged, and Prospective clients. New clients can be added manually or through document uploads.
        - Documents: An AI-powered tool to upload PDFs/images (like Aadhaar/PAN cards) to automatically extract data and pre-fill an onboarding form.
        - Reconciliation: A tool to upload bank and policy PDFs to automatically match financial transactions.

        User's question: "{user_question}"

        Your answer:
        """
        
        response = model.generate_content(prompt)
        
        return jsonify({"answer": response.text})

    except Exception as e:
        logger.error(f"Chatbot API error: {e}", exc_info=True)
        return jsonify({"error": "Sorry, I couldn't process that request right now."}), 500