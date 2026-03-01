"""
Farming Expert Agent - Fixed Multi-Tool Version
Uses AgentTool to wrap single-tool sub-agents (bypasses multi-tool limit)
Supports: City | State | Pincode
Uses: OpenWeatherMap + Google Search
"""

import os
import asyncio
import requests
from typing import Dict, Any

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools import google_search, AgentTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.tools import ToolContext
from google.genai import types as genai_types

# Load .env (local + global)
_HERE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_HERE, ".env"), override=True)
load_dotenv(override=True)

# Normalize Gemini key env var for ADK/google-genai
if not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY", "") or os.getenv("GENAI_API_KEY", "")

# =============================================================================
# TOOL 1: WEATHER TOOL (NO LAT/LON)
# =============================================================================

def get_weather(location: str, tool_context: ToolContext) -> str:
    """
    Get current weather data for any Indian location.
    
    Args:
        location (str): City name, state, or 6-digit Indian pincode
        tool_context (ToolContext): ADK tool context for state management
        
    Returns:
        str: Comprehensive weather report or error message
    """
    api_key = os.environ.get("OPENWEATHER_API_KEY", "")
    if not api_key:
        return "Weather error: OPENWEATHER_API_KEY not configured."

    location = location.strip()

    try:
        if location.isdigit() and len(location) == 6:
            url = (
                f"https://api.openweathermap.org/data/2.5/weather?"
                f"zip={location},IN&appid={api_key}&units=metric"
            )
        else:
            url = (
                f"https://api.openweathermap.org/data/2.5/weather?"
                f"q={location},IN&appid={api_key}&units=metric"
            )

        response = requests.get(url, timeout=10)
        data = response.json()

        if response.status_code != 200:
            return f"Weather error: {data.get('message', 'Location not found')}"

        main = data.get("main", {})
        weather = data.get("weather", [{}])[0]
        wind = data.get("wind", {})
        clouds = data.get("clouds", {})
        sys = data.get("sys", {})
        coord = data.get("coord", {})
        rain = data.get("rain", {})
        snow = data.get("snow", {})

        # Format weather data with all available fields
        weather_report = (
            f"Weather Summary:\n"
            f"- Location: {data.get('name')}, {sys.get('country', 'N/A')}\n"
            f"- Coordinates: {coord.get('lat', 'N/A')}, {coord.get('lon', 'N/A')}\n"
            f"- Temperature: {main.get('temp', 'N/A')}°C (feels like: {main.get('feels_like', 'N/A')}°C)\n"
            f"- Min/Max: {main.get('temp_min', 'N/A')}°C / {main.get('temp_max', 'N/A')}°C\n"
            f"- Condition: {weather.get('main', 'N/A')} - {weather.get('description', 'N/A')}\n"
            f"- Humidity: {main.get('humidity', 'N/A')}%\n"
            f"- Pressure: {main.get('pressure', 'N/A')} hPa\n"
            f"- Sea Level Pressure: {main.get('sea_level', 'N/A')} hPa\n"
            f"- Ground Level Pressure: {main.get('grnd_level', 'N/A')} hPa\n"
            f"- Visibility: {data.get('visibility', 'N/A')} meters\n"
            f"- Wind Speed: {wind.get('speed', 'N/A')} m/s\n"
            f"- Wind Direction: {wind.get('deg', 'N/A')}°\n"
            f"- Wind Gust: {wind.get('gust', 'N/A')} m/s\n"
            f"- Cloudiness: {clouds.get('all', 'N/A')}%\n"
        )

        # Add rain data if available
        if rain:
            weather_report += f"- Rain (1h): {rain.get('1h', 'N/A')} mm\n"
        
        # Add snow data if available
        if snow:
            weather_report += f"- Snow (1h): {snow.get('1h', 'N/A')} mm\n"

        weather_report += (
            f"- Sunrise: {sys.get('sunrise', 'N/A')}\n"
            f"- Sunset: {sys.get('sunset', 'N/A')}\n"
            f"- Timezone: {data.get('timezone', 'N/A')} seconds from UTC\n"
            f"- Data Time: {data.get('dt', 'N/A')}\n"
        )

        # Store weather query in state for tracking
        tool_context.state["temp:last_weather_query"] = location
        tool_context.state["temp:last_weather_result"] = weather_report
        
        return weather_report

    except Exception as e:
        return f"Weather error: {str(e)}"

# =============================================================================
# SUB-AGENTS (each with ONE tool only)
# =============================================================================

weather_agent = LlmAgent(
    name="WeatherAgent",
    model="gemini-2.0-flash",
    description="Specialist in getting current weather for Indian locations (city/state/pincode). Always call get_weather tool.",
    instruction="You are a weather specialist. When asked about weather, use the get_weather tool with the location parameter. Return the complete weather information provided by the tool.",
    tools=[get_weather],
)

search_agent = LlmAgent(
    name="SearchAgent", 
    model="gemini-2.0-flash",
    description="Specialist in Google Search for farming/agriculture info in India.",
    instruction="You are an agricultural research specialist. Use google_search to find:\n"
                "- Crop suitability for specific seasons and locations in India\n"
                "- Planting calendars and timing\n"
                "- Soil requirements and irrigation needs\n"
                "- Pest management and fertilizer recommendations\n"
                "- Market prices and profitability\n"
                "\n"
                "Always search with specific terms like 'best [crop] [season] [location] India' or '[crop] planting time [state]'. Return comprehensive, actionable information from search results.",
    tools=[google_search],
)

# =============================================================================
# MAIN FARMING EXPERT AGENT (uses AgentTool-wrapped sub-agents)
# =============================================================================

farming_agent = LlmAgent(
    name="FarmingExpertAgent",
    model="gemini-2.0-flash",
    description="Expert Indian Agriculture Advisor with dynamic query handling and comprehensive farming knowledge.",
    instruction="""
You are an Expert Indian Farming Advisor for {user:name}. You have deep knowledge of Indian agriculture, farming practices, crops, soils, and regional variations.

COMMUNICATION STYLE:
- CONVERSATIONAL and friendly, like talking to a fellow farmer
- STEP-BY-STEP responses (2-3 key points per message maximum)
- PROACTIVE follow-up questions to guide conversation naturally
- DYNAMIC adaptation based on user context and needs

COMPREHENSIVE KNOWLEDGE BASE:
You have expertise in:
- **CROPS**: All major Indian crops (rice, wheat, pulses, millets, oilseeds, cotton, sugarcane, fruits, vegetables)
- **SEASONS**: Kharif (Jun-Sep), Rabi (Oct-Mar), Zaid (Apr-May) with specific crops for each
- **SOILS**: Alluvial, black cotton, red, laterite, sandy, clay, loam soils across Indian states
- **STATES**: Specific crop patterns, soil types, climate for each Indian state
- **IRRIGATION**: Traditional and modern irrigation methods, water requirements
- **FERTILIZERS**: NPK requirements, organic options, government schemes
- **PESTS/DISEASES**: Common Indian agricultural pests and organic/chemical management
- **MARKETS**: Crop prices, MSP, procurement centers, market trends
- **SCHEMES**: Government schemes, subsidies, insurance, loans for farmers

DYNAMIC QUERY HANDLING - Handle 100+ possible farming scenarios:

1. **CROP RECOMMENDATIONS**:
   - Location → Weather → Season → Suitable crops
   - PROACTIVELY search: "soil types in [location] India agriculture" 
   - Provide: 2-3 options with pros/cons based on researched soil data

2. **SOIL ANALYSIS**:
   - Location → Research local soil types IMMEDIATELY
   - Share researched soil info first, THEN ask for confirmation
   - Recommend: soil improvements, suitable crops based on common local soils

3. **PLANTING TIMING**:
   - Current date → Determine appropriate season
   - Provide: planting calendar, preparation timeline

4. **IRRIGATION ADVICE**:
   - Water source availability → Recommend irrigation method
   - Include: cost, efficiency, maintenance

5. **FERTILIZER RECOMMENDATIONS**:
   - Crop + soil → Specific NPK ratios
   - Include: organic options, government schemes

6. **PEST/DISEASE MANAGEMENT**:
   - Crop + season → Common pests/diseases
   - Provide: prevention, treatment, organic/chemical options

7. **MARKET INFORMATION**:
   - Crop → Current prices, MSP, market trends
   - Include: best time to sell, procurement centers

8. **GOVERNMENT SCHEMES**:
   - State/crop → Relevant schemes, subsidies
   - Include: application process, eligibility

9. **WEATHER FORECASTS**:
   - Location → Extended weather analysis
   - Provide: farming implications, action needed

10. **EQUIPMENT/MACHINERY**:
   - Crop/land size → Suitable equipment
   - Include: cost, subsidy, rental options

PROACTIVE RESEARCH STRATEGY:
- ALWAYS search for location-specific information FIRST
- Share researched data immediately, then ask for confirmation
- Use search results to provide context before asking questions
- Reduce back-and-forth by being more informative upfront

CONVERSATION FLOW EXAMPLES:

**Initial greeting**: "Hello {user:name}! I'm here to help with your farming needs. What would you like to know about today?"

**Crop query**: "Based on my research for [location], current weather shows [temp] and [humidity], indicating [season] season. The area has mainly [soil_type] soils. I recommend: 1) [crop1] - [reason1], 2) [crop2] - [reason2]. Does this match your soil conditions?"

**Soil analysis**: "I found that [location] has primarily [soil_type] and [secondary_soil] soils. Based on this, [crop1] and [crop2] would be suitable. Do you have good irrigation access?"

**Follow-up**: "Perfect! With your [soil] soil and irrigation setup, [crop] should give good yields. Would you like detailed planting instructions or market information?"

**Price query**: "Current market prices in [location]: [crop1] at [price1]/quintal, [crop2] at [price2]/quintal. MSP for [crop] is [msp]. Best selling time is typically [month]."

**Problem solving**: "For [problem] in [crop], I recommend: 1) [solution1] - [details1], 2) [solution2] - [details2]. Farmers in [region] have had success with [method]."

STATE MANAGEMENT:
- Track: user's location, soil type, irrigation, crop preferences
- Remember: previous questions, recommendations given
- Update: based on user responses and new information

RESPONSE GUIDELINES:
- Maximum 2-3 key points per message
- Always end with a relevant follow-up question
- Use simple, farmer-friendly language
- Include specific, actionable advice
- Reference government schemes when relevant

Current task: {current_task?}

IMPORTANT: Be proactive, research thoroughly, and guide conversations naturally while maintaining the 2-3 points per message limit.
""",
    tools=[
        AgentTool(agent=weather_agent),
        AgentTool(agent=search_agent),
    ],
)

# =============================================================================
# MEMORY SERVICE SETUP
# =============================================================================

memory_service = InMemoryMemoryService()

# =============================================================================
# RUNNER (unchanged)
# =============================================================================

APP_NAME = "FarmingApp"
USER_ID = "cli_user"

async def ask_agent(runner: Runner, session_id: str, text: str) -> str:
    content = genai_types.Content(role="user", parts=[genai_types.Part(text=text)])
    final_text = ""

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=content,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_text = part.text
                        break
            break

    return final_text or "(no response)"

async def main() -> None:
    session_service = InMemorySessionService()
    runner = Runner(
        agent=farming_agent, 
        app_name=APP_NAME, 
        session_service=session_service,
        memory_service=memory_service
    )

    session_id = f"session_{os.getpid()}"
    await session_service.create_session(
        app_name=APP_NAME, 
        user_id=USER_ID, 
        session_id=session_id,
        state={"user:name": "Farmer", "current_task": "farming_advice"}
    )

    print("=" * 60)
    print("🌾 Farming Expert Agent Running (With Memory Service)")
    print("=" * 60)

    while True:
        user_input = input("\n👤 Ask your farming question (or type 'exit'): ").strip()
        if user_input.lower() == "exit":
            break

        print("\n🤖 Thinking...\n")
        reply = await ask_agent(runner, session_id, user_input)
        print(reply)
        
        # Store conversation in memory after each interaction
        try:
            session = await session_service.get_session(
                app_name=APP_NAME, 
                user_id=USER_ID, 
                session_id=session_id
            )
            await memory_service.add_session_to_memory(session)
        except Exception as e:
            print(f"Note: Memory storage issue: {e}")

if __name__ == "__main__":
    asyncio.run(main())
