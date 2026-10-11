import io
import re
import html
import unicodedata
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Tecnologías | Transporte de carga", page_icon="🚚", layout="wide", initial_sidebar_state="expanded")

NAVY="#103C59"
BLUE="#1768A0"
CYAN="#10A7B5"
GREEN="#53B977"
YELLOW="#F4B544"
CORAL="#F77964"
PINK="#ED6D98"
PURPLE="#8266C5"
PALETTE=[BLUE,CYAN,GREEN,YELLOW,CORAL,PINK,PURPLE,"#7797AD"]
BACKGROUND="#F3F7FB"
TEXT="#18334E"

st.markdown("""
<style>
.stApp {background:#F3F7FB;color:#18334E}
.block-container {max-width:1550px;padding-top:1.15rem;padding-bottom:1.5rem}
section[data-testid="stSidebar"] {background:linear-gradient(175deg,#103C59 0%,#075A76 100%);}
section[data-testid="stSidebar"] * {color:#F5FBFF!important}
section[data-testid="stSidebar"] [data-baseweb="select"] * {color:#1C3548!important}
section[data-testid="stSidebar"] input {color:#1C3548!important}
h1,h2,h3 {color:#123A59!important;letter-spacing:-.025em}
h1 {font-size:2rem!important}
div[data-testid="stVerticalBlockBorderWrapper"] > div {border-radius:15px!important}
div[data-testid="stTabs"] button {font-weight:650;font-size:.91rem;border-radius:8px}
div[data-testid="stTabs"] button[aria-selected="true"] {background:#079EAF;color:white!important}
.kpi {padding:17px 18px;border-radius:15px;min-height:125px;box-shadow:0 3px 14px #18344d10}
.kpi .klabel {font-size:.88rem;font-weight:600;color:#17344F}
.kpi .kvalue {font-size:2.1rem;font-weight:800;color:#123653;margin-top:7px;line-height:1.1}
.kpi .knote {font-size:.75rem;color:#486075;margin-top:8px}
.sectiontitle {font-weight:750;color:#143E5E;font-size:1.12rem;margin:.65rem 0 .4rem}
.smallnote {font-size:.82rem;color:#4D6477}
</style>
""",unsafe_allow_html=True)

@st.cache_data
def read_book(file_bytes):
    return pd.read_excel(io.BytesIO(file_bytes),sheet_name=None)

def normalize(x):
    if pd.isna(x): return "Sin respuesta"
    s=re.sub(r"\s+"," ",str(x)).strip()
    return s if s else "Sin respuesta"

def base_original(sheets):
    for sheet,df in sheets.items():
        found={}
        for c in df.columns:
            m=re.search(r"Pregunta\s*(\d+)\s*:",str(c),re.I)
            if m and 1<=int(m.group(1))<=11:found[c]="P"+m.group(1)
        if len(found)>=9:
            d=df.rename(columns=found).copy()
            for i in range(1,12):
                if "P"+str(i) not in d:d["P"+str(i)]=pd.NA
            return d,sheet
    return None,None

def base_modelo(sheets):
    for sheet,df in sheets.items():
        if {"Flota_cat","Eficiencia_1a5"}.issubset(df.columns):
            mp={"Flota_cat":"P1","Antiguedad_cat":"P2","Tipo_carga":"P3","Tecnologias_originales":"P4",
                "Otras_texto":"P5","Educacion_cat":"P6","Conocimiento_cat":"P8","Costo_1a5":"P9","Eficiencia_1a5":"P11"}
            d=df.rename(columns=mp).copy()
            if "Capacitacion_01" in d:d["P7"]=d["Capacitacion_01"].map({1:"Sí",0:"No"})
            if "Incentivos_01" in d:d["P10"]=d["Incentivos_01"].map({1:"Sí",0:"No"})
            for i in range(1,12):
                if "P"+str(i) not in d:d["P"+str(i)]=pd.NA
            return d,sheet
    return None,None

def values(df,col):
    return df[col].map(normalize).replace({"Si":"Sí","SI":"Sí","si":"Sí"})

def categorical(df,col):
    v=values(df,col)
    return v[v!="Sin respuesta"]

def counts(df,col,order=None):
    v=categorical(df,col)
    z=v.value_counts().rename_axis("Categoría").reset_index(name="Empresas")
    if order:
        z["orden"]=z["Categoría"].map({str(x):i for i,x in enumerate(order)}).fillna(len(order))
        z=z.sort_values(["orden","Categoría"])
    else:z=z.sort_values("Empresas",ascending=False)
    z["Porcentaje"]=z["Empresas"]/max(1,len(v))*100
    return z

def style_fig(fig,height=315,legend=False):
    fig.update_layout(height=height,margin=dict(l=8,r=16,t=20,b=40),paper_bgcolor="white",plot_bgcolor="white",
                      font=dict(family="Arial",color=TEXT,size=12),showlegend=legend)
    fig.update_xaxes(showgrid=False,zeroline=False,linecolor="#D7E3ED")
    fig.update_yaxes(gridcolor="#E8EEF4",zeroline=False)
    return fig

def card_chart(title,fig,key,subtitle=None):
    with st.container(border=True):
        st.markdown(f'<div class="sectiontitle">{html.escape(title)}</div>',unsafe_allow_html=True)
        if subtitle:st.caption(subtitle)
        st.plotly_chart(fig,use_container_width=True,key=key,config={"displaylogo":False,"toImageButtonOptions":{"format":"png","scale":3}})

def bar(df,col,title,key,horizontal=False,order=None):
    z=counts(df,col,order)
    if z.empty:
        st.info(f"No hay respuestas para {title}.");return
    z["Etiqueta"]=z["Porcentaje"].map(lambda x:f"{x:.1f}%")
    colors=[PALETTE[i%len(PALETTE)] for i in range(len(z))]
    if horizontal:
        z=z.iloc[::-1]
        colors=colors[::-1]
        fig=go.Figure(go.Bar(x=z["Porcentaje"],y=z["Categoría"],orientation="h",text=z["Etiqueta"],
                             textposition="outside",marker_color=colors,customdata=z[["Empresas"]],
                             hovertemplate="%{y}<br>%{x:.1f}% · %{customdata[0]} empresas<extra></extra>"))
        fig.update_xaxes(title="Empresas (%)",range=[0,max(105,float(z["Porcentaje"].max())*1.16)])
        fig.update_yaxes(automargin=True)
    else:
        fig=go.Figure(go.Bar(x=z["Categoría"],y=z["Porcentaje"],text=z["Etiqueta"],textposition="outside",
                             marker_color=colors,customdata=z[["Empresas"]],
                             hovertemplate="%{x}<br>%{y:.1f}% · %{customdata[0]} empresas<extra></extra>"))
        fig.update_yaxes(title="Empresas (%)",range=[0,max(105,float(z["Porcentaje"].max())*1.16)])
        fig.update_xaxes(tickangle=-18,automargin=True)
    card_chart(title,style_fig(fig,height=340 if not horizontal else max(300,55*len(z))),key)

def donut(df,col,title,key):
    z=counts(df,col)
    if z.empty:
        st.info(f"No hay respuestas para {title}.");return
    fig=go.Figure(go.Pie(labels=z["Categoría"],values=z["Empresas"],hole=.61,
                         marker=dict(colors=PALETTE[:len(z)]),textinfo="percent",
                         textfont=dict(size=13,color="white"),sort=False))
    fig.update_layout(annotations=[dict(text=f"<b>{len(categorical(df,col))}</b><br>respuestas",showarrow=False,
                                        font=dict(size=13,color=NAVY))],
                      legend=dict(orientation="h",y=-.13,x=0,font=dict(size=11)))
    card_chart(title,style_fig(fig,height=345,legend=True),key)

TECHS=[
("GPS y rastreo en tiempo real","GPS y rastreo"),
("Software de gestión de rutas","Gestión de rutas"),
("Sensores IoT en vehículos","Sensores IoT"),
("Plataformas de gestión logística (TMS, WMS)","Plataformas TMS/WMS"),
("Aplicaciones móviles para conductores","Aplicaciones móviles"),
("Sistemas de mantenimiento predictivo","Mantenimiento predictivo"),
("Telemetría avanzada","Telemetría"),
("Tecnología de monitoreo de emisiones","Monitoreo de emisiones")]
def tech_table(df):
    s=df["P4"].fillna("").astype(str)
    data=[]
    for phrase,short in TECHS:
        n=int(s.str.contains(re.escape(phrase),case=False,regex=True).sum())
        data.append({"Tecnología":short,"Empresas":n,"Porcentaje":100*n/max(1,len(df))})
    return pd.DataFrame(data).sort_values("Porcentaje",ascending=False)

def technology_chart(df,key):
    z=tech_table(df)
    z=z.iloc[::-1]
    fig=go.Figure(go.Bar(x=z["Porcentaje"],y=z["Tecnología"],orientation="h",
                         marker_color=[PALETTE[i%len(PALETTE)] for i in range(len(z))],
                         text=z["Porcentaje"].map(lambda x:f"{x:.1f}%"),textposition="outside",
                         customdata=z[["Empresas"]],
                         hovertemplate="%{y}<br>%{x:.1f}% · %{customdata[0]} empresas<extra></extra>"))
    fig.update_xaxes(title="Empresas (%)",range=[0,112])
    fig.update_yaxes(automargin=True)
    card_chart("P4 · Tecnologías implementadas",style_fig(fig,height=390),key,
               "Selección múltiple: los porcentajes no suman necesariamente 100 %.")

def cross(df,a,b,title,key):
    a0=categorical(df,a)
    b0=categorical(df,b)
    valid=(values(df,a)!="Sin respuesta")&(values(df,b)!="Sin respuesta")
    tab=pd.crosstab(values(df.loc[valid],a),values(df.loc[valid],b))
    if tab.empty:
        st.info("No hay datos suficientes.");return
    fig=px.imshow(tab,text_auto=True,aspect="auto",color_continuous_scale=[[0,"#ECF7F9"],[1,CYAN]])
    fig.update_coloraxes(showscale=False)
    fig.update_xaxes(title="")
    fig.update_yaxes(title="")
    card_chart(title,style_fig(fig,335),key)

def kpi(label,value,note,bg):
    st.markdown(f"""<div class="kpi" style="background:{bg}">
      <div class="klabel">{html.escape(str(label))}</div>
      <div class="kvalue">{html.escape(str(value))}</div>
      <div class="knote">{html.escape(str(note))}</div></div>""",unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🚚 Transporte de carga")
    st.markdown("**Adopción tecnológica en empresas colombianas**")
    st.caption("Dashboard de resultados de encuesta")
    upload=st.file_uploader("Cargar archivo Excel",type=["xlsx"])
    st.caption("Admite la base original o la base limpia para regresión. No es necesario publicar respuestas en GitHub.")

st.title("Adopción tecnológica | Transporte de carga")
st.caption("Resultados descriptivos · Encuesta empresarial · Visualizaciones interactivas")
if upload is None:
    st.info("Cargue su Excel desde el panel lateral para visualizar los gráficos de las 11 preguntas.")
    st.stop()
try:
    sheets=read_book(upload.getvalue())
    d,sheet=base_original(sheets)
    if d is None:d,sheet=base_modelo(sheets)
    if d is None:st.error("No se reconoció la estructura de la encuesta.");st.stop()
except Exception as exc:
    st.error(f"No fue posible leer el archivo: {exc}");st.stop()

with st.sidebar:
    st.success(f"Hoja: {sheet}")
    st.markdown("### Filtros")
    selections={}
    for col,name in [("P1","Tamaño de flota"),("P3","Tipo de carga"),("P6","Nivel educativo"),("P7","Capacitación")]:
        opts=sorted(categorical(d,col).unique().tolist())
        selections[col]=st.multiselect(name,opts,default=opts,key="filter_"+col)
    for col,chosen in selections.items():
        d=d[values(d,col).isin(chosen)]
    st.caption(f"Empresas en la selección: {len(d)}")
if d.empty:
    st.warning("Los filtros no dejan registros. Amplíe la selección en el panel lateral.");st.stop()

trained=values(d,"P7").str.casefold().isin(["sí","si"]).mean()*100
supported=values(d,"P10").str.casefold().isin(["sí","si"]).mean()*100
hastech=(tech_table(d)["Empresas"].sum())
adopted=d["P4"].fillna("").astype(str).str.strip().ne("").mean()*100

a,b,c,e=st.columns(4)
with a:kpi("Empresas encuestadas",str(len(d)),"Muestra filtrada","#DBECFD")
with b:kpi("Con capacitación",f"{trained:.1f}%","Pregunta 7","#E8E1FC")
with c:kpi("Implementan tecnología",f"{adopted:.1f}%","Pregunta 4","#DDF5EC")
with e:kpi("Con apoyo gubernamental",f"{supported:.1f}%","Pregunta 10","#FFF0D9")

tabs=st.tabs(["Panorama","Empresas","Tecnologías","Capital humano","Costos y eficiencia","Datos"])
with tabs[0]:
    a,b=st.columns([1,1])
    with a:bar(d,"P1","P1 · Tamaño de flota","overview_fleet")
    with b:donut(d,"P3","P3 · Tipo de carga","overview_cargo")
    a,b=st.columns([1.25,1])
    with a:technology_chart(d,"overview_tech")
    with b:donut(d,"P7","P7 · Capacitación tecnológica","overview_train")
    a,b=st.columns(2)
    with a:bar(d,"P9","P9 · Costos percibidos (1–5)","overview_cost",order=["1","2","3","4","5"])
    with b:bar(d,"P11","P11 · Eficiencia percibida (1–5)","overview_eff",order=["1","2","3","4","5"])
with tabs[1]:
    a,b=st.columns(2)
    with a:bar(d,"P1","P1 · Vehículos operativos","companies_fleet")
    with b:donut(d,"P2","P2 · Antigüedad de la empresa","companies_age")
    bar(d,"P3","P3 · Tipo de carga transportada","companies_cargo")
with tabs[2]:
    technology_chart(d,"tech_tab")
    st.markdown('<div class="sectiontitle">P5 · Otras tecnologías mencionadas</div>',unsafe_allow_html=True)
    other=categorical(d,"P5")
    other=other[~other.str.casefold().isin(["no","ninguna","no aplica","n/a","ninguno"])]
    if other.empty:st.info("No se registraron respuestas abiertas en la pregunta 5.")
    else:st.dataframe(other.value_counts().rename_axis("Tecnología").reset_index(name="Menciones"),hide_index=True,use_container_width=True)
with tabs[3]:
    a,b=st.columns(2)
    with a:donut(d,"P6","P6 · Nivel educativo","people_education")
    with b:donut(d,"P7","P7 · Capacitación","people_training")
    bar(d,"P8","P8 · Conocimiento tecnológico","people_knowledge")
    cross(d,"P7","P8","Capacitación y conocimiento","people_cross")
with tabs[4]:
    a,b=st.columns(2)
    with a:bar(d,"P9","P9 · Costos de implementación (1–5)","costs",order=["1","2","3","4","5"])
    with b:donut(d,"P10","P10 · Subsidios y apoyos","support")
    bar(d,"P11","P11 · Eficiencia operativa (1–5)","efficiency",order=["1","2","3","4","5"])
    cross(d,"P9","P11","Costos y eficiencia percibida","cost_eff_cross")
with tabs[5]:
    st.subheader("Respuestas filtradas")
    cols=[f"P{i}" for i in range(1,12)]
    st.dataframe(d[cols],use_container_width=True,hide_index=True)
    st.download_button("Descargar CSV filtrado",data=d[cols].to_csv(index=False).encode("utf-8-sig"),
                       file_name="encuesta_transporte_filtrada.csv",mime="text/csv")
    st.caption("P1–P11 corresponden a las preguntas del cuestionario original.")
st.caption("Nota: los porcentajes se calculan sobre respuestas válidas por pregunta, salvo P4, que utiliza el número de empresas filtradas. La muestra no probabilística no permite generalizaciones poblacionales.")
