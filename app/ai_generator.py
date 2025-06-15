# app/ai_generator.py
import openai
import json
import re
from typing import List, Dict, Optional
from app.vector_store import VectorStore

class AIResponseGenerator:
    def __init__(self, api_key: str, vector_store: VectorStore):
        self.client = openai.OpenAI(api_key=api_key)
        self.vector_store = vector_store
        
    def analyze_tender_requirements(self, document_text: str) -> Dict[str, Any]:
        """Analyze tender document to understand requirements"""
        prompt = f"""
        Analyze this tender document and extract key information:
        
        1. Tender type and industry
        2. Key requirements and evaluation criteria
        3. Required sections/responses
        4. Deadline and submission requirements
        5. Company qualifications needed
        
        Document text (first 4000 chars):
        {document_text[:4000]}
        
        Return a structured JSON response with the analysis.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            # Try to parse as JSON, fallback to text
            try:
                return json.loads(content)
            except:
                return {"analysis": content}
                
        except Exception as e:
            print(f"Error analyzing tender: {e}")
            return {"error": str(e)}
    
    def generate_field_response(self, field_name: str, context: str = "", 
                              company_info: Dict = None) -> str:
        """Generate response for a specific field"""
        
        # Search for similar past responses
        similar_responses = self.vector_store.search_similar(field_name, limit=3)
        
        # Build context from similar responses
        context_examples = ""
        if similar_responses:
            context_examples = "\n\nExamples from past successful responses:\n"
            for i, resp in enumerate(similar_responses, 1):
                context_examples += f"{i}. {resp.get('content', '')[:200]}...\n"
        
        # Company information context
        company_context = ""
        if company_info:
            company_context = f"""
            Company Information:
            - Name: {company_info.get('name', 'N/A')}
            - Industry: {company_info.get('industry', 'N/A')}
            - Experience: {company_info.get('experience', 'N/A')}
            - Capabilities: {company_info.get('capabilities', 'N/A')}
            """
        
        prompt = f"""
        You are an expert tender response writer. Generate a professional, comprehensive response for this tender field.
        
        Field/Question: {field_name}
        
        Additional Context: {context}
        
        {company_context}
        
        {context_examples}
        
        Requirements:
        1. Write a professional, detailed response
        2. Address all aspects of the question/requirement
        3. Use formal business language
        4. Be specific and provide concrete examples where appropriate
        5. Ensure compliance with tender requirements
        6. Keep response between 100-500 words unless the question requires more detail
        
        Generate the response:
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return f"Error generating response for: {field_name}"
    
    def improve_response(self, original_response: str, feedback: str) -> str:
        """Improve response based on feedback"""
        prompt = f"""
        Improve this tender response based on the feedback provided:
        
        Original Response:
        {original_response}
        
        Feedback:
        {feedback}
        
        Generate an improved version that addresses the feedback while maintaining professional quality.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=2000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error improving response: {e}")
            return original_response
    
    def generate_executive_summary(self, all_responses: Dict[str, str], 
                                 tender_info: Dict) -> str:
        """Generate executive summary for the tender response"""
        
        responses_summary = "\n".join([f"- {field}: {resp[:100]}..." 
                                     for field, resp in all_responses.items()])
        
        prompt = f"""
        Generate a compelling executive summary for this tender response.
        
        Tender Information:
        {json.dumps(tender_info, indent=2)}
        
        Key Response Areas:
        {responses_summary}
        
        Create a 2-3 paragraph executive summary that:
        1. Highlights our key strengths and capabilities
        2. Demonstrates understanding of the requirements
        3. Positions our company as the ideal choice
        4. Is compelling and professional
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating executive summary: {e}")
            return "Executive Summary: [Error generating summary]"
