import openai
from django.conf import settings
from typing import List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

class AIContentGenerator:
    """Generates tender responses using OpenAI API"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def generate_field_content(self, field_info: Dict[str, Any], 
                             reference_content: str, 
                             project_context: str = "") -> str:
        """Generate content for a specific field using AI"""
        
        field_name = field_info.get('field_name', 'Unknown Field')
        field_type = field_info.get('field_type', 'text')
        
        prompt = self._create_field_prompt(field_name, field_type, reference_content, project_context)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Updated model name
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert tender response writer for an Australian business. 
                        Generate professional, compliant responses based on past submissions. 
                        Keep responses concise and relevant."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except openai.APIError as e:
            logger.error(f"OpenAI API error for field {field_name}: {e}")
            return f"Error generating content for {field_name}. Please try again."
        except Exception as e:
            logger.error(f"Unexpected error for field {field_name}: {e}")
            return f"[Please fill in content for {field_name}]"
    
    def _create_field_prompt(self, field_name: str, field_type: str, 
                           reference_content: str, project_context: str) -> str:
        """Create a detailed prompt for field content generation"""
        
        # Limit reference content to avoid token limits
        limited_reference = reference_content[:1500] if reference_content else "No reference content available."
        
        prompt = f"""
        Generate a professional tender response for: {field_name}
        
        Field Type: {field_type}
        Project Context: {project_context}
        
        Reference Content:
        {limited_reference}
        
        Requirements:
        - Professional Australian business language
        - Concise but comprehensive (2-4 sentences)
        - Directly address the field requirement
        - Use reference content as guidance
        
        Response:
        """
        
        return prompt
    
    def generate_bulk_content(self, fields: List[Dict[str, Any]], 
                            reference_content: str, 
                            project_context: str = "") -> Dict[str, str]:
        """Generate content for multiple fields"""
        
        results = {}
        
        for field in fields:
            field_id = str(field.get('id'))
            try:
                content = self.generate_field_content(field, reference_content, project_context)
                results[field_id] = content
            except Exception as e:
                logger.error(f"Error generating content for field {field_id}: {e}")
                results[field_id] = f"[Content for {field.get('field_name', 'Unknown Field')}]"
        
        return results
