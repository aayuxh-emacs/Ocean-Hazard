import google.generativeai as genai
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OceanHazardDetector:
    def __init__(self, api_key: str):
        """
        Initialize the Ocean Hazard Detector with Gemini API
        """
        genai.configure(api_key= "API_KEY")
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.vision_model = genai.GenerativeModel('gemini-2.5-flash-vision')
        
    def create_hazard_analysis_prompt(self, location: str, time_range: str = "24 hours") -> str:
        """
        Create a structured prompt for hazard analysis
        """
        return f"""
        You are an ocean safety expert analyzing real-time data. Search the web for current ocean hazards and conditions near {location} within the last {time_range}.

        Look for information about:
        1. IMMEDIATE HAZARDS:
           - Shark sightings or attacks
           - Jellyfish blooms
           - Riptide/rip current warnings
           - Large waves or dangerous surf
           - Water pollution incidents
           - Beach closures

        2. WEATHER-RELATED:
           - Storm conditions
           - High winds
           - Tsunami warnings
           - Storm surge alerts

        3. OFFICIAL SOURCES:
           - Coast Guard announcements
           - Lifeguard reports
           - Local government warnings
           - Weather service alerts

        4. SOCIAL MEDIA REPORTS:
           - User reports of dangerous conditions
           - Photos/videos of hazardous situations
           - Local community warnings

        Analyze the credibility of each source and return results in this EXACT JSON format:

        {{
            "location": "{location}",
            "analysis_time": "current timestamp",
            "overall_risk_level": "LOW/MEDIUM/HIGH/EXTREME",
            "hazards": [
                {{
                    "type": "hazard type (shark, riptide, pollution, etc.)",
                    "severity": "LOW/MEDIUM/HIGH/EXTREME", 
                    "location_specific": "specific beach/area if mentioned",
                    "description": "detailed description of the hazard",
                    "source": "where this information came from",
                    "credibility": "HIGH/MEDIUM/LOW based on source reliability",
                    "reported_time": "when this was reported",
                    "coordinates": "lat,lng if available",
                    "recommended_action": "what people should do"
                }}
            ],
            "safe_areas": ["list of areas reported as safe"],
            "general_conditions": "overall summary of ocean conditions",
            "last_updated": "timestamp"
        }}

        IMPORTANT: Return ONLY valid JSON. No additional text or explanation.
        """

    async def analyze_current_hazards(self, location: str) -> Dict:
        """
        Analyze current ocean hazards for a specific location
        """
        try:
            prompt = self.create_hazard_analysis_prompt(location)
            response = self.model.generate_content(prompt)
            
            if not response.text:
                logger.warning(f"No data returned for {location}")
                return self._create_error_response(location, "no_data")
            
            # Clean up response text
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith('```'):
                response_text = response_text[3:-3].strip()
                
            try:
                hazard_data = json.loads(response_text)
                
                # Add metadata
                hazard_data['processed_at'] = datetime.now().isoformat()
                hazard_data['source'] = 'gemini_web_analysis'
                
                logger.info(f"Successfully analyzed hazards for {location}")
                return hazard_data
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}\nResponse: {response_text}")
                return self._create_error_response(location, "json_parse_error")
                
        except Exception as e:
            logger.error(f"Error analyzing hazards: {e}")
            return self._create_error_response(location, str(e))

    async def analyze_user_report(self, report_text: str, location: str, image_data: Optional[bytes] = None) -> Dict:
        """
        Analyze a user-submitted report about ocean conditions
        """
        try:
            base_prompt = f"""
            Analyze this user report about ocean conditions at {location}:
            
            User Report: "{report_text}"
            
            Determine:
            1. Is this a legitimate safety concern?
            2. What type of hazard (if any) is being reported?
            3. How urgent is this report?
            4. What's the credibility level?
            
            Return in JSON format:
            {{
                "is_hazard": true/false,
                "hazard_type": "type if applicable",
                "urgency": "LOW/MEDIUM/HIGH/CRITICAL",
                "credibility": "LOW/MEDIUM/HIGH",
                "recommended_action": "what should be done",
                "requires_verification": true/false,
                "location_specific": "specific area mentioned",
                "summary": "brief summary of the report"
            }}
            """
            
            if image_data:
                # Use vision model for image analysis
                response = self.vision_model.generate_content([base_prompt, image_data])
            else:
                response = self.model.generate_content(base_prompt)
            
            # Parse response
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3].strip()
                
            analysis = json.loads(response_text)
            analysis['processed_at'] = datetime.now().isoformat()
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing user report: {e}")
            return {"error": str(e), "is_hazard": False}

async def analyze_batch_social_posts(self, posts: List[str], location: str) -> Dict:
    """
    Analyze multiple social media posts at once
    """
    try:
        posts_text = "\n\n---POST---\n".join([f"Post {i+1}: {post}" for i, post in enumerate(posts)])
        
        prompt = f"""
        Analyze these social media posts about ocean conditions near {location}:
        
        {posts_text}
        
        For each post that mentions a potential ocean hazard:
        1. Extract relevant safety information
        2. Assess credibility 
        3. Determine if it requires attention
        
        Return JSON:
        {{
            "location": "{location}",
            "total_posts_analyzed": {len(posts)},
            "hazard_posts": [
                {{
                    "post_number": 1,
                    "hazard_type": "type",
                    "severity": "LOW/MEDIUM/HIGH",
                    "credibility": "LOW/MEDIUM/HIGH",
                    "summary": "what the post reports",
                    "location_mentioned": "specific area if any"
                }}
            ],
            "overall_assessment": "summary of findings",
            "recommendation": "what action to take if any"
        }}
        """
        
        response = await asyncio.to_thread(self.model.generate_content, prompt)
        response_text = response.text.strip()
        
        if response_text.startswith('```json'):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith('```'):
            response_text = response_text[3:-3].strip()
            
        return json.loads(response_text)
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        return {"error": str(e)}

    def _create_error_response(self, location: str, error: str) -> Dict:
        """
        Create a standardized error response
        """
        return {
            "location": location,
            "overall_risk_level": "UNKNOWN",
            "hazards": [],
            "error": error,
            "analysis_time": datetime.now().isoformat()
        }

    async def get_multi_location_analysis(self, locations: List[str]) -> Dict:
        """
        Analyze multiple locations simultaneously
        """
        tasks = [self.analyze_current_hazards(location) for location in locations]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "analysis_time": datetime.now().isoformat(),
            "locations": {
                location: result if not isinstance(result, Exception) else {"error": str(result)}
                for location, result in zip(locations, results)
            }
        }

# Integration with your app
class HazardMonitoringService:
    def __init__(self, api_key: str):
        self.detector = OceanHazardDetector(api_key)
        
    async def continuous_monitoring(self, locations: List[str], interval_minutes: int = 30):
        """
        Continuously monitor locations for hazards
        """
        while True:
            try:
                print(f"Monitoring {len(locations)} locations...")
                results = await self.detector.get_multi_location_analysis(locations)
                
                # Process results - send alerts, update database, etc.
                for location, data in results["locations"].items():
                    if data.get("overall_risk_level") in ["HIGH", "EXTREME"]:
                        await self.send_alert(location, data)
                
                # Wait before next check
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def send_alert(self, location: str, hazard_data: Dict):
        """
        Send alert when high-risk hazard is detected
        """
        print(f"🚨 HIGH RISK ALERT for {location}:")
        print(f"Risk Level: {hazard_data['overall_risk_level']}")
        for hazard in hazard_data.get('hazards', []):
            print(f"- {hazard['type']}: {hazard['description']}")
        # Integrate with your notification system here

# FastAPI Backend Setup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust for your React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HazardRequest(BaseModel):
    location: str

class UserReportRequest(BaseModel):
    report: str
    location: str

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

detector = OceanHazardDetector(API_KEY)

@app.post("/analyze-hazards")
async def analyze_hazards(request: HazardRequest):
    try:
        return await detector.analyze_current_hazards(request.location)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-user-report")
async def analyze_user_report(request: UserReportRequest):
    try:
        return await detector.analyze_user_report(request.report, request.location)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Usage Examples for Standalone Testing
async def main():
    load_dotenv()
    API_KEY = os.getenv("GEMINI_API_KEY")
    if not API_KEY:
        raise ValueError("GEMINI_API_KEY not found in .env file")
    detector = OceanHazardDetector(API_KEY)
    
    # Example 1: Analyze current hazards for a location
    print("=== CURRENT HAZARD ANALYSIS ===")
    hazards = await detector.analyze_current_hazards("Santa Monica Beach, California")
    print(json.dumps(hazards, indent=2))
    
    # Example 2: Analyze user report
    print("\n=== USER REPORT ANALYSIS ===")
    user_report = "I saw a large shark about 100 yards from shore at Malibu beach this morning around 9am"
    analysis = await detector.analyze_user_report(user_report, "Malibu Beach, California")
    print(json.dumps(analysis, indent=2))
    
    # Example 3: Batch analyze social posts
    print("\n=== BATCH SOCIAL MEDIA ANALYSIS ===")
    sample_posts = [
        "Huge waves at Huntington Beach today, lifeguards telling everyone to stay out",
        "Beautiful day at Manhattan Beach, perfect swimming conditions!",
        "Warning: saw multiple jellyfish at Redondo Beach pier, got stung",
        "Storm coming in fast at Malibu, waves getting dangerous"
    ]
    batch_analysis = await detector.analyze_batch_social_posts(sample_posts, "Los Angeles County Beaches")
    print(json.dumps(batch_analysis, indent=2))
    
    # Example 4: Multi-location analysis
    print("\n=== MULTI-LOCATION ANALYSIS ===")
    locations = ["Santa Monica", "Venice Beach", "Manhattan Beach"]
    multi_analysis = await detector.get_multi_location_analysis(locations)
    print(json.dumps(multi_analysis, indent=2))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
