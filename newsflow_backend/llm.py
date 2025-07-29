"""
Language model integration for NewsFlow AI Editor.

Enhanced LLM processing with fine-tuned prompts for:
- Complete removal of source website references
- Minimal but effective content improvements
- Maintaining Albanian language quality
- Avoiding identical content to prevent detection
"""

from typing import Optional
import requests
import json
import os
from jinja2 import Template
import re

# Konfigurimi për OpenRouter
OPENROUTER_API_KEY = "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"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "DeepSeek: DeepSeek V3 0324 (free)"

def clean_content_from_llm_output(content: str) -> str:
    """Final cleaning of LLM output to ensure no source references remain."""
    # Remove any remaining website patterns that might slip through
    patterns_to_remove = [
        r'\b\w+\.(com|al|net|org|info|co\.uk)\b',
        r'\b(burim|source|nga|sipas|lexuar në|më shumë në)\s*[:]\s*[\w\s]+',
        r'\b(foto|image|video)\s*[:]\s*[\w\s]+',
        r'©\s*[\w\s]+',
        r'\b(All rights reserved|Të drejtat e rezervuara)\b',
        r'\b(më shumë|lexo|shiko|ndiq)\s+(në|here|këtu)[\w\s]*',
        r'\b\d+\s*komente?\b'
    ]
    
    for pattern in patterns_to_remove:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    # Clean up excessive whitespace
    content = ' '.join(content.split())
    return content

def process_article(article, instruction: Optional[str] = None) -> str:
    """Process an article's content using OpenRouter LLM with professional journalism standards."""
    try:
        # Extract article data
        title = getattr(article, 'title', 'No Title')
        content = getattr(article, 'content', 'No Content')
        url = getattr(article, 'url', '')
        images = getattr(article, 'images', [])
        
        # Keep more content for better processing - use up to 1200 characters
        if len(content) > 1200:
            content = content[:1200] + "..."
        
        # Load the professional journalism prompt template
        template_path = os.path.join(os.path.dirname(__file__), 'llm_prompt.jinja2')
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Create Jinja2 template
        template = Template(template_content)
        
        # Render the prompt with article data
        prompt = template.render(
            title=title,
            content=content,
            url=url,
            images=images
        )
        
        # Create request payload with higher token limit for JSON output
        data = {
            "model": "DeepSeek: DeepSeek V3 0324 (free)",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,  # Higher limit for structured JSON response
            "temperature": 0.3
        }
        
        # Make request to OpenRouter
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json=data,
            timeout=30
        )
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and result["choices"]:
                llm_response = result["choices"][0]["message"]["content"]
                
                # Try to parse JSON response
                try:
                    # Extract JSON from response (may contain markdown code blocks)
                    if "```json" in llm_response:
                        json_start = llm_response.find("```json") + 7
                        json_end = llm_response.find("```", json_start)
                        json_content = llm_response[json_start:json_end].strip()
                    elif "{" in llm_response and "}" in llm_response:
                        json_start = llm_response.find("{")
                        json_end = llm_response.rfind("}") + 1
                        json_content = llm_response[json_start:json_end]
                    else:
                        # No JSON found, return as formatted text
                        return clean_content_from_llm_output(llm_response)
                    
                    # Parse JSON
                    structured_content = json.loads(json_content)
                    
                    # Format the structured content into a readable article
                    formatted_article = f"{structured_content.get('title', '')}\n\n"
                    
                    # Add introduction
                    if structured_content.get('content', {}).get('introduction'):
                        formatted_article += structured_content['content']['introduction'] + "\n\n"
                    
                    # Add body paragraphs
                    if structured_content.get('content', {}).get('body'):
                        for paragraph in structured_content['content']['body']:
                            if paragraph.strip():
                                formatted_article += paragraph + "\n\n"
                    
                    # Add conclusion
                    if structured_content.get('content', {}).get('conclusion'):
                        formatted_article += structured_content['content']['conclusion']
                    
                    # Apply final cleaning
                    formatted_article = clean_content_from_llm_output(formatted_article)
                    return formatted_article.strip()
                    
                except json.JSONDecodeError:
                    # If JSON parsing fails, return cleaned text
                    return clean_content_from_llm_output(llm_response)
                
            else:
                return f"{content}\n\n[OpenRouter: No response received]"
        else:
            print(f"OpenRouter Error {response.status_code}: {response.text}")
            return f"{content}\n\n[OpenRouter Error: {response.status_code}]"
            
    except Exception as e:
        print(f"OpenRouter Exception: {e}")
        return f"{getattr(article, 'content', 'No Content')}\n\n[Error: {str(e)}]"

async def process_article_with_instructions(content: str, instructions: str) -> str:
    """
    Process article content with specific user instructions and strict source removal.
    
    Args:
        content: The article content to edit
        instructions: Specific editing instructions from user
        
    Returns:
        Edited content or None if processing fails
    """
    try:
        print(f"🤖 Starting LLM edit with instructions: {instructions[:50]}...")
        print(f"📝 Content length: {len(content)} chars")
        
        if not content or not content.strip():
            print("❌ Empty content provided")
            return None
            
        if not instructions or not instructions.strip():
            print("❌ Empty instructions provided")
            return None
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Limit content to prevent token overflow
        max_content_length = 700
        if len(content) > max_content_length:
            content_to_process = content[:max_content_length] + "..."
            print(f"⚠️ Content truncated to {max_content_length} chars")
        else:
            content_to_process = content
        
        # Enhanced custom prompt with strict source removal
        prompt = f"""Ti je një redaktor ekspert i lajmeve shqipe. 

RREGULLA ABSOLUTE (MOS I SHKEL ASNJËHERË):
❌ MOS PËRMENDJE ASNJË EMR FAQE WEB (shkodrazone, telegrafi, albeu, etj.)
❌ MOS SHKRUAJ ASNJË URL OSE LINK (.com, .al, .net, .org)
❌ MOS SHKRUAJ BURIM, SOURCE, NGA, SIPAS + emër faqe
❌ MOS LË COPYRIGHT, ©, TË DREJTAT E REZERVUARA
❌ MOS SHKRUAJ "MË SHUMË NË", "LEXO NË", "SHIKO NË"

INSTRUKSIONET E REDAKTIMIT: {instructions}

TEKSTI ORIGJINAL:
{content_to_process}

DETYRA:
1. Zbato instruksionet e dhëna të redaktimit
2. HEKE plotësisht çdo referencë të faqes së burimit
3. Ruaj të gjitha faktet dhe informacionet e rëndësishme
4. Shkruaj në shqipe natyrore dhe profesionale
5. Mos shto informacione të reja që nuk janë në tekst
6. Bëj ndryshime sa për të mos qenë identik me origjinalin

TEKSTI I REDAKTUAR (vetëm teksti, pa komente):"""

        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": 700,
            "temperature": 0.2  # Very low temperature for consistent source removal
        }

        print(f"📤 Sending request to OpenRouter...")
        
        # Use asyncio to make the request non-blocking
        import asyncio
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                print(f"📥 LLM Response status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    if 'choices' in result and len(result['choices']) > 0:
                        edited_content = result['choices'][0]['message']['content'].strip()
                        # Apply final cleaning to remove any remaining source references
                        edited_content = clean_content_from_llm_output(edited_content)
                        print(f"✅ LLM Edit Success: {len(edited_content)} chars")
                        return edited_content
                    else:
                        print("❌ LLM Edit: No choices in response")
                        print(f"Response data: {result}")
                        return None
                else:
                    error_text = await response.text()
                    print(f"❌ LLM Edit Error: {response.status} - {error_text}")
                    return None

    except Exception as e:
        print(f"❌ LLM Edit Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# Predefined editing instructions for common use cases
PREDEFINED_INSTRUCTIONS = {
    "improve_albanian": "Përmirëso shqipen dhe gramatikën, bëje më profesionale dhe të qartë",
    "make_journalistic": "Bëje më gazetaresk dhe objektiv, përmirëso strukturën e lajmit",
    "shorten": "Shkurtoje duke ruajtur informacionet më të rëndësishme",
    "expand": "Zgjato duke shpjeguar më mirë detajet, por mos shto fakte të reja",
    "dramatize": "Bëje më dramatik dhe tërheqës për lexuesit",
    "formalize": "Bëje më formal dhe akademik në ton"
}

def get_predefined_instruction(instruction_key: str) -> str:
    """Get predefined instruction by key."""
    return PREDEFINED_INSTRUCTIONS.get(instruction_key, instruction_key)