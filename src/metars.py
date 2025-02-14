import json
import urllib.parse
import openai
import requests


STATION_IDS = ["CYYZ", "OMDB", "LTFM", "KLAX", "WIII"]
WEATHER_PARAMS = {
    "site": "station_name",
    "obsTime": "time_utc",
    "temp": "temperature_c",
    "dewp": "dew_point_c",
    "wspd": "wind_speed_kt",
    "wdir": "wind_direction",
    "wgst": "wind_gust_kt",
    "cover": "cloud_cover",
    "wx": "wx_code",
}
INSTRUCTIONS = (
    "You are an AI assistant specialized in interpreting and describing weather data stored in JSON format. "
    "You are expert at reading weather data for a given location and providing an English description of the weather at that location. "
    "The English weather description should be in the style of TV weatherman."
)
PROMPT = (
    "Briefly describe the weather for the location identified in the following JSON data. "
    "Format your response as a JSON object with the following key: 'weather_description'. "
)


def process_metars(raw_metars, properties):
    stations = {}
    for weather_report in raw_metars:
        station = {}

        station_id = weather_report["properties"].get("id")
        if station_id not in stations:
            stations[station_id] = station

        for property, feat_name in properties.items():
            station[feat_name] = weather_report["properties"].get(property, None)

        station["geometry"] = weather_report.get("geometry", None)

        stations[station_id].update(station)
    return stations


def download_metars(args, properties, base_url="https://aviationweather.gov/api/data/metar"):
    params = urllib.parse.urlencode(args)
    url = f"{base_url}?{params}"
    print("Downloading new METARS data from", url)

    resp = requests.get(url)
    if resp.status_code != 200:
        print("Error downloading METARS", resp.status_code)
        return None
    metars_json = json.loads(resp.text)
    metars = process_metars(metars_json["features"], properties)
    return metars


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


def gpt_weather_report(metars: dict, client: openai.OpenAI, model: str, max_tokens: int):
    for station_id, weather in metars.items():
        print(f"Generating weather report for {station_id}")
        msgs = [{"role": "system", "content": INSTRUCTIONS}]
        content = [
            {
                "type": "text",
                "text": f"{PROMPT} \n\nWEATHER DATA: {json.dumps(weather)}",
            }
        ]
        msgs.append({"role": "user", "content": content})
        response = gpt_chat(
            client=client, model=model, messages=msgs, max_tokens=max_tokens
        )
        weather.update(json.loads(response))


def main():
    args = {"ids": ",".join(STATION_IDS), "format": "geojson", "taf": False, "hours": 1}
    metars = download_metars(args, WEATHER_PARAMS)
    openai_client = openai.OpenAI()
    gpt_weather_report(
        metars=metars, client=openai_client, model="gpt-4o-mini", max_tokens=1000
    )
    with open("data/metars/current-weather.json", "w") as f:
        json.dump(metars, f, indent=4)


if __name__ == "__main__":
    main()
