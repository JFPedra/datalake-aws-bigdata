import io, os, re, unicodedata
import boto3, pandas as pd, requests
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()
BUCKET = os.environ["S3_BUCKET"]
s3 = boto3.client("s3")


def normalizar(nombre: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", sin_tildes.lower()).strip("_")


def limpiar(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [normalizar(c) for c in df.columns]
    df = df.convert_dtypes()
    for c in df.select_dtypes(include=["object", "string"]).columns:
        df[c] = (df[c].astype("string")
                 .str.replace(";", ",", regex=False)
                 .str.replace(r"[\r\n]+", " ", regex=True)
                 .str.strip())
    return df


def subir(df: pd.DataFrame, carpeta: str) -> None:
    key = f"raw/{carpeta}/{carpeta}.csv"
    s3.put_object(Bucket=BUCKET, Key=key, Body=df.to_csv(sep=";", index=False).encode("utf-8"))
    print(f"OK {len(df)} filas -> s3://{BUCKET}/{key}")


def origen_mysql() -> None:
    url = (f"mysql+pymysql://{os.environ['MYSQL_USER']}:{os.environ['MYSQL_PASSWORD']}"
           f"@{os.environ['MYSQL_HOST']}:{os.environ['MYSQL_PORT']}/{os.environ['MYSQL_DB']}"
           "?charset=utf8mb4")
    engine = create_engine(url)
    for tabla in os.environ["MYSQL_TABLES"].split(","):
        df = pd.read_sql(f"SELECT * FROM {tabla.strip()}", engine)
        subir(limpiar(df), f"mysql_{normalizar(tabla)}")


def origen_csv() -> None:
    # AJUSTAR sep y encoding según el archivo ("," o ";", "utf-8" o "latin-1")
    opciones = dict(sep=";", encoding="utf-8")
    if os.environ.get("CSV_URL"):
        r = requests.get(os.environ["CSV_URL"], timeout=120)
        r.raise_for_status()
        df = pd.read_csv(io.BytesIO(r.content), **opciones)
    else:
        df = pd.read_csv(os.environ["CSV_PATH"], **opciones)
    subir(limpiar(df), f"csv_{normalizar(os.environ['CSV_NAME'])}")


if __name__ == "__main__":
    origen_mysql()
    origen_csv()