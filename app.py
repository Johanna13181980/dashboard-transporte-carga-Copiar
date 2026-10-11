import io, re, html, math
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

st.set_page_config(page_title='Transporte de carga | Evidencia empírica',page_icon='📊',layout='wide')
NAVY='#173B55'; TEAL='#217C83'; BLUE='#487EA2'; CYAN='#5EADB0'; GOLD='#C49A52'; SAGE='#76A591'; PLUM='#94799E'; CORAL='#C48470'; SLATE='#708B9E'
COLORS=[TEAL,BLUE,GOLD,SAGE,PLUM,CORAL,CYAN,SLATE]
TECH={'T1_GPS':'GPS y rastreo','T2_Rutas':'Gestión de rutas','T3_IoT':'Sensores IoT','T4_TMS_WMS':'TMS / WMS','T5_Apps':'Aplicaciones móviles','T6_Mantenimiento':'Mantenimiento predictivo','T7_Telemetria':'Telemetría','T8_Emisiones':'Monitoreo de emisiones'}
NUM={'Numero_tecnologias_8':'Tecnologías adoptadas','Flota_ord':'Tamaño de flota','Antiguedad_ord':'Antigüedad','Conocimiento_1a5':'Conocimiento','Costo_1a5':'Costos percibidos','Eficiencia_1a5':'Eficiencia percibida'}
st.markdown('''<style>
:root{--accent:#C74653;--navy:#173B55;--muted:#5B7486;--surface:#FFFFFF}
.stApp{background:#F3F6F9;color:#173B55}
.block-container{max-width:1420px;padding-top:1.4rem;padding-bottom:2rem}
h1,h2,h3{color:#173B55!important;letter-spacing:-.02em}
h1{font-size:2rem!important}
h3{font-size:1.24rem!important}
section[data-testid="stSidebar"]{background:#173B55!important;border-right:1px solid #234B63}
section[data-testid="stSidebar"] h2,section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"]{color:#F0F5F7!important}
section[data-testid="stSidebar"] [data-baseweb="select"]>div{background:#FFF!important;border:1px solid #C6D4DF!important;border-radius:9px!important}
section[data-testid="stSidebar"] [data-baseweb="select"] input{color:#173B55!important}
section[data-testid="stSidebar"] [data-baseweb="tag"],
section[data-testid="stSidebar"] [data-baseweb="tag"] span{background:#C74653!important;background-color:#C74653!important;border-color:#C74653!important;color:#FFF!important}
section[data-testid="stSidebar"] [data-baseweb="tag"] *,
section[data-testid="stSidebar"] [data-baseweb="tag"] svg{color:#FFF!important;fill:#FFF!important}
section[data-testid="stSidebar"] [data-baseweb="tag"] button{background:transparent!important}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]{background:#EAF1F6!important;border:2px dashed #7B9BAD!important;border-radius:12px!important}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] *{color:#173B55!important}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button{background:#C74653!important;color:#FFF!important;border:0!important}
section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"]{background:#E5EFF4!important;border-radius:9px!important}
section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] *{color:#173B55!important}
/* Un solo color para texto, borde y subrayado; oculta el indicador nativo */
.stTabs [data-baseweb="tab-list"]{gap:6px!important;border-bottom:1px solid #D7E2E9!important}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"]{display:none!important;background:transparent!important}
.stTabs [data-baseweb="tab"]{position:relative!important;color:#597387!important;
 border:1px solid transparent!important;border-radius:9px 9px 0 0!important;
 padding:10px 13px!important;background:transparent!important;font-weight:550!important}
.stTabs [data-baseweb="tab"][aria-selected="true"],
.stTabs button[role="tab"][aria-selected="true"]{color:#C74653!important;
 background:#FFF4F4!important;border:1px solid #F0D3D6!important;
 border-bottom:3px solid #C74653!important;font-weight:750!important}
.stTabs [data-baseweb="tab"][aria-selected="true"] *,
.stTabs button[role="tab"][aria-selected="true"] *{color:#C74653!important}
.stTabs [data-baseweb="tab"]:focus{box-shadow:none!important}
.stTabs [data-baseweb="tab"]:hover{background:#FBECEF!important;color:#C74653!important}
div[data-testid="stVerticalBlockBorderWrapper"]>div[data-testid="stVerticalBlock"]{border-radius:14px}
div[data-testid="stVerticalBlockBorderWrapper"]{border-radius:14px!important}
div[data-testid="stMetric"]{background:#FFF;border:1px solid #DCE5EB;border-radius:12px;padding:15px}
button[kind="primary"],div[data-testid="stButton"] button[kind="primary"]{background:#C74653!important;border-color:#C74653!important}
.kpi{border:1px solid #DFE7EC;border-left:4px solid #C74653;background:#FFF;border-radius:12px;padding:17px 19px;box-shadow:0 3px 13px #173B5508;min-height:108px}
.kpi small{color:#5D788B;font-size:12px}
.kpi b{display:block;font-size:29px;color:#173B55;margin:6px 0 4px;font-weight:750}
.hero{background:linear-gradient(112deg,#173B55,#275C75);border-radius:17px;
padding:22px 28px;margin-bottom:18px;color:white;box-shadow:0 8px 26px #173B5520}
.hero h1{color:#FFF!important;font-size:1.85rem!important;margin:0 0 8px!important}
.hero p{color:#DBEAF1!important;font-size:14px;margin:0}
.hero .eyebrow{color:#E9A6AD!important;text-transform:uppercase;letter-spacing:.13em;font-size:11px;font-weight:800;margin-bottom:9px}
</style>''',unsafe_allow_html=True)

def norm(x):
    if pd.isna(x):return 'Sin respuesta'
    s=re.sub(r'\s+',' ',str(x)).strip()
    return s or 'Sin respuesta'

@st.cache_data
def read_book(raw):return pd.read_excel(io.BytesIO(raw),sheet_name=None)

def read_data(book):
    if 'Base_modelo' in book:
        d=book['Base_modelo'].copy()
        if 'Respuestas_originales' in book and len(book['Respuestas_originales'])==len(d):
            original=book['Respuestas_originales']
            for col in original.columns:
                m=re.search(r'Pregunta\s*(\d+)\s*:',str(col),re.I)
                if m:d['P'+m.group(1)]=original[col].to_numpy()
    else:
        d=None
        for raw in book.values():
            q={}
            for col in raw.columns:
                m=re.search(r'Pregunta\s*(\d+)\s*:',str(col),re.I)
                if m:q[int(m.group(1))]=col
            if len(q)<10:continue
            d=pd.DataFrame(index=raw.index)
            for i in range(1,12):d['P'+str(i)]=raw[q[i]] if i in q else np.nan
            d['Flota_cat']=d['P1'].map(norm);d['Antiguedad_cat']=d['P2'].map(norm);d['Tipo_carga']=d['P3'].map(norm)
            d['Educacion_cat']=d['P6'].map(norm);d['Conocimiento_cat']=d['P8'].map(norm);d['Antiguedad_cat']=d['P2'].map(norm)
            d['Flota_ord']=d['Flota_cat'].map({'1-5':1,'6-15':2,'16-30':3,'Más de 30':4})
            d['Antiguedad_ord']=d['Antiguedad_cat'].map({'Menos de 1 año':1,'1-5 años':2,'De 6 a 10 años':3,'6-10 años':3,'Más de 10 años':4})
            d['Educacion_ord']=d['Educacion_cat'].map({'Primaria':1,'Secundaria':2,'Técnico o tecnólogo':3,'Técnico/Tecnólogo':3,'Profesional':4,'Posgrado':5})
            yes=lambda v: 1 if norm(v).lower() in ['sí','si'] else (0 if norm(v).lower()=='no' else np.nan)
            d['Capacitacion_01']=d['P7'].map(yes);d['Incentivos_01']=d['P10'].map(yes)
            d['Conocimiento_1a5']=d['Conocimiento_cat'].map({'Muy bajo':1,'Bajo':2,'Medio':3,'Alto':4,'Muy alto':5})
            d['Costo_1a5']=pd.to_numeric(d['P9'],errors='coerce');d['Eficiencia_1a5']=pd.to_numeric(d['P11'],errors='coerce')
            phrases=['GPS y rastreo en tiempo real','Software de gestión de rutas','Sensores IoT en vehículos','Plataformas de gestión logística (TMS, WMS)','Aplicaciones móviles para conductores','Sistemas de mantenimiento predictivo','Telemetría avanzada','Tecnología de monitoreo de emisiones']
            for key,phrase in zip(TECH,phrases):d[key]=d['P4'].fillna('').astype(str).str.contains(re.escape(phrase),case=False).astype(int)
            d['Numero_tecnologias_8']=d[list(TECH)].sum(axis=1)
            d['Otras_texto']=d['P5']
            break
    if d is None:return None
    for i in range(1,12):
        if 'P'+str(i) not in d:d['P'+str(i)]=np.nan
    required=['Flota_cat','Tipo_carga','Educacion_cat','Capacitacion_01','Flota_ord','Numero_tecnologias_8']+list(TECH)
    missing=[c for c in required if c not in d]
    if missing:raise ValueError('Faltan columnas: '+', '.join(missing))
    for c in list(TECH)+['Numero_tecnologias_8','Flota_ord','Capacitacion_01','Incentivos_01','Conocimiento_1a5','Costo_1a5','Eficiencia_1a5','Antiguedad_ord']:
        if c in d:d[c]=pd.to_numeric(d[c],errors='coerce')
    return d

def graph(fig,title,key,caption='',height=355):
    with st.container(border=True):
        st.markdown('#### '+title)
        if caption:st.caption(caption)
        fig.update_layout(height=height,margin=dict(l=15,r=28,t=16,b=45),paper_bgcolor='white',plot_bgcolor='white',font=dict(family='Arial',color='#31556A',size=12),legend=dict(orientation='h',y=-.22),hoverlabel=dict(bgcolor='#173B55',font_color='white'))
        fig.update_xaxes(gridcolor='#E9EFF3',zeroline=False)
        fig.update_yaxes(gridcolor='#E9EFF3',zeroline=False)
        st.plotly_chart(fig,use_container_width=True,key=key,config={'displaylogo':False,'toImageButtonOptions':{'format':'png','scale':3}})

def kpi(title,value,desc):
    st.markdown(f'<div class="kpi"><small>{html.escape(title)}</small><b>{html.escape(str(value))}</b><small>{html.escape(desc)}</small></div>',unsafe_allow_html=True)

def counts(s):
    x=s.map(norm);x=x[x!='Sin respuesta'];return x.value_counts()

def spearman(x,y):
    sub=pd.DataFrame({'x':x,'y':y}).apply(pd.to_numeric,errors='coerce').dropna()
    if len(sub)<4 or sub.x.nunique()<2 or sub.y.nunique()<2:return np.nan
    return float(np.corrcoef(sub.x.rank(method='average'),sub.y.rank(method='average'))[0,1])

def glm_binomial(y,flota,trials=8):
    """IRLS ML for grouped Binomial(8,p), single ordinal covariate."""
    a=pd.DataFrame({'y':y,'x':flota}).apply(pd.to_numeric,errors='coerce').dropna()
    a=a[(a.y>=0)&(a.y<=trials)&(a.y.round()==a.y)]
    if len(a)<8 or a.x.nunique()<2:return None
    X=np.column_stack([np.ones(len(a)),a.x.to_numpy(float)])
    yy=a.y.to_numpy(float)
    beta=np.array([math.log(max(.001,min(.999,yy.sum()/(trials*len(yy))))/(1-max(.001,min(.999,yy.sum()/(trials*len(yy)))))),0.])
    def ll(b):
        eta=np.clip(X@b,-30,30)
        return float(np.sum(yy*eta-trials*np.logaddexp(0,eta)+np.array([math.lgamma(trials+1)-math.lgamma(k+1)-math.lgamma(trials-k+1) for k in yy])))
    converged=False
    for it in range(200):
        eta=np.clip(X@beta,-30,30)
        p=1/(1+np.exp(-eta))
        w=np.maximum(trials*p*(1-p),1e-10)
        info=X.T@(w[:,None]*X)
        grad=X.T@(yy-trials*p)
        try:step=np.linalg.solve(info,grad)
        except np.linalg.LinAlgError:return None
        current=ll(beta);fraction=1.
        while fraction>1e-7 and ll(beta+fraction*step)<current-1e-9:fraction/=2
        updated=beta+fraction*step
        if np.max(np.abs(updated-beta))<1e-10:
            beta=updated;converged=True;break
        beta=updated
    if not converged:return None
    eta=np.clip(X@beta,-30,30);p=1/(1+np.exp(-eta))
    info=X.T@((trials*p*(1-p))[:,None]*X)
    try:cov=np.linalg.inv(info)
    except np.linalg.LinAlgError:return None
    se=np.sqrt(np.diag(cov));z=beta[1]/se[1];pv=math.erfc(abs(z)/math.sqrt(2))
    b0=math.log(np.clip(yy.sum()/(trials*len(yy)),1e-9,1-1e-9)/np.clip(1-yy.sum()/(trials*len(yy)),1e-9,1))
    lr=2*(ll(beta)-ll(np.array([b0,0.])))
    pearson=float(np.sum((yy-trials*p)**2/np.maximum(trials*p*(1-p),1e-10)))/(len(a)-2)
    return dict(beta=beta,se=se,pvalue=pv,odds=np.exp(beta[1]),ci=np.exp(beta[1]+np.array([-1.96,1.96])*se[1]),n=len(a),ll=ll(beta),aic=4-2*ll(beta),lr=lr,disp=pearson,frame=a)

with st.sidebar:
    st.markdown('## Transporte de carga')
    st.caption('Evidencia empírica · Adopción tecnológica')
    file=st.file_uploader('Cargar base Excel',type=['xlsx'])
    st.caption('La base se procesa durante la sesión; no la publique en GitHub.')
st.markdown('''<div class="hero">
<div class="eyebrow">Observatorio de transformación digital · Evidencia empírica</div>
<h1>Adopción tecnológica en el transporte de carga</h1>
<p>Estudio transversal · 22 empresas encuestadas · Muestreo no probabilístico · Análisis descriptivo y regresión binomial exploratoria</p>
</div>''',unsafe_allow_html=True)
if file is None:
    st.info('Cargue la base limpia de la encuesta en el panel izquierdo para activar los análisis.');st.stop()
try:d=read_data(read_book(file.getvalue()))
except Exception as exc:st.error('No fue posible interpretar la base: '+str(exc));st.stop()
if d is None:st.error('No se encontró una hoja Base_modelo ni las preguntas originales.');st.stop()
with st.sidebar:
    st.success('Base reconocida')
    st.markdown('### Filtros')
    for col,name in [('Flota_cat','Tamaño de flota'),('Tipo_carga','Tipo de carga'),('Educacion_cat','Nivel educativo'),('Capacitacion_01','Capacitación')]:
        opts=sorted(d[col].dropna().unique().tolist(),key=str)
        if col=='Capacitacion_01':
            selected=st.multiselect(name,opts,default=opts,format_func=lambda x:'Sí' if x==1 else 'No',key='filtro_'+col)
        else:
            selected=st.multiselect(name,opts,default=opts,key='filtro_'+col)
        d=d[d[col].isin(selected)]
    st.caption(f'Empresas seleccionadas: {len(d)} de 22')
    st.progress(min(len(d)/22,1.0),text='Cobertura de muestra')
if d.empty:st.warning('No hay empresas con estos filtros.');st.stop()
cols=st.columns(4)
with cols[0]:kpi('Empresas',len(d),'Muestra filtrada')
with cols[1]:kpi('Adopción media',f"{d.Numero_tecnologias_8.mean():.2f}/8",'Tecnologías por empresa')
with cols[2]:kpi('Con capacitación',f"{100*d.Capacitacion_01.mean():.1f}%",'Respuestas válidas')
with cols[3]:kpi('Eficiencia percibida',f"{d.Eficiencia_1a5.mean():.2f}/5",'Escala ordinal')
tabs=st.tabs(['Síntesis','Perfil empresarial','Mapa tecnológico','Capacidades','Percepciones','Regresión binomial (GLM)','Datos'])
with tabs[0]:
    st.subheader('Panorama de adopción tecnológica')
    c1,c2=st.columns([1.2,1])
    with c1:
        z=pd.DataFrame({'Tecnología':list(TECH.values()),'Empresas':[int(d[c].sum()) for c in TECH]})
        z=z.sort_values('Empresas')
        fig=go.Figure(go.Bar(x=100*z.Empresas/len(d),y=z.Tecnología,orientation='h',marker_color=[COLORS[list(TECH.values()).index(x)%len(COLORS)] for x in z.Tecnología],text=[f'{v}/{len(d)}' for v in z.Empresas],textposition='outside'))
        fig.update_xaxes(title='% de empresas',range=[0,115]);graph(fig,'Tecnologías más utilizadas','overview_tech','Respuesta múltiple: los porcentajes no suman 100 %.',410)
    with c2:
        hist=d.Numero_tecnologias_8.value_counts().reindex(range(9),fill_value=0)
        fig=go.Figure(go.Bar(x=hist.index,y=hist.values,marker_color=TEAL,text=hist.values,textposition='outside'))
        fig.update_xaxes(dtick=1,title='Número de tecnologías (0–8)');fig.update_yaxes(title='Empresas')
        graph(fig,'Distribución de intensidad tecnológica','overview_dist','Número de tecnologías distintas implementadas por empresa.',410)
    st.caption('Lectura: describa qué tecnologías predominan y cuántas adopta cada empresa. No se infieren impactos ambientales medidos.')
with tabs[1]:
    st.subheader('Caracterización de las empresas')
    c1,c2=st.columns(2)
    with c1:
        z=counts(d.P1 if d.P1.notna().any() else d.Flota_cat)
        fig=go.Figure(go.Bar(y=z.index[::-1],x=z.values[::-1],orientation='h',marker_color=BLUE,text=z.values[::-1],textposition='outside'))
        fig.update_xaxes(title='Empresas');graph(fig,'Tamaño de flota','profile_fleet','Frecuencias absolutas.',345)
    with c2:
        z=counts(d.P2 if d.P2.notna().any() else d.Antiguedad_cat)
        if z.empty:st.info('No hay respuestas para antigüedad.')
        fig=go.Figure(go.Pie(labels=z.index,values=z.values,hole=.62,marker_colors=COLORS,textinfo='percent'))
        graph(fig,'Antigüedad empresarial','profile_age','Distribución de la muestra.',345)
    z=counts(d.P3 if d.P3.notna().any() else d.Tipo_carga)
    fig=go.Figure(go.Treemap(labels=list(z.index),parents=['']*len(z),values=list(z.values),marker_colors=COLORS[:len(z)],textinfo='label+value+percent root'))
    graph(fig,'Composición por tipo de carga','profile_cargo','El área de cada rectángulo representa el número de empresas.',335)
with tabs[2]:
    st.subheader('Estructura y combinación de tecnologías')
    mat=d[list(TECH)].fillna(0).gt(0).astype(int)
    co=mat.T.dot(mat)
    fig=go.Figure(go.Heatmap(z=co.to_numpy(),x=list(TECH.values()),y=list(TECH.values()),colorscale=[[0,'#EFF5F7'],[.5,'#A2C9C7'],[1,TEAL]],text=co.to_numpy(),texttemplate='%{text}',colorbar=dict(title='Empresas')))
    fig.update_xaxes(tickangle=-35,automargin=True);fig.update_yaxes(autorange='reversed')
    graph(fig,'Matriz de coadopción tecnológica','technology_co','Cada celda muestra empresas que implementaron simultáneamente dos tecnologías; la diagonal representa frecuencias.',535)
    patterns=mat.apply(lambda row:', '.join([TECH[c] for c in TECH if row[c]]) or 'Ninguna',axis=1).value_counts().head(8)
    st.markdown('**Adopción tecnológica por tamaño de flota**')
    groups=(d.dropna(subset=['Flota_cat']).groupby('Flota_cat',observed=True))
    if len(groups):
        fleet_order=[v for v in ['1-5','6-15','16-30','Más de 30'] if v in groups.groups]
        fleet_order += [v for v in groups.groups if v not in fleet_order]
        rates=np.array([[100*groups.get_group(f)[c].mean() for c in TECH] for f in fleet_order])
        ns=[len(groups.get_group(f)) for f in fleet_order]
        fig=go.Figure(go.Heatmap(
            z=rates,x=list(TECH.values()),
            y=[f'{f} (n={n})' for f,n in zip(fleet_order,ns)],
            colorscale=[[0,'#EAF2F4'],[.5,'#82B8B5'],[1,'#217C83']],
            zmin=0,zmax=100,text=np.rint(rates).astype(int),
            texttemplate='%{text}%',colorbar=dict(title='%')))
        fig.update_xaxes(tickangle=-30,automargin=True)
        graph(fig,'Mapa de calor: tecnologías × tamaño de flota','tech_by_fleet',
              'Porcentaje dentro de cada categoría de flota; interpretar con cautela los grupos pequeños.',390)
    st.markdown('**Combinaciones tecnológicas más frecuentes**')
    st.dataframe(pd.DataFrame({'Combinación':patterns.index,'Empresas':patterns.values}),hide_index=True,use_container_width=True)
with tabs[3]:
    st.subheader('Capacidades organizacionales')
    c1,c2=st.columns(2)
    with c1:
        z=counts(d.P6 if d.P6.notna().any() else d.Educacion_cat)
        fig=go.Figure(go.Scatter(x=z.values,y=z.index,mode='markers',marker=dict(size=17,color=PLUM),text=z.values,textposition='middle right'))
        for label,val in z.items():fig.add_shape(type='line',x0=0,x1=int(val),y0=label,y1=label,line=dict(color='#B5C5CF',width=3))
        fig.update_xaxes(title='Empresas',range=[0,max(z.values)*1.25])
        graph(fig,'Nivel educativo: gráfico de puntos','capacity_education','Frecuencia de cada nivel educativo.',330)
    with c2:
        z=counts(d.P7 if d.P7.notna().any() else d.Capacitacion_01.map({0:'No',1:'Sí'}))
        fig=go.Figure(go.Pie(labels=z.index,values=z.values,hole=.65,marker_colors=[TEAL,GOLD],textinfo='percent+label'))
        graph(fig,'Capacitación reportada','capacity_training','Distribución de respuestas válidas.',330)
    z=counts(d.P8 if d.P8.notna().any() else d.Conocimiento_cat)
    fig=go.Figure(go.Bar(x=z.index,y=z.values,marker_color=COLORS[:len(z)],text=z.values,textposition='outside'))
    fig.update_yaxes(title='Empresas');graph(fig,'Conocimiento tecnológico','capacity_knowledge','Respuestas por nivel declarado.',310)
    sub=d[['Conocimiento_cat','Numero_tecnologias_8']].dropna()
    g=sub.groupby('Conocimiento_cat').Numero_tecnologias_8.agg(['mean','size']).reset_index().sort_values('mean')
    fig=go.Figure(go.Bar(x=g['mean'],y=g.Conocimiento_cat,orientation='h',marker_color=SAGE,text=[f'{a:.2f} (n={n})' for a,n in zip(g['mean'],g['size'])],textposition='outside'))
    fig.update_xaxes(range=[0,9],title='Tecnologías por empresa');graph(fig,'Adopción según conocimiento','capacity_relation','Comparación descriptiva; grupos pequeños requieren cautela.',335)
with tabs[4]:
    st.subheader('Costos, incentivos y eficiencia percibida')
    vals=[]
    for field,label in [('Costo_1a5','Costos'),('Eficiencia_1a5','Eficiencia')]:
        a=d[field].dropna();vals.append((label,a))
    fig=go.Figure()
    likert_colors=['#B66F77','#D7A18C','#C6CFD4','#87B8A5',TEAL]
    for score in range(1,6):
        fig.add_trace(go.Bar(y=[x[0] for x in vals],x=[100*(x[1]==score).mean() if len(x[1]) else 0 for x in vals],orientation='h',name=str(score),marker_color=likert_colors[score-1]))
    fig.update_layout(barmode='stack',xaxis_title='% de respuestas',legend_title='Escala 1–5')
    graph(fig,'Escalas Likert: costos y eficiencia','perceptions_likert','Comparación de distribuciones, no de impactos objetivos.',335)
    sub=d[['Costo_1a5','Eficiencia_1a5']].dropna()
    cross=pd.crosstab(sub.Costo_1a5,sub.Eficiencia_1a5)
    fig=go.Figure(go.Heatmap(x=cross.columns.astype(str),y=cross.index.astype(str),z=cross.to_numpy(),text=cross.to_numpy(),texttemplate='%{text}',colorscale=[[0,'#EEF4F6'],[1,BLUE]],colorbar=dict(title='Empresas')))
    fig.update_xaxes(title='Eficiencia percibida (1–5)');fig.update_yaxes(title='Costos percibidos (1–5)')
    graph(fig,'Cruce: costos y eficiencia percibida','perceptions_cross','Frecuencias absolutas por combinación de respuestas.',340)
    sub=d[['Numero_tecnologias_8','Eficiencia_1a5']].dropna()
    if not sub.empty:
        bubble=sub.groupby(['Numero_tecnologias_8','Eficiencia_1a5']).size().reset_index(name='Empresas')
        fig=px.scatter(bubble,x='Numero_tecnologias_8',y='Eficiencia_1a5',
                       size='Empresas',size_max=36,color='Empresas',
                       color_continuous_scale=['#DDECEB','#72B0AC','#217C83'],
                       labels={'Numero_tecnologias_8':'Número de tecnologías (0–8)',
                               'Eficiencia_1a5':'Eficiencia percibida (1–5)'})
        fig.update_layout(coloraxis_showscale=False)
        fig.update_xaxes(dtick=1,range=[-.5,8.5])
        fig.update_yaxes(dtick=1,range=[.5,5.5])
        rho=spearman(sub.Numero_tecnologias_8,sub.Eficiencia_1a5)
        note=f'rho de Spearman = {rho:.3f}' if np.isfinite(rho) else 'rho no calculable'
        graph(fig,'Intensidad tecnológica y eficiencia percibida','perceptions_adoption',
              f'El tamaño de cada burbuja representa empresas; {note}. Asociación exploratoria, no causal.',355)
    z=counts(d.P10 if d.P10.notna().any() else d.Incentivos_01.map({0:'No',1:'Sí'}))
    st.markdown('**Acceso a incentivos o apoyos**')
    st.dataframe(pd.DataFrame({'Respuesta':z.index,'Empresas':z.values}),hide_index=True)
with tabs[5]:
    st.subheader('Regresión binomial (GLM): intensidad de adopción tecnológica')
    st.caption('Modelo exploratorio sobre la intensidad de adopción (0 a 8 tecnologías).')
    st.latex(r'Y_i\sim\operatorname{Binomial}(8,p_i),\quad\operatorname{logit}(p_i)=\beta_0+\beta_1\,\mathrm{Flota}_i')
    st.caption('Variable dependiente: número de tecnologías adoptadas (0–8). Flota: categoría ordinal de 1 a 4. Modelo reducido predefinido.')
    if len(d)<22:
        st.warning('Modelo calculado sobre la selección filtrada. Para reproducir los resultados del artículo, seleccione todas las empresas.')
    result=glm_binomial(d.Numero_tecnologias_8,d.Flota_ord)
    if result is None:st.warning('Los filtros dejan datos insuficientes o un modelo no identificable. Amplíe la selección.');
    else:
        b=result['beta']; ci=result['ci']; c1,c2,c3,c4=st.columns(4)
        with c1:kpi('Razón de momios',f"{result['odds']:.3f}",'Por nivel de flota')
        with c2:kpi('IC 95 % OR',f'{ci[0]:.2f}–{ci[1]:.2f}','Aproximación Wald')
        with c3:kpi('Valor p',f"{result['pvalue']:.4f}",'Prueba Wald exploratoria')
        with c4:kpi('AIC',f"{result['aic']:.2f}",'Modelo binomial')
        order=[1,2,3,4]
        eta=b[0]+b[1]*np.array(order);probs=1/(1+np.exp(-eta))
        observed=result['frame'].groupby('x').y.agg(['mean','size']).reindex(order)
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=order,y=8*probs,mode='lines+markers',name='Predicción binomial',line=dict(color=TEAL,width=3)))
        fig.add_trace(go.Scatter(x=order,y=observed['mean'],mode='markers',name='Promedio observado',marker=dict(size=13,color=GOLD,symbol='diamond'),customdata=observed['size'],hovertemplate='Flota %{x}<br>Media %{y:.2f}<br>n=%{customdata}<extra></extra>'))
        fig.update_xaxes(dtick=1,title='Categoría ordinal de flota (1–4)');fig.update_yaxes(range=[0,8.5],title='Tecnologías adoptadas (de 8)')
        graph(fig,'Adopción observada y predicción del modelo','binomial_prediction','Las predicciones son valores esperados del conteo de tecnologías, no probabilidades de adoptar alguna tecnología.',380)
        fig=go.Figure(go.Scatter(x=[result['odds']],y=['Flota ordinal'],mode='markers',marker=dict(size=13,color=TEAL),error_x=dict(type='data',symmetric=False,array=[ci[1]-result['odds']],arrayminus=[result['odds']-ci[0]])))
        fig.add_vline(x=1,line_dash='dash',line_color=SLATE);fig.update_xaxes(title='Razón de momios (OR) e IC 95 %')
        graph(fig,'Efecto estimado del tamaño de flota','binomial_or','OR mayor que 1 indica asociación positiva con la propensión modelada a adoptar cada tecnología.',255)
        st.markdown(f"**Ecuación estimada:** logit(p) = {b[0]:.4f} + {b[1]:.4f} × Flota")
        st.caption(f"n={result['n']}; dispersión de Pearson/gl={result['disp']:.3f}; razón de verosimilitudes LR={result['lr']:.3f}. Estimación de máxima verosimilitud con algoritmo IRLS, sin SciPy.")
        if result['disp']>1.5:
            st.warning('La dispersión de Pearson supera 1,5: los errores estándar y valores p binomiales pueden ser demasiado optimistas. Considere un modelo cuasibinomial o análisis de sensibilidad.')
        st.warning('Interpretación exploratoria: n pequeño y muestra por conveniencia. El modelo binomial presupone ocho oportunidades de adopción con probabilidad común condicional y dependencia limitada; tecnologías heterogéneas y correlacionadas pueden incumplir ese supuesto. No afirmar causalidad ni representatividad poblacional.')
with tabs[6]:
    st.subheader('Datos filtrados y trazabilidad')
    st.dataframe(d,use_container_width=True,hide_index=True)
    st.download_button('Exportar CSV filtrado',d.to_csv(index=False).encode('utf-8-sig'),file_name='transporte_carga_filtrado.csv',mime='text/csv')
    st.caption('No publique respuestas identificables en repositorios públicos. Los gráficos pueden exportarse a PNG desde el icono de cámara.')
st.divider();st.caption('Resultados descriptivos de empresas encuestadas. No permiten atribuir efectos causales ni extrapolar a todas las empresas de transporte de carga.')
