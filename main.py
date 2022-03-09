import datetime
import gzip
import logging
import os
import pathlib
from typing import Any, cast

import fastapi
import maxminddb
import pydantic
import requests

app = fastapi.FastAPI()

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError("Error! API_KEY env variable is not set.")

LOGLEVEL = os.getenv("LOGLEVEL", "INFO").upper()

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)

month = datetime.date.today().strftime("%Y-%m")
filepath = (
    pathlib.Path(__file__).resolve(strict=True).parent / f"dbip-city-lite-{month}.mmdb"
)
reader: maxminddb.Reader | None = None

JsonDict = dict[str, Any]


class Country(pydantic.BaseModel):
    name: str
    code: str


class GeoLocation(pydantic.BaseModel):
    country: Country
    region: str
    city: str


@app.on_event("startup")
def startup_event() -> None:
    global reader

    try:
        reader = maxminddb.open_database(filepath)
    except OSError:
        logger.debug(f"Downloading GeoIP database for {month}...")
        content = requests.get(
            f"https://download.db-ip.com/free/dbip-city-lite-{month}.mmdb.gz"
        ).content
        logger.debug("Downloaded GeoIP database.")
        decompressed_content = gzip.decompress(content)

        with open(filepath, "wb") as f:
            f.write(decompressed_content)

        reader = maxminddb.open_database(f.name)
    else:
        logger.debug(f"GeoIP database for {month} already exists - using it.")


@app.get("/geoip")
async def get_geoip(
    ip: str,
    x_api_key: str = fastapi.Header(pydantic.Required),
    response_model: type[GeoLocation] = GeoLocation,
) -> JsonDict:
    if x_api_key != API_KEY:
        raise fastapi.HTTPException(status_code=401, detail="Invalid API key.")

    assert reader
    try:
        data = cast(JsonDict, reader.get(ip))  # maxminddb's typings are bad.
    except ValueError:
        raise fastapi.HTTPException(
            status_code=400, detail="Invalid IP address."
        ) from None

    return {
        "country": {
            "name": data["country"]["names"]["en"],
            "code": data["country"]["iso_code"],
        },
        "region": ", ".join(region["names"]["en"] for region in data["subdivisions"]),
        "city": data["city"]["names"]["en"],
    }
