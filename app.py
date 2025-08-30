import geopandas as gpd
from shapely.geometry import Point
from shapely.validation import make_valid
from fastapi import FastAPI
import uvicorn

app = FastAPI()

# Load dataset once (on startup)
try:
    mangrove = gpd.read_file("clipped_gmw.json")
    mangrove["geometry"] = mangrove.geometry.apply(
        lambda g: make_valid(g) if g is not None and not g.is_valid else g
    )
    mangrove = mangrove[mangrove.geometry.notnull()]
    mangrove_m = mangrove.to_crs(epsg=3857)  # keep cached in meters
except Exception as e:
    print("Error loading mangrove dataset:", e)
    mangrove_m = None


def is_in_mangrove(lat: float, lon: float, buffer_km: int = 0) -> int:
    """Return 1 if point is inside/near mangrove, else 0."""
    if mangrove_m is None or mangrove_m.empty:
        return 0
    try:
        # Create point
        point = gpd.GeoDataFrame(geometry=[Point(lon, lat)], crs="EPSG:4326").to_crs(epsg=3857)

        # Buffer if needed
        if buffer_km > 0:
            buffer_geom = point.buffer(buffer_km * 1000)
            intersects = mangrove_m.intersects(buffer_geom.iloc[0])
        else:
            intersects = mangrove_m.contains(point.iloc[0].geometry)

        return int(intersects.any())
    except Exception:
        return 0


@app.get("/check")
def check(lat: float, lon: float, buffer_km: int = 0):
    """
    API endpoint:
    Example: /check?lat=21.95&lon=88.75&buffer_km=5
    Returns: 0 or 1
    """
    return is_in_mangrove(lat, lon, buffer_km)


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
