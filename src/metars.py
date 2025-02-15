import json
import urllib.parse
import openai
import requests
from dotenv import load_dotenv

INSTRUCTIONS = (
    "You are a Toronto historian/walking tour guide knowledgable in Toronto architecture, urban history, city planning data stored in JSON format. "
    "You are expert at reading street and building data for a given location and providing an English description of the urban geography at that location. "
    "The English description should be in the style of a walking tour and no more than 280 characters."
)
PROMPT = (
    "Briefly describe the history, culture and architecture for the location identified in the following JSON data. "
    "Format your response as a JSON object with the following key: 'street_description'. "
    # "{ 'type': 'Feature', 'properties': { 'name': 'Old City Hall' }, 'geometry': { 'type': 'Point', 'coordinates': [ -79.381759498506327, 43.652636575812757 ] } }"
)

def gpt_list_models(client):
    for m in client.models.list():
        print(m.id)


def gpt_chat(client: openai.OpenAI, model: str, messages: list, max_tokens: int):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        max_tokens=max_tokens,
    )
    weather_report = ""
    if response.choices[0].finish_reason == "stop":
        weather_report = response.choices[0].message.content
    return weather_report


def gpt_osm_description(place: dict, client: openai.OpenAI, model: str, max_tokens: int):
    msgs = [{"role": "system", "content": INSTRUCTIONS}]
    content = [
        {
            "type": "text",
            "text": f"{PROMPT} \n\nOPENSTREETMAP DATA: {json.dumps(place)}",
        }
    ]
    msgs.append({"role": "user", "content": content})
    response = gpt_chat(
        client=client, model=model, messages=msgs, max_tokens=max_tokens
    )
    return response

def main():

    with open("data/osm.geojson", "r") as places_file:
        places = json.load(places_file)
        # print(places)
    
    load_dotenv() # OpenAI API Key is stored in an environment variable
    openai_client = openai.OpenAI()
    for feat in places["features"]:
        place = feat["properties"]
        description = gpt_osm_description(
            client=openai_client, model="gpt-4o-mini", max_tokens=1000, place=place
        )
        feat["properties"]["description"] = description
        # print(place, description)
    
    with open("data/osm-descriptions.json", "w") as f:
        json.dump(places, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
