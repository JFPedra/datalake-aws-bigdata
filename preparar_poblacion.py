import sys
import pandas as pd

PROVINCIAS = {"Andalucía", "Almería", "Cádiz", "Córdoba", "Granada", "Huelva", "Jaén", "Málaga", "Sevilla"}

partes = []
for arg in sys.argv[1:]:
    anio, ruta = arg.split("=")
    df = pd.read_csv(ruta, sep=";", encoding="utf-8", usecols=[0, 1, 3], dtype={"Valor": "string"})
    df.columns = ["municipio", "sexo", "valor"]
    df["anio"] = int(anio)
    partes.append(df)

df = pd.concat(partes, ignore_index=True)
df = df[~df["municipio"].isin(PROVINCIAS)].copy()
df["municipio"] = df["municipio"].str.replace(r"\s*\(capital\)$", "", regex=True).str.strip()
df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
df["sexo"] = df["sexo"].map({"Hombres": "hombres", "Mujeres": "mujeres", "Ambos sexos": "ambos_sexos"})

p = df.pivot_table(index=["municipio", "anio"], columns="sexo", values="valor", aggfunc="first").reset_index()
p.columns.name = None
p = p[["municipio", "anio", "mujeres", "hombres", "ambos_sexos"]].convert_dtypes()
p.to_csv("poblacion.csv", sep=";", index=False, encoding="utf-8")

print(p.shape); print(p.groupby("anio").size()); print(p.isna().sum().to_string())
print(p[p["municipio"].isin(["Almería","Granada","Sevilla","Jaén","Cádiz","Huelva"])].sort_values(["municipio","anio"]).to_string(index=False))