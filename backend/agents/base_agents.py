import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

class BaseAgent:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-2.0-flash-lite')

    def generate_response(self, prompt):
        response = self.model.generate_content(prompt)
        return response.text

class PropertySearchAgent(BaseAgent):
    def search_properties(self, query):
        # Implement property search logic using Gemini API
        prompt = f"Search for real estate properties matching the following criteria: {query}"
        return self.generate_response(prompt)

class AmenitiesAgent(BaseAgent):
    def get_amenities(self, property_id):
        # Mock function to get property amenities
        prompt = f"List all amenities for property ID: {property_id}"
        return self.generate_response(prompt)

class NegotiationAgent(BaseAgent):
    def negotiate(self, property_id, offer):
        # Mock function for price negotiation
        prompt = f"Negotiate property {property_id} for offer: ${offer}"
        return self.generate_response(prompt)

class DealSealingAgent(BaseAgent):
    def seal_deal(self, property_id):
        # Mock function for finalizing the deal
        prompt = f"Process paperwork and finalize deal for property {property_id}"
        return self.generate_response(prompt)
