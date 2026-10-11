
import io
import re
import html
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Transporte de carga | Análisis científico", page_icon="📊",
                   layout="wide", initial_sidebar_state="expanded")

NAVY="#153D58"; TEAL="#087F8C"; BLUE="#3979A8"; CORAL="#DF7965"
GOLD="#D6A247"; SAGE="#75A995"; LAVENDER="#8C84B4"; GRAY="#8295A3"
PALETTE=[NAVY,TEAL,BLUE,CORAL,GOLD,SAGE,LAVENDER,GRAY]
TECH={
"T1_GPS":"GPS y rastreo",
"T2_Rutas":"Software de rutas",
"T3_IoT":"Sensores IoT",
"T4_TMS_WMS":"Plataformas TMS/WMS",
"T5_Apps":"Aplicaciones móviles",
"T6_Mantenimiento":"Mantenimiento predictivo",
"T7_Telemetria":"Telemetría",
"T8_Emisiones":"Monitoreo de emisiones"
}
NUMERIC={
"Numero_tecnologias_8":"Tecnologías adoptadas",
"Flota_ord":"Tamaño de flota (ordinal)",
"Antiguedad_ord":"Antigüedad (ordinal)",
"Educacion_ord":"Educación (ordinal)",
"Capacitacion_01":"Capacitación (0/1)",
"Conocimiento_1a5":"Conocimiento (1–5)",
"Costo_1a5":"Costo percibido (1–5)",
"Incentivos_01":"Apoyos (0/1)",
"Eficiencia_1a5":"Eficiencia percibida (1–5)"
}
st.markdown("""
<style>
.stApp{background:#F6F8FB;color:#1B3448}
.block-container{max-width:1480px;padding-top:1.3rem}
h1,h2,h3{color:#153D58!important;letter-spacing:-.025em}
h1{font-size:1.9rem!important}
section[data-testid="stSidebar"]{background:#153D58}
section[data-testid="stSidebar"] *{color:#F2F7FA!important}
section[data-testid="stSidebar"] [data-baseweb="select"] *{color:#17384D!important}
div[data-testid="stTabs"] button{font-weight:650;font-size:.88rem}
div[data-testid="stTabs"] button[aria-selected="true"]{color:#087F8C!important}
.metric{background:white;border:1px solid #E0E8EE;border-top:4px solid #087F8C;border-radius:10px;
padding:15px 17px;min-height:110px}
.metric .label{font-size:.82rem;color:#5C6F7D;font-weight:600}
.metric .value{font-size:1.9rem;color:#153D58;font-weight:750;margin:6px 0 0}
.metric .foot{font-size:.75rem;color:#758695}
div[data-testid="stVerticalBlockBorderWrapper"]>div{border-radius:11px!important}
</style>
""",unsafe_allow_html=True)

def normalize(v):
    if pd.isna(v):return "Sin respuesta"
    s=re.sub(r"\s+"," ",str(v)).strip()
    return s if s else "Sin respuesta"

@st.cache_data
def parse_excel(raw):
    return pd.read_excel(io.BytesIO(raw),sheet_name=None)

def derive_from_original(book):
    for name,frame in book.items():
        q={}
        for c in frame.columns:
            m=re.search(r"Pregunta\s*(\d+)\s*:",str(c),re.I)
            if m:q[int(m.group(1))]=c
        if len(q)<10:continue
        d=pd.DataFrame(index=frame.index)
        d["ID"]=np.arange(1,len(frame)+1)
        for i in range(1,12):
            d[f"P{i}"]=frame[q[i]] if i in q else np.nan
        d["Flota_cat"]=d["P1"].map(normalize)
        d["Antiguedad_cat"]=d["P2"].map(normalize)
        d["Tipo_carga"]=d["P3"].map(normalize)
        d["Educacion_cat"]=d["P6"].map(normalize)
        d["Conocimiento_cat"]=d["P8"].map(normalize)
        d["Flota_ord"]=d["Flota_cat"].map({"1-5":1,"6-15":2,"16-30":3,"Más de 30":4})
        d["Antiguedad_ord"]=d["Antiguedad_cat"].map({"Menos de 1 año":1,"1-5 años":2,"De 6 a 10 años":3,"6-10 años":3,"Más de 10 años":4})
        d["Educacion_ord"]=d["Educacion_cat"].map({"Primaria":1,"Secundaria":2,"Técnico o tecnólogo":3,"Técnico/Tecnólogo":3,"Profesional":4,"Posgrado":5})
        d["Capacitacion_01"]=d["P7"].map(lambda x: 1 if normalize(x).casefold() in ("sí","si") else (0 if normalize(x).casefold()=="no" else np.nan))
        d["Incentivos_01"]=d["P10"].map(lambda x: 1 if normalize(x).casefold() in ("sí","si") else (0 if normalize(x).casefold()=="no" else np.nan))
        d["Conocimiento_1a5"]=d["Conocimiento_cat"].map({"Muy bajo":1,"Bajo":2,"Medio":3,"Alto":4,"Muy alto":5})
        d["Costo_1a5"]=pd.to_numeric(d["P9"],errors="coerce")
        d["Eficiencia_1a5"]=pd.to_numeric(d["P11"],errors="coerce")
        s=d["P4"].fillna("").astype(str)
        phrases=["GPS y rastreo en tiempo real","Software de gestión de rutas",
                 "Sensores IoT en vehículos","Plataformas de gestión logística (TMS, WMS)",
                 "Aplicaciones móviles para conductores","Sistemas de mantenimiento predictivo",
                 "Telemetría avanzada","Tecnología de monitoreo de emisiones"]
        for col,phrase in zip(TECH,phrases):
            d[col]=s.str.contains(re.escape(phrase),case=False,regex=True).astype(int)
        d["Numero_tecnologias_8"]=d[list(TECH)].sum(axis=1)
        d["Otras_texto"]=d["P5"]
        d["Tecnologias_originales"]=d["P4"]
        return d,name
    return None,None

def get_data(book):
    if "Base_modelo" in book and set(TECH).issubset(book["Base_modelo"].columns):
        d=book["Base_modelo"].copy()
        if "Respuestas_originales" in book:
            r=book["Respuestas_originales"]
            q={}
            for c in r.columns:
                m=re.search(r"Pregunta\s*(\d+)\s*:",str(c),re.I)
                if m:q[int(m.group(1))]=c
            if len(r)==len(d):
                for i,c in q.items():d[f"P{i}"]=r[c].to_numpy()
        for i in range(1,12):
            if f"P{i}" not in d:d[f"P{i}"]=np.nan
        return d,"Base_modelo + Respuestas_originales"
    return derive_from_original(book)

def base_plot(fig,height=315):
    fig.update_layout(height=height,margin=dict(l=12,r=22,t=22,b=32),font=dict(family="Arial",size=12,color="#28445A"),
                      paper_bgcolor="white",plot_bgcolor="white",legend=dict(orientation="h",y=-.22))
    fig.update_xaxes(showgrid=False,linecolor="#DDE5EA")
    fig.update_yaxes(gridcolor="#EDF1F5",zeroline=False)
    return fig

def panel(title,fig,key,caption=None,height=315):
    with st.container(border=True):
        st.markdown(f"**{title}**")
        if caption:st.caption(caption)
        st.plotly_chart(base_plot(fig,height),use_container_width=True,key=key,
                        config={"displaylogo":False,"toImageButtonOptions":{"format":"png","scale":3}})

def cat_counts(s):
    x=s.map(normalize)
    x=x[x!="Sin respuesta"]
    z=x.value_counts().rename_axis("Categoría").reset_index(name="n")
    z["%"]=100*z["n"]/max(len(x),1)
    return z

def categorical(df,col,title,key,horizontal=False):
    z=cat_counts(df[col])
    if z.empty:st.info(f"Sin datos: {title}");return
    colors=[PALETTE[i%len(PALETTE)] for i in range(len(z))]
    if horizontal:
        z=z.iloc[::-1]
        colors=colors[::-1]
        fig=go.Figure(go.Bar(x=z["%"],y=z["Categoría"],orientation="h",marker_color=colors,
                             text=z["%"].map(lambda x:f"{x:.1f}%"),textposition="outside"))
        fig.update_xaxes(title="% de respuestas",range=[0,max(105,z["%"].max()*1.16)])
        fig.update_yaxes(automargin=True)
    else:
        fig=go.Figure(go.Bar(x=z["Categoría"],y=z["%"],marker_color=colors,
                             text=z["%"].map(lambda x:f"{x:.1f}%"),textposition="outside"))
        fig.update_yaxes(title="% de respuestas",range=[0,max(105,z["%"].max()*1.16)])
        fig.update_xaxes(tickangle=-15,automargin=True)
    panel(title,fig,key,height=max(300,48*len(z)) if horizontal else 315)

def donut(df,col,title,key):
    z=cat_counts(df[col])
    if z.empty:st.info(f"Sin datos: {title}");return
    fig=go.Figure(go.Pie(labels=z["Categoría"],values=z["n"],hole=.63,
                         marker_colors=PALETTE[:len(z)],textinfo="percent",sort=False))
    fig.update_layout(showlegend=True,annotations=[dict(text=f"<b>{int(z['n'].sum())}</b><br>respuestas",
                                                         showarrow=False,font=dict(size=13,color=NAVY))])
    panel(title,fig,key,height=325)

def tech_chart(df,key):
    n=len(df)
    z=pd.DataFrame({"Tecnología":list(TECH.values()),"n":[int(df[c].sum()) for c in TECH]})
    z["%"]=100*z["n"]/max(1,n)
    z=z.sort_values("%",ascending=True)
    fig=go.Figure(go.Bar(x=z["%"],y=z["Tecnología"],orientation="h",marker_color=TEAL,
                         text=z["%"].map(lambda x:f"{x:.1f}%"),textposition="outside",
                         customdata=z["n"],hovertemplate="%{y}<br>%{x:.1f}% · %{customdata} empresas<extra></extra>"))
    fig.update_xaxes(title="% de empresas",range=[0,max(105,z["%"].max()*1.15)])
    fig.update_yaxes(automargin=True)
    panel("P4 · Tecnologías implementadas",fig,key,
          "Respuesta múltiple. El denominador es el total de empresas filtradas.",height=410)

def likert(df,key):
    a=pd.to_numeric(df["Costo_1a5"],errors="coerce").dropna()
    b=pd.to_numeric(df["Eficiencia_1a5"],errors="coerce").dropna()
    fig=go.Figure()
    palette=["#BD6372","#E9A18D","#D6DDE3","#8FC2B4","#087F8C"]
    for score in range(1,6):
        fig.add_trace(go.Bar(y=["Costos percibidos","Eficiencia percibida"],
                             x=[100*(a==score).mean() if len(a) else 0,
                                100*(b==score).mean() if len(b) else 0],
                             name=str(score),orientation="h",marker_color=palette[score-1],
                             text=[f"{100*(a==score).mean():.0f}%" if len(a) and (a==score).mean()>.06 else "",
                                   f"{100*(b==score).mean():.0f}%" if len(b) and (b==score).mean()>.06 else ""],
                             textposition="inside"))
    fig.update_layout(barmode="stack",legend_title_text="Escala",xaxis_title="% de respuestas")
    panel("Distribución de respuestas en escalas 1–5",fig,key,
          "Barras apiladas: 1 representa el extremo inferior y 5 el superior en cada pregunta.",height=300)

def metric(label,value,foot):
    st.markdown(f'<div class="metric"><div class="label">{html.escape(str(label))}</div>'
                f'<div class="value">{html.escape(str(value))}</div>'
                f'<div class="foot">{html.escape(str(foot))}</div></div>',unsafe_allow_html=True)

def spearman_table(df,cols):
    records=[]
    for i,a in enumerate(cols):
        for b in cols[i+1:]:
            sub=df[[a,b]].apply(pd.to_numeric,errors="coerce").dropna()
            if len(sub)<5 or sub[a].nunique()<2 or sub[b].nunique()<2:continue
            rho=sub[a].corr(sub[b],method="spearman")
            if np.isfinite(rho):
                records.append({"Variable A":NUMERIC[a],"Variable B":NUMERIC[b],
                                "rho":float(rho),"n":len(sub)})
    return pd.DataFrame(records)


def corr_heatmap(df,cols,key):
    pairs=spearman_table(df,cols)
    if pairs.empty:st.info("No hay variación suficiente para calcular correlaciones.");return
    names=[NUMERIC[c] for c in cols]
    matrix=pd.DataFrame(np.nan,index=names,columns=names)
    for n in names:matrix.loc[n,n]=1.
    for _,r in pairs.iterrows():
        matrix.loc[r["Variable A"],r["Variable B"]]=r["rho"]
        matrix.loc[r["Variable B"],r["Variable A"]]=r["rho"]
    fig=go.Figure(go.Heatmap(z=matrix.to_numpy(dtype=float),x=names,y=names,zmin=-1,zmax=1,zmid=0,
                             colorscale=[[0,"#C36C70"],[.5,"#F6F8FA"],[1,"#087F8C"]],
                             text=[[f"{v:.2f}" if np.isfinite(v) else "" for v in row]
                                   for row in matrix.to_numpy(dtype=float)],
                             texttemplate="%{text}",textfont=dict(size=11),colorbar=dict(title="ρ")))
    fig.update_xaxes(tickangle=-35,automargin=True)
    fig.update_yaxes(autorange="reversed",automargin=True)
    panel("Matriz de correlación de Spearman",fig,key,
          "Coeficientes descriptivos. Las variables binarias u ordinales requieren interpretación contextual.",height=530)
    st.dataframe(pairs.assign(rho=pairs.rho.round(3)),hide_index=True,use_container_width=True)

def box_compare(df,group,key):
    sub=df[[group,"Numero_tecnologias_8"]].dropna().copy()
    if group in ["Capacitacion_01","Incentivos_01"]:
        sub[group]=sub[group].map({0:"No",1:"Sí"})
    if sub[group].nunique()<2:st.info("No hay dos grupos para comparar.");return
    fig=px.box(sub,x=group,y="Numero_tecnologias_8",points="all",color=group,
               color_discrete_sequence=[TEAL,BLUE,CORAL,GOLD,SAGE])
    fig.update_layout(showlegend=False)
    fig.update_xaxes(title=NUMERIC.get(group,group))
    fig.update_yaxes(title="Número de tecnologías (0–8)")
    panel("Tecnologías adoptadas según "+NUMERIC.get(group,group).lower(),fig,key,
          "Cada punto representa una empresa.",height=355)

def group_test(df,group):
    sub=df[[group,"Numero_tecnologias_8"]].dropna()
    groups=[x["Numero_tecnologias_8"].to_numpy(dtype=float) for _,x in sub.groupby(group)]
    if len(groups)<2 or any(len(x)==0 for x in groups):return None
    # Prueba exploratoria de permutación sin dependencias adicionales.
    values=np.concatenate(groups)
    sizes=[len(x) for x in groups]
    if len(groups)==2:
        statistic=float(abs(np.mean(groups[0])-np.mean(groups[1])))
        label="Permutación: diferencia absoluta de medias"
        def calc(arr):
            return abs(float(arr[:sizes[0]].mean()-arr[sizes[0]:].mean()))
    else:
        statistic=float(np.var([np.mean(x) for x in groups]))
        label="Permutación: variación entre medias"
        def calc(arr):
            ix=np.cumsum(sizes)[:-1]
            return float(np.var([np.mean(x) for x in np.split(arr,ix)]))
    rng=np.random.default_rng(2026)
    reps=4999
    extreme=sum(calc(rng.permutation(values))>=statistic-1e-12 for _ in range(reps))
    p=(extreme+1)/(reps+1)
    return label,statistic,float(p),sizes


def regression(df,xcol,ycol,key):
    sub=df[[xcol,ycol]].apply(pd.to_numeric,errors="coerce").dropna()
    if len(sub)<12 or sub[xcol].nunique()<2 or sub[ycol].nunique()<2:
        st.info("No hay observaciones o variación suficientes para estimar esta regresión.");return
    x=sub[xcol].to_numpy(dtype=float); y=sub[ycol].to_numpy(dtype=float)
    def slope(xx,yy):
        if np.var(xx)<1e-12:return np.nan
        return float(np.cov(xx,yy,ddof=0)[0,1]/np.var(xx))
    beta=slope(x,y)
    if not np.isfinite(beta):
        st.info("La variable explicativa no tiene variación suficiente.");return
    rng=np.random.default_rng(2026)
    bs=[]
    for _ in range(1999):
        ix=rng.integers(0,len(x),len(x))
        b=slope(x[ix],y[ix])
        if np.isfinite(b):bs.append(b)
    if len(bs)<100:
        st.info("No fue posible calcular intervalos estables con remuestreo.");return
    lo,hi=np.percentile(bs,[2.5,97.5])
    r=np.corrcoef(x,y)[0,1]
    fig=go.Figure(go.Scatter(x=[beta],y=[NUMERIC[xcol]],mode="markers",
                             marker=dict(size=12,color=TEAL),
                             error_x=dict(type="data",symmetric=False,
                                          array=[max(0,float(hi-beta))],
                                          arrayminus=[max(0,float(beta-lo))])))
    fig.add_vline(x=0,line_dash="dash",line_color=GRAY)
    fig.update_xaxes(title="Pendiente e intervalo bootstrap 95 %")
    panel("Regresión lineal exploratoria",fig,key,
          f"Dependiente: {NUMERIC[ycol]}; n={len(sub)}; pendiente={beta:.3f}; R²={r*r:.3f}.",height=250)
    st.caption("Intervalo bootstrap percentil (1.999 remuestreos). Análisis exploratorio, "
               "sin inferencia causal; la escala ordinal o de conteo limita la interpretación.")


with st.sidebar:
    st.markdown("## Transporte de carga")
    st.caption("Análisis estadístico de adopción tecnológica")
    upload=st.file_uploader("Cargar base Excel",type=["xlsx"])
    st.caption("Recomendado: Base_limpia_regresion_transporte_carga.xlsx, que incluye las respuestas originales.")
st.title("Adopción tecnológica en empresas de transporte de carga")
st.caption("Dashboard académico · Estadística descriptiva, asociaciones y análisis exploratorio")

if upload is None:
    st.info("Cargue el archivo **Base_limpia_regresion_transporte_carga.xlsx** en el panel izquierdo. "
            "El dashboard no almacena los datos en GitHub.")
    st.stop()
try:
    d,origin=get_data(parse_excel(upload.getvalue()))
    if d is None:st.error("No se identificó una hoja Base_modelo ni las 11 preguntas originales.");st.stop()
    needed=["Flota_cat","Tipo_carga","Educacion_cat","Capacitacion_01",
            "Costo_1a5","Eficiencia_1a5","Numero_tecnologias_8"]+list(TECH)
    missing=[c for c in needed if c not in d.columns]
    if missing:
        st.error("La base no contiene las variables requeridas: "+", ".join(missing))
        st.stop()
    for c in list(TECH)+["Numero_tecnologias_8","Capacitacion_01","Incentivos_01",
                         "Flota_ord","Antiguedad_ord","Conocimiento_1a5","Costo_1a5","Eficiencia_1a5"]:
        if c in d.columns:d[c]=pd.to_numeric(d[c],errors="coerce")
    if d["Numero_tecnologias_8"].isna().all():
        d["Numero_tecnologias_8"]=d[list(TECH)].sum(axis=1)
except Exception as e:
    st.error(f"No se pudo leer el archivo: {e}");st.stop()

with st.sidebar:
    st.success(f"Datos: {origin}")
    st.markdown("### Filtros")
    for c,label in [("Flota_cat","Tamaño de flota"),("Tipo_carga","Tipo de carga"),
                    ("Educacion_cat","Nivel educativo"),("Capacitacion_01","Capacitación")]:
        opts=sorted(d[c].dropna().unique().tolist(),key=str)
        if c=="Capacitacion_01":
            chosen=st.multiselect(label,opts,default=opts,format_func=lambda x:"Sí" if x==1 else "No")
        else:chosen=st.multiselect(label,opts,default=opts)
        d=d[d[c].isin(chosen)]
    st.caption(f"Empresas seleccionadas: {len(d)}")
if d.empty:st.warning("Los filtros no dejan empresas para analizar.");st.stop()

k1,k2,k3,k4=st.columns(4)
with k1:metric("Empresas",len(d),"Muestra seleccionada")
with k2:metric("Tecnologías por empresa",f"{d['Numero_tecnologias_8'].mean():.2f}","Media de 8 tecnologías")
with k3:metric("Empresas capacitadas",f"{100*d['Capacitacion_01'].mean():.1f}%","P7 · Sí")
with k4:metric("Eficiencia percibida",f"{d['Eficiencia_1a5'].mean():.2f}/5","P11 · Promedio")
tabs=st.tabs(["Panorama","Empresas","Tecnologías","Capital humano","Costos y eficiencia",
              "Análisis estadístico","Datos"])
with tabs[0]:
    a,b=st.columns([1.25,1])
    with a:tech_chart(d,"pan_tech")
    with b:donut(d,"P3","P3 · Tipo de carga","pan_cargo")
    a,b=st.columns(2)
    with a:categorical(d,"P1","P1 · Tamaño de flota","pan_fleet")
    with b:donut(d,"P7","P7 · Capacitación","pan_training")
    likert(d,"pan_likert")
with tabs[1]:
    a,b=st.columns(2)
    with a:categorical(d,"P1","P1 · Vehículos operativos","emp_fleet")
    with b:donut(d,"P2","P2 · Antigüedad de la empresa","emp_age")
    categorical(d,"P3","P3 · Tipo de carga","emp_cargo",horizontal=True)
with tabs[2]:
    tech_chart(d,"technology_full")
    st.markdown("**P5 · Otras tecnologías reportadas**")
    p5=d["P5"].map(normalize)
    p5=p5[~p5.str.casefold().isin(["sin respuesta","no","ninguna","ninguno","n/a","no aplica"])]
    if p5.empty:st.info("No hay respuestas abiertas adicionales registradas.")
    else:st.dataframe(p5.value_counts().rename_axis("Respuesta").reset_index(name="Menciones"),
                      hide_index=True,use_container_width=True)
    fig=px.histogram(d,x="Numero_tecnologias_8",nbins=9,color_discrete_sequence=[TEAL])
    fig.update_xaxes(dtick=1,title="Número de tecnologías adoptadas")
    fig.update_yaxes(title="Empresas")
    panel("Intensidad de adopción tecnológica",fig,"tech_intensity")
with tabs[3]:
    a,b=st.columns(2)
    with a:donut(d,"P6","P6 · Nivel educativo","people_edu")
    with b:donut(d,"P7","P7 · Capacitación","people_train")
    categorical(d,"P8","P8 · Conocimiento de tecnologías","people_knowledge")
    box_compare(d,"Capacitacion_01","people_box")
with tabs[4]:
    a,b=st.columns(2)
    with a:categorical(d,"P9","P9 · Costos de implementación","cost_p9")
    with b:donut(d,"P10","P10 · Subsidios y apoyos","cost_p10")
    categorical(d,"P11","P11 · Eficiencia operativa percibida","cost_p11")
    likert(d,"cost_likert")
with tabs[5]:
    st.subheader("Relaciones estadísticas")
    st.caption("Análisis exploratorio con muestra no probabilística. Las asociaciones no implican causalidad.")
    corr_cols=["Numero_tecnologias_8","Flota_ord","Antiguedad_ord","Conocimiento_1a5",
               "Costo_1a5","Eficiencia_1a5"]
    corr_heatmap(d,corr_cols,"stat_corr")
    st.subheader("Comparaciones entre grupos")
    g=st.selectbox("Variable para comparar la adopción",["Capacitacion_01","Flota_cat","Incentivos_01"],
                   format_func=lambda c:{"Capacitacion_01":"Capacitación","Flota_cat":"Tamaño de flota",
                                          "Incentivos_01":"Apoyos gubernamentales"}[c])
    box_compare(d,g,"stat_box")
    test=group_test(d,g)
    if test:
        name,stat,p,ns=test
        st.markdown(f"**{name}:** estadístico = {stat:.3f}; valor *p* aproximado = {p:.4f}; tamaños de grupo = {ns}.")
        if min(ns)<5:st.warning("Al menos un grupo tiene menos de cinco empresas; interprete esta prueba con especial cautela.")
        st.caption("Prueba exploratoria sin ajuste por comparaciones múltiples. "
                   "Considere tamaños de efecto, distribución de los grupos y limitaciones de n.")
    st.subheader("Regresión exploratoria")
    c1,c2=st.columns(2)
    with c1:
        ycol=st.selectbox("Variable dependiente",["Eficiencia_1a5","Numero_tecnologias_8"],
                          format_func=lambda c:NUMERIC[c])
    with c2:
        options=[x for x in ["Numero_tecnologias_8","Conocimiento_1a5","Costo_1a5",
                            "Capacitacion_01","Flota_ord","Antiguedad_ord","Eficiencia_1a5"] if x!=ycol]
        xcol=st.selectbox("Variable explicativa (una sola)",options,format_func=lambda c:NUMERIC[c])
    regression(d,xcol,ycol,"stat_reg")
with tabs[6]:
    st.subheader("Base filtrada")
    st.dataframe(d,use_container_width=True,hide_index=True)
    st.download_button("Descargar CSV de datos filtrados",
                       d.to_csv(index=False).encode("utf-8-sig"),
                       file_name="transporte_carga_filtrado.csv",mime="text/csv")
    st.caption("Para modelos reproducibles, use las variables codificadas de la hoja Base_modelo.")
st.divider()
st.caption("Las conclusiones describen las empresas encuestadas. No se pueden extrapolar estadísticamente "
           "a todas las empresas de transporte de carga ni atribuir efectos causales.")
