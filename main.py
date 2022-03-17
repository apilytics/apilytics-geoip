import datetime
import gzip
import logging
import os
import pathlib
from typing import Any, TypeVar, cast

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


class Body(pydantic.BaseModel):
    ip: str


class Country(pydantic.BaseModel):
    name: str | None
    code: str | None


class GeoLocation(pydantic.BaseModel):
    country: Country
    region: str | None
    city: str | None


T = TypeVar("T")


def safe_get(dict_: JsonDict | None, *keys: str, default: T | None = None) -> Any | T:
    for key in keys:
        try:
            dict_ = dict_[key]  # type: ignore[index]
        except (KeyError, TypeError):
            return default
    return dict_


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


@app.post("/geoip")
async def get_geoip(
    body: Body,
    x_api_key: str = fastapi.Header(pydantic.Required),
    response_model: type[GeoLocation] = GeoLocation,
) -> JsonDict:
    if x_api_key != API_KEY:
        raise fastapi.HTTPException(status_code=401, detail="Invalid API key.")

    assert reader  # Initialized in `startup_event`.

    try:
        data = cast(JsonDict, reader.get(body.ip))  # maxminddb's typings are bad.
    except ValueError:
        raise fastapi.HTTPException(
            status_code=400, detail="Invalid IP address."
        ) from None

    return {
        "country": {
            "name": safe_get(data, "country", "names", "en"),
            "code": safe_get(data, "country", "iso_code"),
        },
        "region": ", ".join(
            safe_get(region, "names", "en")
            for region in safe_get(data, "subdivisions", default=[])
        )
        or None,
        "city": safe_get(data, "city", "names", "en"),
    }


@app.get("/healthz")
async def health_check() -> fastapi.Response:
    return fastapi.Response(status_code=fastapi.status.HTTP_200_OK)
