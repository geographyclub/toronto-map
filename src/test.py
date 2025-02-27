import json
import numpy as np
from random import randint


def random_offset(centre, std_dev, num_points):
    x_center, y_center = centre
    x_points = np.random.normal(x_center, std_dev, num_points).tolist()
    y_points = np.random.normal(y_center, std_dev, num_points).tolist()
    return list(zip(x_points, y_points))


def main():
    input_filepath = "data/test.geojson"
    output_filepath = "data/test-random-points.geojson"
    num_points = 10
    icon_numbers = [1, 301]
    std_dev = 0.001

    with open(input_filepath, "r") as input_file:
        centre_pts = json.load(input_file)

    random_points = {
        "type": "FeatureCollection",
        "name": "test",
        "crs": centre_pts["crs"],
        "features": [],
    }

    for cp in centre_pts["features"]:
        centre = cp["geometry"]["coordinates"]
        feat = {
            "type": "Feature",
            "properties": {
                "name": cp["properties"]["name"],
                "icon_number": [randint(*icon_numbers) for _ in range(num_points)],
            },
            "geometry": {
                "type": "MultiPoint",
                "coordinates": random_offset(centre, std_dev, num_points),
            },
        }
        random_points["features"].append(feat)

    with open(output_filepath, "w") as output_file:
        json.dump(random_points, output_file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
